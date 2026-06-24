from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dependency_edge import DependencyEdge
from app.models.file import File
from app.models.symbol import Symbol


async def list_by_snapshot(db: AsyncSession, snapshot_id: UUID) -> list[File]:
    result = await db.execute(
        select(File).where(File.snapshot_id == snapshot_id).order_by(File.relative_path)
    )
    return list(result.scalars().all())


async def get_path_map(db: AsyncSession, snapshot_id: UUID) -> dict[UUID, str]:
    files = await list_by_snapshot(db, snapshot_id)
    return {file.id: file.relative_path for file in files}


async def list_symbols_by_snapshot(db: AsyncSession, snapshot_id: UUID) -> list[tuple[Symbol, str]]:
    result = await db.execute(
        select(Symbol, File.relative_path)
        .join(File, Symbol.file_id == File.id)
        .where(Symbol.snapshot_id == snapshot_id)
        .order_by(File.relative_path, Symbol.start_line)
    )
    return list(result.all())


async def list_dependencies_by_snapshot(
    db: AsyncSession,
    snapshot_id: UUID,
) -> list[tuple[DependencyEdge, str, str]]:
    source = File.__table__.alias("source_file")
    target = File.__table__.alias("target_file")
    result = await db.execute(
        select(DependencyEdge, source.c.relative_path, target.c.relative_path)
        .join(source, DependencyEdge.source_file_id == source.c.id)
        .join(target, DependencyEdge.target_file_id == target.c.id)
        .where(DependencyEdge.snapshot_id == snapshot_id)
        .order_by(source.c.relative_path, target.c.relative_path)
    )
    return list(result.all())


async def list_files_for_graph(db: AsyncSession, snapshot_id: UUID) -> list[File]:
    result = await db.execute(
        select(File)
        .where(File.snapshot_id == snapshot_id, File.is_binary.is_(False))
        .order_by(File.relative_path)
    )
    return list(result.scalars().all())


async def list_symbols_for_graph(db: AsyncSession, snapshot_id: UUID) -> list[tuple[Symbol, str]]:
    result = await db.execute(
        select(Symbol, File.relative_path)
        .join(File, Symbol.file_id == File.id)
        .where(Symbol.snapshot_id == snapshot_id)
        .order_by(File.relative_path, Symbol.start_line)
    )
    return list(result.all())
