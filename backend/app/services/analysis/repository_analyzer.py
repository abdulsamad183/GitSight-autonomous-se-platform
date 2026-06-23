import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from git import Repo
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository, RepositoryStatus
from app.repositories import (
    dependency_repository,
    file_repository,
    job_repository,
    repository_repository,
    snapshot_repository,
    symbol_repository,
)
from app.schemas.analysis import SnapshotCreate, SymbolCreate
from app.services.analysis.dependency_extractor import DependencyExtractor
from app.services.analysis.file_scanner import FileScanner
from app.services.analysis.job_tracker import (
    STAGE_CLEANING,
    STAGE_CLONING,
    STAGE_DISCOVERING,
    JobTracker,
)
from app.services.analysis.repository_cloner import RepositoryCloner
from app.services.analysis.tree_sitter_parser import TreeSitterParser
from app.services.exceptions import AnalysisError

logger = logging.getLogger(__name__)

STAGE_NO_CHANGES = "No changes detected"


def _short_hash(commit_hash: str) -> str:
    return commit_hash[:7]


class RepositoryAnalyzer:
    async def _analyze_branch(
        self,
        db: AsyncSession,
        *,
        settings: Settings,
        repository: Repository,
        clone_path: Path,
        git_repo: Repo,
        branch: str,
        branch_index: int,
        total_branches: int,
        tracker: JobTracker,
        analyzed_at: datetime,
        skip_unchanged: bool,
    ) -> tuple[bool, bool]:
        """Returns (success, updated) where updated is True if DB was written."""
        cloner = RepositoryCloner(settings)
        try:
            commit_hash = cloner.checkout_branch(git_repo, branch)
        except Exception as exc:
            logger.warning("Failed to checkout branch %s: %s", branch, exc)
            await tracker.set_message(f"Skipped branch {branch}: checkout failed")
            return False, False

        existing = await snapshot_repository.get_for_branch(db, repository.id, branch)
        if skip_unchanged and existing and existing.commit_hash == commit_hash:
            await tracker.set_message(
                f"{branch} unchanged at {_short_hash(commit_hash)}",
            )
            return True, False

        if existing:
            await tracker.set_message(
                f"{branch} updated {_short_hash(existing.commit_hash)} → {_short_hash(commit_hash)}",
            )
        else:
            await tracker.set_message(f"{branch} analyzed at {_short_hash(commit_hash)}")

        await tracker.set_branch_stage(
            branch=branch,
            branch_index=branch_index,
            total_branches=total_branches,
            sub_stage="Scanning files",
            sub_progress=10,
        )

        await snapshot_repository.delete_for_branch(db, repository.id, branch)
        snapshot = await snapshot_repository.create(
            db,
            repository_id=repository.id,
            data=SnapshotCreate(
                commit_hash=commit_hash,
                branch=branch,
                analyzed_at=analyzed_at,
            ),
        )

        scanner = FileScanner(settings)
        scanned_files = scanner.scan(clone_path)

        await tracker.set_branch_stage(
            branch=branch,
            branch_index=branch_index,
            total_branches=total_branches,
            sub_stage="Storing metadata",
            sub_progress=35,
        )

        file_records = await file_repository.bulk_create(
            db,
            repository_id=repository.id,
            snapshot_id=snapshot.id,
            files=[item.draft for item in scanned_files],
        )

        path_to_file_id = {record.relative_path: record.id for record in file_records}
        path_to_scanned = {
            item.draft.relative_path: item for item in scanned_files if item.parseable
        }

        await tracker.set_branch_stage(
            branch=branch,
            branch_index=branch_index,
            total_branches=total_branches,
            sub_stage="Parsing source files",
            sub_progress=60,
        )

        parser = TreeSitterParser()
        symbol_creates: list[SymbolCreate] = []
        dependency_creates = []
        extractor = DependencyExtractor(path_to_file_id)

        for record in file_records:
            scanned = path_to_scanned.get(record.relative_path)
            if scanned is None:
                continue

            try:
                source = scanned.absolute_path.read_bytes()
            except OSError:
                logger.warning("Failed to read %s", record.relative_path)
                continue

            parse_result = parser.parse_file(language=record.language or "", source=source)
            for symbol in parse_result.symbols:
                symbol_creates.append(
                    SymbolCreate(
                        file_id=record.id,
                        symbol_name=symbol.symbol_name,
                        symbol_type=symbol.symbol_type,
                        start_line=symbol.start_line,
                        end_line=symbol.end_line,
                        signature=symbol.signature,
                    )
                )

            dependency_creates.extend(
                extractor.resolve_edges(
                    source_file_id=record.id,
                    source_relative_path=record.relative_path,
                    language=record.language,
                    imports=parse_result.imports,
                )
            )

        await tracker.set_branch_stage(
            branch=branch,
            branch_index=branch_index,
            total_branches=total_branches,
            sub_stage="Extracting dependencies",
            sub_progress=85,
        )

        if symbol_creates:
            await symbol_repository.bulk_create(
                db,
                repository_id=repository.id,
                snapshot_id=snapshot.id,
                symbols=symbol_creates,
            )
        if dependency_creates:
            await dependency_repository.bulk_create(
                db,
                repository_id=repository.id,
                snapshot_id=snapshot.id,
                edges=dependency_creates,
            )

        await db.commit()
        return True, True

    async def run(self, job_id: UUID, *, skip_unchanged: bool = False) -> None:
        settings = get_settings()
        clone_path = Path(settings.clone_base_dir) / str(job_id)
        git_repo: Repo | None = None

        async with AsyncSessionLocal() as db:
            job = await job_repository.get_by_id(db, job_id)
            if job is None:
                logger.error("Job %s not found", job_id)
                return

            repository = job.repository
            tracker = JobTracker(db, job)

            try:
                await tracker.mark_running()
                await tracker.set_stage(STAGE_CLONING)

                cloner = RepositoryCloner(settings)
                clone_result = cloner.clone(job_id=job_id, repo_url=repository.repo_url)
                git_repo = Repo(clone_result.clone_path)

                await tracker.set_stage(STAGE_DISCOVERING)
                discover_msg = (
                    f"Discovered {clone_result.total_branches_found} branches "
                    f"(analyzing {len(clone_result.branches)})"
                )
                await tracker.set_message(discover_msg, progress=STAGE_DISCOVERING[1])

                await repository_repository.update_after_clone(
                    db,
                    repository,
                    default_branch=clone_result.default_branch,
                    latest_commit_hash=clone_result.default_commit_hash,
                )
                await db.commit()

                branches = clone_result.branches
                if not branches:
                    raise AnalysisError("No branches found in repository")

                analyzed_count = 0
                updated_count = 0
                for index, branch in enumerate(branches):
                    success, updated = await self._analyze_branch(
                        db,
                        settings=settings,
                        repository=repository,
                        clone_path=clone_result.clone_path,
                        git_repo=git_repo,
                        branch=branch,
                        branch_index=index,
                        total_branches=len(branches),
                        tracker=tracker,
                        analyzed_at=clone_result.analyzed_at,
                        skip_unchanged=skip_unchanged,
                    )
                    if success:
                        analyzed_count += 1
                    if updated:
                        updated_count += 1

                if analyzed_count == 0:
                    raise AnalysisError("Failed to analyze any branches")

                await repository_repository.update_branch_metadata(
                    db,
                    repository,
                    branches_analyzed_count=analyzed_count,
                    branches_truncated=clone_result.branches_truncated,
                )
                await repository_repository.update_status(db, repository, RepositoryStatus.ACTIVE)
                await db.commit()

                await tracker.set_stage(STAGE_CLEANING)
                if skip_unchanged and updated_count == 0:
                    await tracker.mark_completed_with_stage(STAGE_NO_CHANGES)
                else:
                    await tracker.mark_completed()
            except AnalysisError as exc:
                await tracker.mark_failed(str(exc))
                await repository_repository.update_status(db, repository, RepositoryStatus.FAILED)
                await db.commit()
            except Exception as exc:
                logger.exception("Unexpected analysis failure for job %s", job_id)
                await tracker.mark_failed(str(exc))
                await repository_repository.update_status(db, repository, RepositoryStatus.FAILED)
                await db.commit()
            finally:
                if git_repo is not None:
                    git_repo.close()
                shutil.rmtree(clone_path, ignore_errors=True)


async def run_analysis_job(job_id: UUID, skip_unchanged: bool = False) -> None:
    analyzer = RepositoryAnalyzer()
    await analyzer.run(job_id, skip_unchanged=skip_unchanged)
