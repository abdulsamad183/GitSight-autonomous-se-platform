from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import File
from app.schemas.analysis import FileCreate


async def bulk_create(
    db: AsyncSession,
    *,
    repository_id: UUID,
    snapshot_id: UUID,
    files: list[FileCreate],
) -> list[File]:
    records = [
        File(
            repository_id=repository_id,
            snapshot_id=snapshot_id,
            relative_path=item.relative_path,
            file_name=item.file_name,
            extension=item.extension,
            language=item.language,
            size_bytes=item.size_bytes,
            is_binary=item.is_binary,
        )
        for item in files
    ]
    db.add_all(records)
    await db.flush()
    return records


async def list_for_snapshot(db: AsyncSession, *, snapshot_id: UUID) -> list[File]:
    result = await db.execute(
        select(File)
        .where(File.snapshot_id == snapshot_id)
        .order_by(File.relative_path)
    )
    return list(result.scalars().all())
