import logging
import threading
from typing import TYPE_CHECKING

from app.core.config import Settings

if TYPE_CHECKING:
    from fastembed import TextEmbedding

logger = logging.getLogger(__name__)

_model: "TextEmbedding | None" = None
_model_lock = threading.Lock()


def get_embedding_model(settings: Settings) -> "TextEmbedding":
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                from fastembed import TextEmbedding

                logger.info("Loading embedding model %s", settings.embedding_model_name)
                _model = TextEmbedding(
                    model_name=settings.embedding_model_name,
                    threads=settings.embedding_threads,
                )
                logger.info("Embedding model loaded")
    return _model


class LocalEmbeddingBackend:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        model = get_embedding_model(self.settings)
        vectors = list(
            model.passage_embed(
                texts,
                batch_size=self.settings.effective_embedding_batch_size,
            )
        )
        return [vector.tolist() for vector in vectors]

    def embed_query(self, text: str) -> list[float]:
        model = get_embedding_model(self.settings)
        return list(model.query_embed([text]))[0].tolist()
