from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import numpy as np
import pytest

from app.core.config import Settings
from app.models.code_chunk import ChunkType, CodeChunk
from app.services.indexing.embedding_service import EmbeddingService
from app.services.indexing.providers.google_embedding import GoogleEmbeddingBackend


@pytest.fixture(autouse=True)
def reset_local_model_singleton():
    import app.services.indexing.providers.local_embedding as module

    module._model = None
    yield
    module._model = None


def _make_chunk(content: str) -> CodeChunk:
    chunk = CodeChunk(
        repository_id=uuid4(),
        branch_name="main",
        file_path="main.py",
        chunk_type=ChunkType.FUNCTION,
        symbol_name="hello",
        parent_symbol=None,
        start_line=1,
        end_line=2,
        content=content,
        content_hash="abc",
    )
    chunk.id = uuid4()
    return chunk


def _mock_fastembed_model() -> MagicMock:
    mock_model = MagicMock()

    def passage_embed(texts, batch_size=None, **kwargs):
        texts_list = [texts] if isinstance(texts, str) else list(texts)
        for _ in texts_list:
            yield np.array([0.1, 0.2])

    def query_embed(queries, **kwargs):
        queries_list = [queries] if isinstance(queries, str) else list(queries)
        for _ in queries_list:
            yield np.array([0.5, 0.6])

    mock_model.passage_embed.side_effect = passage_embed
    mock_model.query_embed.side_effect = query_embed
    return mock_model


def test_generate_embeddings_uses_batch_encode():
    mock_model = _mock_fastembed_model()

    with patch(
        "app.services.indexing.providers.local_embedding.get_embedding_model",
        return_value=mock_model,
    ):
        service = EmbeddingService(db=MagicMock())
        result = service.generate_embeddings(["def a(): pass", "def b(): pass"])

    mock_model.passage_embed.assert_called_once()
    call_kwargs = mock_model.passage_embed.call_args
    assert call_kwargs.kwargs["batch_size"] == service.settings.effective_embedding_batch_size
    assert len(result) == 2


@pytest.mark.asyncio
async def test_generate_query_embedding_uses_query_embed():
    mock_model = _mock_fastembed_model()

    with patch(
        "app.services.indexing.providers.local_embedding.get_embedding_model",
        return_value=mock_model,
    ):
        service = EmbeddingService(db=MagicMock())
        result = await service.generate_query_embedding("search me")

    mock_model.query_embed.assert_called_once_with(["search me"])
    assert result == [0.5, 0.6]


def test_google_backend_resolves_legacy_model_name():
    settings = Settings(
        embedding_provider="google",
        google_api_key="test-key",
        embedding_model_name="text-embedding-004",
        embedding_dimension=384,
    )
    backend = GoogleEmbeddingBackend(settings)
    assert backend._resolve_model_name() == "gemini-embedding-001"


def test_google_backend_embed_passages():
    settings = Settings(
        embedding_provider="google",
        google_api_key="test-key",
        embedding_model_name="gemini-embedding-001",
        embedding_dimension=384,
    )
    backend = GoogleEmbeddingBackend(settings)
    vector_a = [0.1] * 384
    vector_b = [0.3] * 384

    with patch.object(backend, "_post_with_retries") as mock_post:
        mock_post.return_value = {
            "embeddings": [{"values": vector_a}, {"values": vector_b}],
        }
        result = backend.embed_passages(["def a(): pass", "def b(): pass"])

    assert len(result) == 2
    assert all(len(vector) == 384 for vector in result)
    for vector in result:
        norm = sum(value * value for value in vector) ** 0.5
        assert abs(norm - 1.0) < 1e-6
    mock_post.assert_called_once()
    payload = mock_post.call_args.args[1]
    assert len(payload["requests"]) == 2
    assert payload["requests"][0]["model"] == "models/gemini-embedding-001"
    assert payload["requests"][0]["embedContentConfig"]["taskType"] == "RETRIEVAL_DOCUMENT"
    assert payload["requests"][0]["outputDimensionality"] == 384
    assert payload["requests"][0]["embedContentConfig"]["outputDimensionality"] == 384
    assert "gemini-embedding-001" in mock_post.call_args.args[0]


def test_google_backend_truncates_and_normalizes_oversized_vectors():
    settings = Settings(
        embedding_provider="google",
        google_api_key="test-key",
        embedding_model_name="gemini-embedding-001",
        embedding_dimension=384,
    )
    backend = GoogleEmbeddingBackend(settings)

    with patch.object(backend, "_post_with_retries") as mock_post:
        mock_post.return_value = {"embeddings": [{"values": [1.0, 0.0] * 1536}]}
        result = backend.embed_passages(["hello"])

    assert len(result) == 1
    assert len(result[0]) == 384
    norm = sum(value * value for value in result[0]) ** 0.5
    assert abs(norm - 1.0) < 1e-6


def test_google_backend_embed_query():
    settings = Settings(
        embedding_provider="google",
        google_api_key="test-key",
        embedding_model_name="gemini-embedding-001",
        embedding_dimension=384,
    )
    backend = GoogleEmbeddingBackend(settings)

    with patch.object(backend, "_post_with_retries") as mock_post:
        mock_post.return_value = {"embeddings": [{"values": [0.5] * 384}]}
        result = backend.embed_query("find auth")

    assert len(result) == 384
    payload = mock_post.call_args.args[1]
    assert payload["requests"][0]["embedContentConfig"]["taskType"] == "RETRIEVAL_QUERY"


@pytest.mark.asyncio
async def test_embed_chunks_batches_db_writes():
    mock_model = _mock_fastembed_model()

    chunks = [_make_chunk("def a(): pass"), _make_chunk("def b(): pass")]

    with (
        patch(
            "app.services.indexing.providers.local_embedding.get_embedding_model",
            return_value=mock_model,
        ),
        patch(
            "app.services.indexing.embedding_service.chunk_embedding_repository.bulk_upsert",
            new_callable=AsyncMock,
        ) as bulk_upsert,
    ):
        bulk_upsert.return_value = None
        db = MagicMock()
        service = EmbeddingService(db)
        count = await service.embed_chunks(chunks)

    assert count == 2
    bulk_upsert.assert_called_once()
