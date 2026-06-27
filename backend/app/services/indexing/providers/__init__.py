from app.core.config import Settings
from app.services.indexing.providers.google_embedding import GoogleEmbeddingBackend
from app.services.indexing.providers.local_embedding import LocalEmbeddingBackend
from app.services.indexing.providers.protocol import EmbeddingBackend

__all__ = [
    "EmbeddingBackend",
    "GoogleEmbeddingBackend",
    "LocalEmbeddingBackend",
    "get_embedding_backend",
]


def get_embedding_backend(settings: Settings) -> EmbeddingBackend:
    if settings.embedding_provider == "google":
        return GoogleEmbeddingBackend(settings)
    return LocalEmbeddingBackend(settings)
