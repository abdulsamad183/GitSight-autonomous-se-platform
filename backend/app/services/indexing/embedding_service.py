import gc
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.code_chunk import CodeChunk
from app.repositories import chunk_embedding_repository, code_chunk_repository
from app.services.indexing.providers import EmbeddingBackend, get_embedding_backend

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, db: AsyncSession, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self._backend: EmbeddingBackend = get_embedding_backend(self.settings)

    def generate_embedding(self, text: str) -> list[float]:
        return self._backend.embed_passages([text])[0]

    def generate_query_embedding(self, text: str) -> list[float]:
        return self._backend.embed_query(text)

    def generate_embeddings(self, chunks: list[CodeChunk]) -> list[list[float]]:
        if not chunks:
            return []
        return self._backend.embed_passages([chunk.content for chunk in chunks])

    async def embed_chunk(self, chunk_id: UUID) -> None:
        chunk = await code_chunk_repository.get_by_id(self.db, chunk_id)
        if chunk is None:
            return

        embedding = self.generate_embedding(chunk.content)
        await chunk_embedding_repository.bulk_upsert(
            self.db,
            chunk_ids=[chunk_id],
            embeddings=[embedding],
            model_name=self.settings.effective_embedding_model_name,
        )

    async def embed_chunks(self, chunks: list[CodeChunk]) -> int:
        if not chunks:
            return 0

        total = len(chunks)
        embedded = 0
        batch_size = self.settings.effective_embedding_batch_size

        for start in range(0, total, batch_size):
            batch = chunks[start : start + batch_size]
            embeddings = self.generate_embeddings(batch)
            await chunk_embedding_repository.bulk_upsert(
                self.db,
                chunk_ids=[chunk.id for chunk in batch],
                embeddings=embeddings,
                model_name=self.settings.effective_embedding_model_name,
            )
            embedded += len(batch)
            del embeddings
            if self.settings.should_gc_between_embedding_batches:
                gc.collect()
            logger.info("Embedded %d/%d chunks", embedded, total)

        logger.info("Embedded %d chunks", embedded)
        return embedded

    async def reindex_repository(self, repository_id: UUID) -> int:
        chunks = await code_chunk_repository.list_chunks_needing_embedding(
            self.db, repository_id=repository_id
        )
        return await self.embed_chunks(chunks)
