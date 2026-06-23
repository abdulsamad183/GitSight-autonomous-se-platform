from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository_snapshot import RepositorySnapshot
from app.schemas.analysis import SnapshotCreate


async def create(
    db: AsyncSession,
    *,
    repository_id: UUID,
    data: SnapshotCreate,
) -> RepositorySnapshot:
    snapshot = RepositorySnapshot(
        repository_id=repository_id,
        commit_hash=data.commit_hash,
        branch=data.branch,
        analyzed_at=data.analyzed_at,
    )
    db.add(snapshot)
    await db.flush()
    return snapshot


async def list_for_repository(
    db: AsyncSession,
    repository_id: UUID,
) -> list[RepositorySnapshot]:
    result = await db.execute(
        select(RepositorySnapshot)
        .where(RepositorySnapshot.repository_id == repository_id)
        .order_by(RepositorySnapshot.branch)
    )
    return list(result.scalars().all())


async def get_for_branch(
    db: AsyncSession,
    repository_id: UUID,
    branch: str,
) -> RepositorySnapshot | None:
    result = await db.execute(
        select(RepositorySnapshot).where(
            RepositorySnapshot.repository_id == repository_id,
            RepositorySnapshot.branch == branch,
        )
    )
    return result.scalar_one_or_none()


async def get_latest_for_repository(
    db: AsyncSession,
    repository_id: UUID,
) -> RepositorySnapshot | None:
    result = await db.execute(
        select(RepositorySnapshot)
        .where(RepositorySnapshot.repository_id == repository_id)
        .order_by(RepositorySnapshot.analyzed_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def delete_for_branch(
    db: AsyncSession,
    repository_id: UUID,
    branch: str,
) -> None:
    await db.execute(
        delete(RepositorySnapshot).where(
            RepositorySnapshot.repository_id == repository_id,
            RepositorySnapshot.branch == branch,
        )
    )
    await db.flush()
