from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.job import Job, JobStatus, JobType
from app.models.repository import Repository


async def create(
    db: AsyncSession,
    *,
    repository_id: UUID,
    job_type: JobType = JobType.INGEST,
) -> Job:
    job = Job(
        repository_id=repository_id,
        job_type=job_type,
        status=JobStatus.QUEUED,
        progress=0.0,
    )
    db.add(job)
    await db.flush()
    return job


async def get_by_id(db: AsyncSession, job_id: UUID) -> Job | None:
    result = await db.execute(
        select(Job).where(Job.id == job_id).options(joinedload(Job.repository))
    )
    return result.scalar_one_or_none()


async def get_by_id_for_user(db: AsyncSession, job_id: UUID, user_id: UUID) -> Job | None:
    result = await db.execute(
        select(Job)
        .join(Repository, Job.repository_id == Repository.id)
        .where(Job.id == job_id, Repository.user_id == user_id)
        .options(joinedload(Job.repository))
    )
    return result.scalar_one_or_none()


async def get_latest_for_repository(db: AsyncSession, repository_id: UUID) -> Job | None:
    result = await db.execute(
        select(Job)
        .where(Job.repository_id == repository_id)
        .order_by(Job.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_active_for_repository(db: AsyncSession, repository_id: UUID) -> Job | None:
    result = await db.execute(
        select(Job)
        .where(
            Job.repository_id == repository_id,
            Job.status.in_([JobStatus.QUEUED, JobStatus.RUNNING]),
        )
        .order_by(Job.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def update_progress(
    db: AsyncSession,
    job: Job,
    *,
    status: JobStatus | None = None,
    progress: float | None = None,
    current_stage: str | None = None,
    error_message: str | None = None,
) -> Job:
    if status is not None:
        job.status = status
    if progress is not None:
        job.progress = progress
    if current_stage is not None:
        job.current_stage = current_stage
    if error_message is not None:
        job.error_message = error_message
    await db.flush()
    return job
