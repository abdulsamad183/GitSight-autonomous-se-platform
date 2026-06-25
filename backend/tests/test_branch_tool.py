from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.services.ai.tools.branch_tool import BranchTool
from app.services.ai.tools.types import ToolExecutionContext


@pytest.mark.asyncio
async def test_branch_tool_list():
    tool = BranchTool()
    ctx = ToolExecutionContext(
        db=AsyncMock(),
        user_id=uuid4(),
        repository_id=uuid4(),
        branch=None,
        settings=Settings(),
    )
    with patch(
        "app.services.ai.tools.branch_tool.branch_query_service.list_branches",
        new_callable=AsyncMock,
        return_value=[
            {"branch": "main", "files_count": 5, "classes_count": 1, "commit_hash": "abc"}
        ],
    ):
        result = await tool.execute(ctx, {"action": "list"})
    assert result.success is True
    assert "Branch Analysis" in result.text


@pytest.mark.asyncio
async def test_branch_tool_compare():
    tool = BranchTool()
    ctx = ToolExecutionContext(
        db=AsyncMock(),
        user_id=uuid4(),
        repository_id=uuid4(),
        branch=None,
        settings=Settings(),
    )
    with patch(
        "app.services.ai.tools.branch_tool.branch_query_service.compare_branches",
        new_callable=AsyncMock,
        return_value={
            "base_branch": "main",
            "head_branch": "dev",
            "base_stats": {"files_count": 10},
            "head_stats": {"files_count": 12},
            "head_changes": {"total_diff_chunks": 3, "changed_files": []},
        },
    ):
        result = await tool.execute(
            ctx,
            {"action": "compare", "base_branch": "main", "head_branch": "dev"},
        )
    assert result.success is True
    assert "main" in result.text and "dev" in result.text
