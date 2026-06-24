import logging
import threading
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.code_chunk import CodeChunk
from app.repositories import chunk_embedding_repository, code_chunk_repository

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_model: "SentenceTransformer | None" = None
_model_lock = threading.Lock()


def get_embedding_model() -> "SentenceTransformer":
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer

                settings = get_settings()
                logger.info("Loading embedding model %s", settings.embedding_model_name)
                _model = SentenceTransformer(settings.embedding_model_name)
                logger.info("Embedding model loaded")
    return _model


class EmbeddingService:
    def __init__(self, db: AsyncSession, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()

    def generate_embedding(self, text: str) -> list[float]:
        model = get_embedding_model()
        vector = model.encode(text, show_progress_bar=False)
        return vector.tolist()

    def generate_embeddings(self, chunks: list[CodeChunk]) -> list[list[float]]:
        if not chunks:
            return []

        model = get_embedding_model()
        texts = [chunk.content for chunk in chunks]
        vectors = model.encode(
            texts,
            batch_size=self.settings.embedding_batch_size,
            show_progress_bar=False,
        )
        return [vector.tolist() for vector in vectors]

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
        batch_size = self.settings.embedding_batch_size

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
            logger.info("Embedded %d/%d chunks", embedded, total)

        logger.info("Embedded %d chunks", embedded)
        return embedded

    async def reindex_repository(self, repository_id: UUID) -> int:
        chunks = await code_chunk_repository.list_chunks_needing_embedding(
            self.db, repository_id=repository_id
        )
        return await self.embed_chunks(chunks)
