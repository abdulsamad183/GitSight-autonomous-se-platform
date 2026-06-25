from pathlib import Path
from unittest.mock import MagicMock, patch
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
        head_commit_hash="abc123",
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
        head_commit_hash="abc123",
    )
    assert draft is not None
    assert draft.chunk_type == "class"


def test_file_chunks_for_path_chunks_markdown_by_heading():
    service = ChunkService(db=MagicMock())
    repository_id = uuid4()
    drafts = service._file_chunks_for_path(
        file_path="README.md",
        extension=".md",
        content="# Title\n\nOverview\n\n## Setup\n\nInstall steps\n",
        repository_id=repository_id,
        branch_name="main",
        head_commit_hash="abc123",
    )
    assert len(drafts) == 2
    assert drafts[0].symbol_name == "README.md#Title"
    assert drafts[1].symbol_name == "README.md#Setup"
    assert drafts[0].repository_id == repository_id


def test_create_chunks_only_new_files_skips_existing_paths():
    service = ChunkService(db=MagicMock())
    repository_id = uuid4()

    async def _run():
        service.db = MagicMock()
        with (
            patch(
                "app.services.indexing.chunk_service.snapshot_repository.get_for_branch",
                return_value=MagicMock(id=uuid4()),
            ),
            patch(
                "app.services.indexing.chunk_service.code_chunk_repository.list_chunked_file_paths",
                return_value={"main.py", "README.md"},
            ),
            patch(
                "app.services.indexing.chunk_service.symbol_repository"
                ".list_for_snapshot_with_files",
                return_value=[],
            ),
            patch(
                "app.services.indexing.chunk_service.file_repository.list_for_snapshot",
                return_value=[],
            ),
            patch(
                "app.services.indexing.chunk_service.code_chunk_repository.bulk_upsert",
                return_value=([], []),
            ),
        ):
            stats, _ = await service.create_chunks(
                repository_id=repository_id,
                branch_name="main",
                clone_path=Path("/tmp"),
                head_commit_hash="abc123",
                only_new_files=True,
            )
            return stats

    import asyncio

    stats = asyncio.run(_run())
    assert stats.total_chunks == 0
