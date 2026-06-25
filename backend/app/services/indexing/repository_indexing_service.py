import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from git import Repo
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.repository import IndexingStatus
from app.repositories import (
    chunk_embedding_repository,
    code_chunk_repository,
    repository_repository,
    snapshot_repository,
)
from app.services.analysis.job_tracker import STAGE_INDEXING_CHUNKS, STAGE_INDEXING_EMBEDDINGS
from app.services.analysis.repository_cloner import RepositoryCloner
from app.services.indexing.chunk_service import ChunkService
from app.services.indexing.diff_chunk_service import build_diff_chunks
from app.services.indexing.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


def resolve_indexing_plan(
    *,
    branches: list[str],
    default_branch: str,
    updated_branches: list[str] | None,
) -> tuple[list[str], list[str]]:
    """Return (branches_for_full_index, branches_for_diff_index)."""
    if updated_branches is None:
        full = [default_branch] if default_branch in branches else []
        if not full and branches:
            full = [branches[0]]
        diff = [branch for branch in branches if branch not in full]
        return full, diff

    if default_branch in updated_branches:
        full = [default_branch]
        diff = [branch for branch in branches if branch != default_branch]
        return full, diff

    full: list[str] = []
    diff = [branch for branch in updated_branches if branch != default_branch]
    return full, diff


class RepositoryIndexingService:
    def __init__(self, db: AsyncSession, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.chunk_service = ChunkService(db, self.settings)
        self.embedding_service = EmbeddingService(db)
        self.cloner = RepositoryCloner(self.settings)

    async def index_repository(
        self,
        *,
        repository_id: UUID,
        clone_path: Path,
        git_repo: Repo,
        default_branch: str,
        branches: list[str],
        updated_branches: list[str] | None = None,
        tracker=None,
    ) -> None:
        repository = await repository_repository.get_by_id(self.db, repository_id)
        if repository is None:
            logger.error("Repository %s not found for indexing", repository_id)
            return

        if default_branch not in branches and branches:
            default_branch = branches[0]

        started_at = datetime.now(timezone.utc)
        start_perf = time.perf_counter()

        await repository_repository.update_indexing_status(
            self.db,
            repository,
            indexing_status=IndexingStatus.PROCESSING,
            indexing_started_at=started_at,
            indexing_completed_at=None,
            indexing_duration_seconds=None,
        )
        await self.db.commit()

        try:
            all_needing_embedding = []
            full_branches, diff_branches = resolve_indexing_plan(
                branches=branches,
                default_branch=default_branch,
                updated_branches=updated_branches,
            )

            default_snapshot = await snapshot_repository.get_for_branch(
                self.db, repository_id, default_branch
            )
            default_commit = default_snapshot.commit_hash if default_snapshot else None

            incremental = updated_branches is not None

            for branch in full_branches:
                if tracker is not None:
                    await tracker.set_stage(STAGE_INDEXING_CHUNKS)

                snapshot = await snapshot_repository.get_for_branch(self.db, repository_id, branch)
                if snapshot is None:
                    logger.warning("No snapshot for branch %s; skipping full index", branch)
                    continue

                self.cloner.checkout_branch(git_repo, branch)
                if not incremental:
                    await code_chunk_repository.delete_for_branch(
                        self.db,
                        repository_id=repository_id,
                        branch_name=branch,
                    )

                _, needing_embedding = await self.chunk_service.create_chunks(
                    repository_id=repository_id,
                    branch_name=branch,
                    clone_path=clone_path,
                    head_commit_hash=snapshot.commit_hash,
                    only_new_files=incremental,
                )
                all_needing_embedding.extend(needing_embedding)
                await self.db.commit()

            if default_commit is None and default_snapshot is None:
                default_snapshot = await snapshot_repository.get_for_branch(
                    self.db, repository_id, default_branch
                )
                default_commit = default_snapshot.commit_hash if default_snapshot else None

            for branch in diff_branches:
                if tracker is not None:
                    await tracker.set_stage(STAGE_INDEXING_CHUNKS)

                branch_snapshot = await snapshot_repository.get_for_branch(
                    self.db, repository_id, branch
                )
                if branch_snapshot is None or default_commit is None:
                    logger.warning("Missing snapshot for diff indexing on branch %s", branch)
                    continue

                self.cloner.checkout_branch(git_repo, branch)

                if not incremental:
                    await code_chunk_repository.delete_for_branch(
                        self.db,
                        repository_id=repository_id,
                        branch_name=branch,
                    )

                diff_chunks = build_diff_chunks(
                    git_repo,
                    repository_id=repository_id,
                    branch_name=branch,
                    default_commit=default_commit,
                    branch_commit=branch_snapshot.commit_hash,
                    max_diff_bytes=self.settings.max_diff_bytes,
                )
                if diff_chunks:
                    _, needing_embedding = await code_chunk_repository.bulk_upsert(
                        self.db, chunks=diff_chunks
                    )
                    all_needing_embedding.extend(needing_embedding)

                if incremental:
                    _, new_file_embeddings = await self.chunk_service.create_chunks(
                        repository_id=repository_id,
                        branch_name=branch,
                        clone_path=clone_path,
                        head_commit_hash=branch_snapshot.commit_hash,
                        only_new_files=True,
                    )
                    all_needing_embedding.extend(new_file_embeddings)

                await self.db.commit()

            if tracker is not None:
                await tracker.set_stage(STAGE_INDEXING_EMBEDDINGS)

            if all_needing_embedding:
                await self.embedding_service.embed_chunks(all_needing_embedding)
            else:
                missing = await code_chunk_repository.list_chunks_needing_embedding(
                    self.db, repository_id=repository_id
                )
                if missing:
                    await self.embedding_service.embed_chunks(missing)

            await self.db.commit()

            total_chunks = await code_chunk_repository.count_by_repository(self.db, repository_id)
            embedded_chunks = await chunk_embedding_repository.count_for_repository(
                self.db, repository_id
            )
            duration = time.perf_counter() - start_perf
            completed_at = datetime.now(timezone.utc)

            await repository_repository.update_indexing_status(
                self.db,
                repository,
                indexing_status=IndexingStatus.COMPLETED,
                total_chunks=total_chunks,
                embedded_chunks=embedded_chunks,
                indexing_completed_at=completed_at,
                indexing_duration_seconds=duration,
            )
            await self.db.commit()

            logger.info(
                "Indexing completed for repository %s: %d chunks, %d embedded in %.1fs",
                repository_id,
                total_chunks,
                embedded_chunks,
                duration,
            )
        except Exception as exc:
            logger.exception("Indexing failed for repository %s: %s", repository_id, exc)
            await self.db.rollback()
            repository = await repository_repository.get_by_id(self.db, repository_id)
            if repository is not None:
                await repository_repository.update_indexing_status(
                    self.db,
                    repository,
                    indexing_status=IndexingStatus.FAILED,
                    indexing_duration_seconds=time.perf_counter() - start_perf,
                )
                await self.db.commit()
            raise
