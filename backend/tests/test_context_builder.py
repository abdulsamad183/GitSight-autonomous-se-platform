from uuid import uuid4

import pytest

from app.core.config import Settings
from app.schemas.search import RetrievalContextItem
from app.services.ai.context_builder import ContextBuilder


def _item(
    *,
    file_path: str,
    symbol_name: str,
    content: str,
    chunk_type: str = "function",
) -> RetrievalContextItem:
    return RetrievalContextItem(
        chunk_id=uuid4(),
        symbol_name=symbol_name,
        file_path=file_path,
        chunk_type=chunk_type,
        content=content,
    )


@pytest.mark.asyncio
async def test_context_builder_groups_by_file():
    class FakeSearchService:
        async def retrieve_context(self, repository_id, query, top_k=5, branch=None):
            return [
                _item(file_path="a.py", symbol_name="foo", content="def foo(): pass"),
                _item(file_path="b.py", symbol_name="bar", content="def bar(): pass"),
                _item(file_path="a.py", symbol_name="baz", content="def baz(): pass"),
            ]

    settings = Settings(rag_max_context_chars=48_000)
    builder = ContextBuilder(FakeSearchService(), settings)  # type: ignore[arg-type]
    built = await builder.build(repository_id=uuid4(), user_query="test")

    assert built.chunks_used == 3
    assert "File: a.py" in built.text or "## File: a.py" in built.text
    assert "foo" in built.text and "baz" in built.text
    assert len(built.sources) == 3


@pytest.mark.asyncio
async def test_context_builder_respects_char_budget():
    class FakeSearchService:
        async def retrieve_context(self, repository_id, query, top_k=5, branch=None):
            return [
                _item(file_path="a.py", symbol_name="one", content="x" * 1000),
                _item(file_path="b.py", symbol_name="two", content="y" * 1000),
                _item(file_path="c.py", symbol_name="three", content="z" * 1000),
            ]

    settings = Settings(rag_max_context_chars=2500)
    builder = ContextBuilder(FakeSearchService(), settings)  # type: ignore[arg-type]
    built = await builder.build(repository_id=uuid4(), user_query="test")

    assert built.chunks_used < 3
    assert len(built.text) <= 2500 or built.chunks_used == 1


@pytest.mark.asyncio
async def test_context_builder_empty_retrieval():
    class FakeSearchService:
        async def retrieve_context(self, repository_id, query, top_k=5, branch=None):
            return []

    builder = ContextBuilder(FakeSearchService(), Settings())  # type: ignore[arg-type]
    built = await builder.build(repository_id=uuid4(), user_query="test")
    assert built.chunks_used == 0
    assert (
        "No relevant code chunks found" in built.text
        or "(No relevant code chunks found.)" in built.text
    )
