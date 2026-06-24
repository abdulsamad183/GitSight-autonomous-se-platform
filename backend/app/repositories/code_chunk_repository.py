import uuid
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_chunk import ChunkType, CodeChunk
from app.schemas.chunk import ChunkCreate


async def get_by_id(db: AsyncSession, chunk_id: UUID) -> CodeChunk | None:
    result = await db.execute(select(CodeChunk).where(CodeChunk.id == chunk_id))
    return result.scalar_one_or_none()


async def get_by_ids(db: AsyncSession, *, chunk_ids: list[UUID]) -> list[CodeChunk]:
    if not chunk_ids:
        return []
    result = await db.execute(select(CodeChunk).where(CodeChunk.id.in_(chunk_ids)))
    return list(result.scalars().all())


async def get_by_id_for_repository(
    db: AsyncSession,
    *,
    repository_id: UUID,
    chunk_id: UUID,
) -> CodeChunk | None:
    result = await db.execute(
        select(CodeChunk).where(
            CodeChunk.id == chunk_id,
            CodeChunk.repository_id == repository_id,
        )
    )
    return result.scalar_one_or_none()


async def list_by_repository(
    db: AsyncSession,
    *,
    repository_id: UUID,
    branch_name: str | None = None,
    file_path: str | None = None,
    chunk_type: ChunkType | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[CodeChunk], int]:
    query = select(CodeChunk).where(CodeChunk.repository_id == repository_id)
    count_query = (
        select(func.count()).select_from(CodeChunk).where(CodeChunk.repository_id == repository_id)
    )

    if branch_name is not None:
        query = query.where(CodeChunk.branch_name == branch_name)
        count_query = count_query.where(CodeChunk.branch_name == branch_name)
    if file_path is not None:
        query = query.where(CodeChunk.file_path == file_path)
        count_query = count_query.where(CodeChunk.file_path == file_path)
    if chunk_type is not None:
        query = query.where(CodeChunk.chunk_type == chunk_type)
        count_query = count_query.where(CodeChunk.chunk_type == chunk_type)

    total_result = await db.execute(count_query)
    total = int(total_result.scalar_one())

    result = await db.execute(
        query.order_by(CodeChunk.file_path, CodeChunk.start_line).limit(limit).offset(offset)
    )
    return list(result.scalars().all()), total


async def list_by_file(
    db: AsyncSession,
    *,
    repository_id: UUID,
    file_path: str,
    branch_name: str | None = None,
) -> list[CodeChunk]:
    query = select(CodeChunk).where(
        CodeChunk.repository_id == repository_id,
        CodeChunk.file_path == file_path,
    )
    if branch_name is not None:
        query = query.where(CodeChunk.branch_name == branch_name)

    result = await db.execute(query.order_by(CodeChunk.start_line))
    return list(result.scalars().all())


async def get_existing_hashes_for_branch(
    db: AsyncSession,
    *,
    repository_id: UUID,
    branch_name: str,
) -> dict[tuple[str, str, str, int], tuple[UUID, str]]:
    """Map (file_path, symbol_name, chunk_type, start_line) -> (chunk_id, content_hash)."""
    result = await db.execute(
        select(
            CodeChunk.id,
            CodeChunk.file_path,
            CodeChunk.symbol_name,
            CodeChunk.chunk_type,
            CodeChunk.start_line,
            CodeChunk.content_hash,
        ).where(
            CodeChunk.repository_id == repository_id,
            CodeChunk.branch_name == branch_name,
        )
    )
    mapping: dict[tuple[str, str, str, int], tuple[UUID, str]] = {}
    for row in result.all():
        key = (row.file_path, row.symbol_name, row.chunk_type.value, row.start_line)
        mapping[key] = (row.id, row.content_hash)
    return mapping


async def bulk_upsert(
    db: AsyncSession,
    *,
    chunks: list[ChunkCreate],
) -> tuple[list[CodeChunk], list[CodeChunk]]:
    """Upsert chunks. Returns (all_chunks, chunks_needing_embedding)."""
    if not chunks:
        return [], []

    repository_id = chunks[0].repository_id
    branch_name = chunks[0].branch_name
    existing = await get_existing_hashes_for_branch(
        db, repository_id=repository_id, branch_name=branch_name
    )

    values = [
        {
            "id": uuid.uuid4(),
            "repository_id": item.repository_id,
            "branch_name": item.branch_name,
            "file_path": item.file_path,
            "chunk_type": item.chunk_type,
            "symbol_name": item.symbol_name,
            "parent_symbol": item.parent_symbol,
            "start_line": item.start_line,
            "end_line": item.end_line,
            "content": item.content,
            "content_hash": item.content_hash,
            "chunk_source": item.chunk_source,
            "base_commit_hash": item.base_commit_hash,
            "head_commit_hash": item.head_commit_hash,
            "change_type": item.change_type,
        }
        for item in chunks
    ]

    stmt = insert(CodeChunk).values(values)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_code_chunks_symbol_location",
        set_={
            "parent_symbol": stmt.excluded.parent_symbol,
            "end_line": stmt.excluded.end_line,
            "content": stmt.excluded.content,
            "content_hash": stmt.excluded.content_hash,
            "chunk_source": stmt.excluded.chunk_source,
            "base_commit_hash": stmt.excluded.base_commit_hash,
            "head_commit_hash": stmt.excluded.head_commit_hash,
            "change_type": stmt.excluded.change_type,
            "updated_at": func.now(),
        },
    ).returning(CodeChunk)

    result = await db.execute(stmt)
    upserted = list(result.scalars().all())

    needing_embedding: list[CodeChunk] = []
    for chunk in upserted:
        key = (
            chunk.file_path,
            chunk.symbol_name,
            chunk.chunk_type.value,
            chunk.start_line,
        )
        prior = existing.get(key)
        if prior is None or prior[1] != chunk.content_hash:
            needing_embedding.append(chunk)

    return upserted, needing_embedding


async def count_by_repository(db: AsyncSession, repository_id: UUID) -> int:
    result = await db.execute(
        select(func.count()).select_from(CodeChunk).where(CodeChunk.repository_id == repository_id)
    )
    return int(result.scalar_one())


async def count_by_type(
    db: AsyncSession,
    repository_id: UUID,
) -> dict[str, int]:
    result = await db.execute(
        select(CodeChunk.chunk_type, func.count())
        .where(CodeChunk.repository_id == repository_id)
        .group_by(CodeChunk.chunk_type)
    )
    return {row[0].value: int(row[1]) for row in result.all()}


async def delete_for_repository(db: AsyncSession, repository_id: UUID) -> None:
    await db.execute(delete(CodeChunk).where(CodeChunk.repository_id == repository_id))
    await db.flush()


async def delete_for_branch(
    db: AsyncSession,
    *,
    repository_id: UUID,
    branch_name: str,
) -> None:
    await db.execute(
        delete(CodeChunk).where(
            CodeChunk.repository_id == repository_id,
            CodeChunk.branch_name == branch_name,
        )
    )
    await db.flush()


async def list_chunks_needing_embedding(
    db: AsyncSession,
    *,
    repository_id: UUID,
    branch_name: str | None = None,
) -> list[CodeChunk]:
    from app.models.chunk_embedding import ChunkEmbedding

    query = (
        select(CodeChunk)
        .outerjoin(ChunkEmbedding, ChunkEmbedding.chunk_id == CodeChunk.id)
        .where(
            CodeChunk.repository_id == repository_id,
            ChunkEmbedding.chunk_id.is_(None),
        )
    )
    if branch_name is not None:
        query = query.where(CodeChunk.branch_name == branch_name)

    result = await db.execute(query.order_by(CodeChunk.file_path, CodeChunk.start_line))
    return list(result.scalars().all())
