from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import admin_repository
from app.schemas.admin import (
    AdminRepositoryItem,
    AdminStatsResponse,
    AdminUserDetailResponse,
    AdminUserListItem,
    AdminUserListResponse,
)
from app.services.exceptions import NotFoundError


async def get_stats(db: AsyncSession) -> AdminStatsResponse:
    data = await admin_repository.get_stats(db)
    return AdminStatsResponse(**data)


async def list_users(db: AsyncSession, *, page: int, limit: int) -> AdminUserListResponse:
    rows, total = await admin_repository.list_users_with_repo_counts(db, page=page, limit=limit)
    items = [
        AdminUserListItem(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            repository_count=repo_count,
        )
        for user, repo_count in rows
    ]
    return AdminUserListResponse(items=items, total=total, page=page, limit=limit)


async def get_user_detail(db: AsyncSession, user_id: UUID) -> AdminUserDetailResponse:
    result = await admin_repository.get_user_with_repositories(db, user_id)
    if result is None:
        raise NotFoundError("User not found")
    user, repositories = result
    return AdminUserDetailResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
        repositories=[
            AdminRepositoryItem(
                id=repo.id,
                name=repo.name,
                repo_url=repo.repo_url,
                status=repo.status.value,
                indexing_status=repo.indexing_status.value,
                created_at=repo.created_at,
                updated_at=repo.updated_at,
            )
            for repo in repositories
        ],
    )
