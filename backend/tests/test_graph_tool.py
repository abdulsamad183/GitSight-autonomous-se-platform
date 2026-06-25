from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.schemas.graph import GraphStats, RepositoryGraphResponse
from app.services.ai.tools.graph_tool import GraphTool
from app.services.ai.tools.types import ToolExecutionContext


@pytest.mark.asyncio
async def test_graph_tool_dependents():
    tool = GraphTool()
    ctx = ToolExecutionContext(
        db=AsyncMock(),
        user_id=uuid4(),
        repository_id=uuid4(),
        branch="main",
        settings=Settings(),
    )
    with patch(
        "app.services.ai.tools.graph_tool.graph_query_service.dependents",
        new_callable=AsyncMock,
        return_value=["app/main.py"],
    ):
        result = await tool.execute(ctx, {"action": "dependents", "file_path": "services/auth.py"})
    assert result.success is True
    assert "app/main.py" in result.text


@pytest.mark.asyncio
async def test_graph_tool_structure():
    tool = GraphTool()
    ctx = ToolExecutionContext(
        db=AsyncMock(),
        user_id=uuid4(),
        repository_id=uuid4(),
        branch=None,
        settings=Settings(),
    )
    graph = RepositoryGraphResponse(
        branch="main",
        nodes=[],
        edges=[],
        stats=GraphStats(files_count=1, classes_count=1, methods_count=1),
    )
    with patch(
        "app.services.ai.tools.graph_tool.graph_query_service.get_structure_graph",
        new_callable=AsyncMock,
        return_value=graph,
    ):
        result = await tool.execute(ctx, {"action": "structure"})
    assert result.success is True
    assert "Dependency Graph" in result.text
