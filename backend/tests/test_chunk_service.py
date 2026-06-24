from unittest.mock import MagicMock
from uuid import uuid4

from app.models.symbol import SymbolType
from app.services.indexing.chunk_service import ChunkService
from app.utils.source_extractor import compute_content_hash


def test_create_chunk_extracts_source():
    service = ChunkService(db=MagicMock())
    symbol = MagicMock()
    symbol.symbol_type = SymbolType.FUNCTION
    symbol.symbol_name = "hello"
    symbol.start_line = 1
    symbol.end_line = 2

    source = b"def hello():\n    return 1\n"
    draft = service.create_chunk(
        symbol=symbol,
        file_path="main.py",
        source=source,
        branch_name="main",
        repository_id=uuid4(),
    )

    assert draft is not None
    assert draft.chunk_type == "function"
    assert draft.symbol_name == "hello"
    assert "def hello():" in draft.content
    assert draft.content_hash == compute_content_hash(draft.content)


def test_create_chunk_creates_class_chunk():
    service = ChunkService(db=MagicMock())
    symbol = MagicMock()
    symbol.symbol_type = SymbolType.CLASS
    symbol.symbol_name = "Foo"
    symbol.start_line = 1
    symbol.end_line = 2

    draft = service.create_chunk(
        symbol=symbol,
        file_path="main.py",
        source=b"class Foo:\n    pass\n",
        branch_name="main",
        repository_id=uuid4(),
    )
    assert draft is not None
    assert draft.chunk_type == "class"
