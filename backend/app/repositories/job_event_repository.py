from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_event import JobEvent


async def append(db: AsyncSession, *, job_id: UUID, message: str) -> JobEvent:
    event = JobEvent(job_id=job_id, message=message)
    db.add(event)
    await db.flush()
    return event


async def list_for_job(db: AsyncSession, job_id: UUID) -> list[JobEvent]:
    result = await db.execute(
        select(JobEvent).where(JobEvent.job_id == job_id).order_by(JobEvent.created_at.asc())
    )
    return list(result.scalars().all())
