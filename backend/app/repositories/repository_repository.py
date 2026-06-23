from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository import Repository


async def get_by_user_id(db: AsyncSession, user_id: UUID) -> list[Repository]:
    result = await db.execute(
        select(Repository)
        .where(Repository.user_id == user_id)
        .order_by(Repository.created_at.desc())
    )
    return list(result.scalars().all())


async def get_by_id_for_user(
    db: AsyncSession,
    repo_id: UUID,
    user_id: UUID,
) -> Repository | None:
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.user_id == user_id)
    )
    return result.scalar_one_or_none()
