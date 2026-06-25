from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.schemas.search import RetrievalContextItem, SearchResponse
from app.services.ai.tools.search_tool import SearchTool
from app.services.ai.tools.types import ToolExecutionContext


@pytest.mark.asyncio
async def test_search_tool_retrieve_context():
    item = RetrievalContextItem(
        chunk_id=uuid4(),
        symbol_name="validate",
        file_path="auth.py",
        chunk_type="function",
        content="def validate(): pass",
    )
    search_service = AsyncMock()
    search_service.retrieve_context = AsyncMock(return_value=[item])
    tool = SearchTool(search_service)
    ctx = ToolExecutionContext(
        db=AsyncMock(),
        user_id=uuid4(),
        repository_id=uuid4(),
        branch="main",
        settings=Settings(),
    )
    result = await tool.execute(ctx, {"action": "retrieve_context", "query": "authentication"})
    assert result.success is True
    assert len(result.sources) == 1
    assert result.sources[0].source_tool == "search"


@pytest.mark.asyncio
async def test_search_tool_search_action():
    from app.schemas.search import SearchResult

    hit = SearchResult(
        chunk_id=uuid4(),
        symbol_name="login",
        file_path="auth.py",
        chunk_type="function",
        content_snippet="def login(): pass",
        final_score=0.9,
        start_line=1,
        end_line=2,
        branch_name="main",
    )
    search_service = AsyncMock()
    search_service.search = AsyncMock(
        return_value=SearchResponse(
            query="jwt",
            mode="hybrid",
            total_results=1,
            limit=5,
            offset=0,
            execution_time_ms=1.0,
            results=[hit],
        )
    )
    tool = SearchTool(search_service)
    ctx = ToolExecutionContext(
        db=AsyncMock(),
        user_id=uuid4(),
        repository_id=uuid4(),
        branch=None,
        settings=Settings(),
    )
    result = await tool.execute(ctx, {"action": "search", "query": "jwt"})
    assert result.success is True
    assert "jwt" in result.text.lower() or "login" in result.text
