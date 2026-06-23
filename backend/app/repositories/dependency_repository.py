from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dependency_edge import DependencyEdge, DependencyType
from app.schemas.analysis import DependencyCreate


async def bulk_create(
    db: AsyncSession,
    *,
    repository_id: UUID,
    snapshot_id: UUID,
    edges: list[DependencyCreate],
) -> list[DependencyEdge]:
    records = [
        DependencyEdge(
            repository_id=repository_id,
            snapshot_id=snapshot_id,
            source_file_id=item.source_file_id,
            target_file_id=item.target_file_id,
            dependency_type=DependencyType(item.dependency_type),
        )
        for item in edges
    ]
    db.add_all(records)
    await db.flush()
    return records
