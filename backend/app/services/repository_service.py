from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository import Repository
from app.repositories import repository_repository


async def get_user_repositories(db: AsyncSession, user_id: UUID) -> list[Repository]:
    return await repository_repository.get_by_user_id(db, user_id)
