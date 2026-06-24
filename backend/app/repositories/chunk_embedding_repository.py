from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk_embedding import ChunkEmbedding


async def bulk_upsert(
    db: AsyncSession,
    *,
    chunk_ids: list[UUID],
    embeddings: list[list[float]],
    model_name: str,
) -> None:
    if not chunk_ids:
        return
    if len(chunk_ids) != len(embeddings):
        raise ValueError("chunk_ids and embeddings must have the same length")

    values = [
        {
            "chunk_id": chunk_id,
            "embedding": embedding,
            "model_name": model_name,
        }
        for chunk_id, embedding in zip(chunk_ids, embeddings, strict=True)
    ]

    stmt = insert(ChunkEmbedding).values(values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["chunk_id"],
        set_={
            "embedding": stmt.excluded.embedding,
            "model_name": stmt.excluded.model_name,
            "created_at": func.now(),
        },
    )
    await db.execute(stmt)
    await db.flush()


async def get_by_chunk_id(db: AsyncSession, chunk_id: UUID) -> ChunkEmbedding | None:
    result = await db.execute(select(ChunkEmbedding).where(ChunkEmbedding.chunk_id == chunk_id))
    return result.scalar_one_or_none()


async def count_for_repository(db: AsyncSession, repository_id: UUID) -> int:
    from app.models.code_chunk import CodeChunk

    result = await db.execute(
        select(func.count())
        .select_from(ChunkEmbedding)
        .join(CodeChunk, CodeChunk.id == ChunkEmbedding.chunk_id)
        .where(CodeChunk.repository_id == repository_id)
    )
    return int(result.scalar_one())


async def delete_for_chunks(db: AsyncSession, chunk_ids: list[UUID]) -> None:
    if not chunk_ids:
        return
    await db.execute(delete(ChunkEmbedding).where(ChunkEmbedding.chunk_id.in_(chunk_ids)))
    await db.flush()
