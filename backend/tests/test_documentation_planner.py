import pytest

from app.models.repository_document import DocumentType
from app.services.documentation.planner import DocumentationPlanner, _tool_plan_for_type


def test_tool_plan_repository_overview():
    plan = _tool_plan_for_type(DocumentType.REPOSITORY_OVERVIEW, "main")
    assert len(plan.invocations) == 2
    assert plan.invocations[0].tool_name == "repository"
    assert plan.invocations[1].tool_name == "repository"


def test_tool_plan_architecture_includes_graph():
    plan = _tool_plan_for_type(DocumentType.ARCHITECTURE_OVERVIEW, "main")
    tools = [inv.tool_name for inv in plan.invocations]
    assert "graph" in tools
    graph_inv = next(inv for inv in plan.invocations if inv.tool_name == "graph")
    assert graph_inv.arguments.get("branch") == "main"


def test_tool_plan_branch_summary_with_branch():
    plan = _tool_plan_for_type(DocumentType.BRANCH_SUMMARY, "feature")
    tools = [inv.tool_name for inv in plan.invocations]
    assert tools.count("branch") >= 2


def test_tool_plan_branch_summary_without_branch():
    plan = _tool_plan_for_type(DocumentType.BRANCH_SUMMARY, None)
    assert len(plan.invocations) == 1
    assert plan.invocations[0].arguments["action"] == "list"


@pytest.mark.asyncio
async def test_planner_skips_ai_when_discovery_finds_doc():
    from unittest.mock import AsyncMock
    from uuid import uuid4

    from app.services.documentation.discovery import DiscoveredDocument

    discovery = AsyncMock()
    discovery.find = AsyncMock(
        return_value=DiscoveredDocument(
            file_path="README.md",
            content="# Project\n\n" + ("x" * 100),
            title="Repository Overview",
        )
    )
    planner = DocumentationPlanner(discovery=discovery)
    plan = await planner.plan(
        None,
        repository_id=uuid4(),
        document_type=DocumentType.REPOSITORY_OVERVIEW,
        branch="main",
    )
    assert plan.requires_ai is False
    assert plan.existing_document is not None
    assert plan.tool_plan is None
