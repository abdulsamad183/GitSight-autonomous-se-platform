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


def test_generate_embeddings_uses_batch_encode():
    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])

    with patch(
        "app.services.indexing.embedding_service.get_embedding_model",
        return_value=mock_model,
    ):
        service = EmbeddingService(db=MagicMock())
        chunks = [_make_chunk("def a(): pass"), _make_chunk("def b(): pass")]
        result = service.generate_embeddings(chunks)

    mock_model.encode.assert_called_once()
    call_kwargs = mock_model.encode.call_args
    assert call_kwargs.kwargs["batch_size"] == service.settings.embedding_batch_size
    assert len(result) == 2


@pytest.mark.asyncio
async def test_embed_chunks_batches_db_writes():
    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([[0.1] * 384, [0.2] * 384])

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
