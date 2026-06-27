from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import numpy as np
import pytest

from app.models.code_chunk import ChunkType, CodeChunk
from app.services.indexing.embedding_service import EmbeddingService


@pytest.fixture(autouse=True)
def reset_model_singleton():
    import app.services.indexing.embedding_service as module

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
        "app.services.indexing.embedding_service.get_embedding_model",
        return_value=mock_model,
    ):
        service = EmbeddingService(db=MagicMock())
        chunks = [_make_chunk("def a(): pass"), _make_chunk("def b(): pass")]
        result = service.generate_embeddings(chunks)

    mock_model.passage_embed.assert_called_once()
    call_kwargs = mock_model.passage_embed.call_args
    assert call_kwargs.kwargs["batch_size"] == service.settings.effective_embedding_batch_size
    assert len(result) == 2


def test_generate_query_embedding_uses_query_embed():
    mock_model = _mock_fastembed_model()

    with patch(
        "app.services.indexing.embedding_service.get_embedding_model",
        return_value=mock_model,
    ):
        service = EmbeddingService(db=MagicMock())
        result = service.generate_query_embedding("search me")

    mock_model.query_embed.assert_called_once_with(["search me"])
    assert result == [0.5, 0.6]


@pytest.mark.asyncio
async def test_embed_chunks_batches_db_writes():
    mock_model = _mock_fastembed_model()

    chunks = [_make_chunk("def a(): pass"), _make_chunk("def b(): pass")]

    with (
        patch(
            "app.services.indexing.embedding_service.get_embedding_model",
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
