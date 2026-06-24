import logging
import shutil
from pathlib import Path
from uuid import UUID

from git import Repo
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.job import JobType
from app.models.repository import IndexingStatus, RepositoryStatus
from app.repositories import job_repository, repository_repository
from app.services.analysis.job_tracker import JobTracker
from app.services.analysis.repository_cloner import RepositoryCloner
from app.services.exceptions import IndexingError, NotFoundError
from app.services.indexing.repository_indexing_service import RepositoryIndexingService

logger = logging.getLogger(__name__)


async def get_index_status(
    db: AsyncSession,
    *,
    repository_id: UUID,
    user_id: UUID,
) -> dict:
    repository = await repository_repository.get_by_id_for_user(db, repository_id, user_id)
    if repository is None:
        raise NotFoundError("Repository not found")

    from app.repositories import code_chunk_repository

    chunk_type_distribution = await code_chunk_repository.count_by_type(db, repository_id)

    return {
        "repository_id": repository.id,
        "indexing_status": repository.indexing_status.value,
        "total_chunks": repository.total_chunks,
        "embedded_chunks": repository.embedded_chunks,
        "indexing_started_at": repository.indexing_started_at,
        "indexing_completed_at": repository.indexing_completed_at,
        "indexing_duration_seconds": repository.indexing_duration_seconds,
        "chunk_type_distribution": chunk_type_distribution,
    }


async def start_reindex(
    db: AsyncSession,
    *,
    repository_id: UUID,
    user_id: UUID,
) -> tuple[UUID, UUID]:
    from app.services.exceptions import ConflictError, ValidationError

    repository = await repository_repository.get_by_id_for_user(db, repository_id, user_id)
    if repository is None:
        raise NotFoundError("Repository not found")

    if repository.status != RepositoryStatus.ACTIVE:
        raise ValidationError("Only active repositories can be reindexed")

    if repository.indexing_status == IndexingStatus.PROCESSING:
        raise ConflictError("Indexing is already in progress for this repository")

    active_job = await job_repository.get_active_for_repository(db, repository.id)
    if active_job:
        raise ConflictError("A job is already running for this repository")

    job = await job_repository.create(db, repository_id=repository.id, job_type=JobType.EMBED)
    await db.commit()
    return repository.id, job.id


async def run_indexing_job(job_id: UUID) -> None:
    settings = get_settings()
    clone_path = Path(settings.clone_base_dir) / str(job_id)
    git_repo: Repo | None = None

    async with AsyncSessionLocal() as db:
        job = await job_repository.get_by_id(db, job_id)
        if job is None:
            logger.error("Indexing job %s not found", job_id)
            return

        repository = job.repository
        tracker = JobTracker(db, job)

        try:
            await tracker.mark_running()
            await tracker.set_message("Cloning repository for reindexing")

            cloner = RepositoryCloner(settings)
            clone_result = cloner.clone(job_id=job_id, repo_url=repository.repo_url)
            git_repo = Repo(clone_result.clone_path)

            branches = clone_result.branches
            if not branches:
                raise IndexingError("No branches found in repository")

            indexing_service = RepositoryIndexingService(db, settings)
            await indexing_service.index_repository(
                repository_id=repository.id,
                clone_path=clone_result.clone_path,
                git_repo=git_repo,
                default_branch=clone_result.default_branch,
                branches=branches,
                updated_branches=None,
                tracker=tracker,
            )
            await tracker.mark_completed()
        except IndexingError as exc:
            await tracker.mark_failed(str(exc))
            await db.commit()
        except Exception as exc:
            logger.exception("Unexpected indexing failure for job %s", job_id)
            await tracker.mark_failed(str(exc))
            await db.commit()
        finally:
            if git_repo is not None:
                git_repo.close()
            shutil.rmtree(clone_path, ignore_errors=True)
