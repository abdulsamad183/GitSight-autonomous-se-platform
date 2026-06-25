from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.services.ai.tools.repository_metadata_tool import RepositoryMetadataTool
from app.services.ai.tools.types import ToolExecutionContext


@pytest.mark.asyncio
async def test_repository_metadata_tool_summary():
    tool = RepositoryMetadataTool()
    ctx = ToolExecutionContext(
        db=AsyncMock(),
        user_id=uuid4(),
        repository_id=uuid4(),
        branch=None,
        settings=Settings(),
    )
    summary = MagicMock()
    summary.model_dump.return_value = {
        "owner": "acme",
        "repository_name": "app",
        "default_branch": "main",
        "status": "ACTIVE",
        "analysis_status": "COMPLETED",
        "branches_count": 3,
        "files_count": 10,
        "classes_count": 2,
        "functions_count": 5,
        "methods_count": 8,
        "dependencies_count": 4,
    }
    branch = MagicMock()
    branch.model_dump.return_value = {
        "branch": "main",
        "files_count": 10,
        "classes_count": 2,
        "commit_hash": "abc123",
    }

    summary_path = (
        "app.services.ai.tools.repository_metadata_tool"
        ".repository_detail_service.get_repository_summary"
    )
    branches_path = (
        "app.services.ai.tools.repository_metadata_tool"
        ".repository_detail_service.list_repository_branches"
    )
    with (
        patch(summary_path, new_callable=AsyncMock, return_value=summary),
        patch(branches_path, new_callable=AsyncMock, return_value=[branch]),
    ):
        result = await tool.execute(ctx, {"action": "summary"})

    assert result.success is True
    assert "Repository Metadata" in result.text
    assert "acme" in result.text
