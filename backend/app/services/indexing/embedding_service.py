import gc
import logging
import threading
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.code_chunk import CodeChunk
from app.repositories import chunk_embedding_repository, code_chunk_repository

if TYPE_CHECKING:
    from fastembed import TextEmbedding

logger = logging.getLogger(__name__)

_model: "TextEmbedding | None" = None
_model_lock = threading.Lock()


def get_embedding_model() -> "TextEmbedding":
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                from fastembed import TextEmbedding

                settings = get_settings()
                logger.info("Loading embedding model %s", settings.embedding_model_name)
                _model = TextEmbedding(
                    model_name=settings.embedding_model_name,
                    threads=settings.embedding_threads,
                )
                logger.info("Embedding model loaded")
    return _model


class EmbeddingService:
    def __init__(self, db: AsyncSession, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()

    def _embed_passages(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        model = get_embedding_model()
        vectors = list(
            model.passage_embed(
                texts,
                batch_size=self.settings.effective_embedding_batch_size,
            )
        )
        return [vector.tolist() for vector in vectors]

    def _embed_query(self, text: str) -> list[float]:
        model = get_embedding_model()
        return list(model.query_embed([text]))[0].tolist()

    def generate_embedding(self, text: str) -> list[float]:
        return self._embed_passages([text])[0]

    def generate_query_embedding(self, text: str) -> list[float]:
        return self._embed_query(text)

    def generate_embeddings(self, chunks: list[CodeChunk]) -> list[list[float]]:
        if not chunks:
            return []
        return self._embed_passages([chunk.content for chunk in chunks])

    async def embed_chunk(self, chunk_id: UUID) -> None:
        chunk = await code_chunk_repository.get_by_id(self.db, chunk_id)
        if chunk is None:
            return

        embedding = self.generate_embedding(chunk.content)
        await chunk_embedding_repository.bulk_upsert(
            self.db,
            chunk_ids=[chunk_id],
            embeddings=[embedding],
            model_name=self.settings.embedding_model_name,
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
                model_name=self.settings.embedding_model_name,
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
