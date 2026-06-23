from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.job import JobStatus, JobType
from app.models.repository import RepositoryStatus
from app.repositories import job_repository, repository_repository
from app.schemas.repository import AnalyzeResponse
from app.services.analysis.repository_analyzer import run_analysis_job
from app.services.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.utils.github import parse_github_url, validate_public_repo


async def start_analysis(
    db: AsyncSession,
    *,
    user_id: UUID,
    github_url: str,
    settings: Settings,
    background_tasks: BackgroundTasks,
) -> AnalyzeResponse:
    try:
        parsed = parse_github_url(github_url)
    except ValidationError:
        raise

    existing = await repository_repository.get_by_url_for_user(db, user_id, parsed.normalized_url)

    if existing and existing.status == RepositoryStatus.ACTIVE:
        latest_job = await job_repository.get_latest_for_repository(db, existing.id)
        return AnalyzeResponse(
            repository_id=existing.id,
            job_id=latest_job.id if latest_job else None,
            status="CACHED",
            cached=True,
        )

    if existing:
        active_job = await job_repository.get_active_for_repository(db, existing.id)
        if active_job:
            return AnalyzeResponse(
                repository_id=existing.id,
                job_id=active_job.id,
                status="PENDING",
                cached=False,
            )

    await validate_public_repo(parsed.owner, parsed.repository_name, settings)

    if existing and existing.status in {RepositoryStatus.FAILED, RepositoryStatus.PENDING}:
        repository = existing
        await repository_repository.update_status(db, repository, RepositoryStatus.PENDING)
    else:
        repository = await repository_repository.create(
            db,
            user_id=user_id,
            name=f"{parsed.owner}/{parsed.repository_name}",
            repo_url=parsed.normalized_url,
            owner=parsed.owner,
            repository_name=parsed.repository_name,
            status=RepositoryStatus.PENDING,
        )

    job = await job_repository.create(db, repository_id=repository.id, job_type=JobType.INGEST)
    await db.commit()

    background_tasks.add_task(run_analysis_job, job.id)

    return AnalyzeResponse(
        repository_id=repository.id,
        job_id=job.id,
        status="PENDING",
        cached=False,
    )


async def start_refresh(
    db: AsyncSession,
    *,
    user_id: UUID,
    repository_id: UUID,
    background_tasks: BackgroundTasks,
) -> AnalyzeResponse:
    repository = await repository_repository.get_by_id_for_user(db, repository_id, user_id)
    if repository is None:
        raise NotFoundError("Repository not found")

    if repository.status != RepositoryStatus.ACTIVE:
        raise ValidationError("Only active repositories can be refreshed")

    active_job = await job_repository.get_active_for_repository(db, repository.id)
    if active_job:
        raise ConflictError("An analysis job is already running for this repository")

    job = await job_repository.create(db, repository_id=repository.id, job_type=JobType.INGEST)
    await db.commit()

    background_tasks.add_task(run_analysis_job, job.id, True)

    return AnalyzeResponse(
        repository_id=repository.id,
        job_id=job.id,
        status="PENDING",
        cached=False,
    )
