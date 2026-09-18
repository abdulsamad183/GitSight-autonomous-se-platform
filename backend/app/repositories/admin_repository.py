from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository import IndexingStatus, Repository, RepositoryStatus
from app.models.user import User


async def get_stats(db: AsyncSession) -> dict:
    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)

    total_users = await db.scalar(select(func.count()).select_from(User)) or 0
    total_repositories = await db.scalar(select(func.count()).select_from(Repository)) or 0

    status_rows = await db.execute(
        select(Repository.status, func.count()).group_by(Repository.status)
    )
    repos_by_status = {status.value: count for status, count in status_rows.all()}
    for status in RepositoryStatus:
        repos_by_status.setdefault(status.value, 0)

    indexing_rows = await db.execute(
        select(Repository.indexing_status, func.count()).group_by(Repository.indexing_status)
    )
    repos_by_indexing_status = {status.value: count for status, count in indexing_rows.all()}
    for status in IndexingStatus:
        repos_by_indexing_status.setdefault(status.value, 0)

    signups_last_7_days = (
        await db.scalar(select(func.count()).select_from(User).where(User.created_at >= week_ago))
        or 0
    )
    repos_added_last_7_days = (
        await db.scalar(
            select(func.count()).select_from(Repository).where(Repository.created_at >= week_ago)
        )
        or 0
    )

    return {
        "total_users": total_users,
        "total_repositories": total_repositories,
        "repos_by_status": repos_by_status,
        "repos_by_indexing_status": repos_by_indexing_status,
        "signups_last_7_days": signups_last_7_days,
        "repos_added_last_7_days": repos_added_last_7_days,
    }


async def list_users_with_repo_counts(
    db: AsyncSession,
    *,
    page: int,
    limit: int,
) -> tuple[list[tuple[User, int]], int]:
    total = await db.scalar(select(func.count()).select_from(User)) or 0
    repo_count = func.count(Repository.id).label("repository_count")
    offset = (page - 1) * limit
    result = await db.execute(
        select(User, repo_count)
        .outerjoin(Repository, Repository.user_id == User.id)
        .group_by(User.id)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = [(user, count) for user, count in result.all()]
    return rows, total


async def get_user_with_repositories(
    db: AsyncSession,
    user_id: UUID,
) -> tuple[User, list[Repository]] | None:
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        return None
    result = await db.execute(
        select(Repository)
        .where(Repository.user_id == user_id)
        .order_by(Repository.updated_at.desc())
    )
    repositories = list(result.scalars().all())
    return user, repositories
