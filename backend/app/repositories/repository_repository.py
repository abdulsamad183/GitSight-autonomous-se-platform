from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository import Repository, RepositoryStatus


async def get_by_user_id(db: AsyncSession, user_id: UUID) -> list[Repository]:
    result = await db.execute(
        select(Repository)
        .where(Repository.user_id == user_id)
        .order_by(Repository.updated_at.desc())
    )
    return list(result.scalars().all())


async def get_by_url_for_user(
    db: AsyncSession,
    user_id: UUID,
    repo_url: str,
) -> Repository | None:
    result = await db.execute(
        select(Repository)
        .where(Repository.user_id == user_id, Repository.repo_url == repo_url)
        .order_by(Repository.updated_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_by_id_for_user(
    db: AsyncSession,
    repo_id: UUID,
    user_id: UUID,
) -> Repository | None:
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    *,
    user_id: UUID,
    name: str,
    repo_url: str,
    owner: str,
    repository_name: str,
    status: RepositoryStatus = RepositoryStatus.PENDING,
) -> Repository:
    repository = Repository(
        user_id=user_id,
        name=name,
        repo_url=repo_url,
        owner=owner,
        repository_name=repository_name,
        status=status,
    )
    db.add(repository)
    await db.flush()
    return repository


async def update_after_clone(
    db: AsyncSession,
    repository: Repository,
    *,
    default_branch: str,
    latest_commit_hash: str,
) -> Repository:
    repository.default_branch = default_branch
    repository.latest_commit_hash = latest_commit_hash
    await db.flush()
    return repository


async def update_branch_metadata(
    db: AsyncSession,
    repository: Repository,
    *,
    branches_analyzed_count: int,
    branches_truncated: bool,
) -> Repository:
    repository.branches_analyzed_count = branches_analyzed_count
    repository.branches_truncated = branches_truncated
    await db.flush()
    return repository


async def update_status(
    db: AsyncSession,
    repository: Repository,
    status: RepositoryStatus,
) -> Repository:
    repository.status = status
    await db.flush()
    return repository


async def delete_for_user(db: AsyncSession, repo_id: UUID, user_id: UUID) -> bool:
    repository = await get_by_id_for_user(db, repo_id, user_id)
    if repository is None:
        return False
    await db.delete(repository)
    await db.flush()
    return True


async def delete_all_for_user(db: AsyncSession, user_id: UUID) -> int:
    repositories = await get_by_user_id(db, user_id)
    count = len(repositories)
    for repository in repositories:
        await db.delete(repository)
    if count:
        await db.flush()
    return count
