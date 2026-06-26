from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.models.pull_request import PullRequestState
from app.services.pr_review.planner import (
    CodeReviewPlanner,
    _build_tool_plan,
    _format_pr_metadata,
)


def _make_pull_request(**overrides):
    pull_request = MagicMock()
    pull_request.id = overrides.get("id", uuid4())
    pull_request.number = overrides.get("number", 42)
    pull_request.title = overrides.get("title", "Add feature")
    pull_request.author_username = overrides.get("author_username", "dev")
    pull_request.state = overrides.get("state", PullRequestState.OPEN)
    pull_request.source_branch = overrides.get("source_branch", "feature/x")
    pull_request.target_branch = overrides.get("target_branch", "main")
    pull_request.is_draft = overrides.get("is_draft", False)
    pull_request.is_merged = overrides.get("is_merged", False)
    pull_request.description = overrides.get("description", "Implements feature x")
    return pull_request


def test_format_pr_metadata_includes_core_fields():
    pull_request = _make_pull_request()
    text = _format_pr_metadata(pull_request)
    assert "# Pull Request Metadata" in text
    assert "#42" in text
    assert "Add feature" in text
    assert "feature/x" in text
    assert "main" in text
    assert "Implements feature x" in text


def test_build_tool_plan_includes_compare_and_graph_steps():
    settings = Settings(pr_review_max_tool_steps=20, pr_review_max_graph_files=2)
    pull_request = _make_pull_request()
    plan = _build_tool_plan(
        pull_request,
        changed_files=["src/auth.py", "src/user.py"],
        changes={"changed_files": [{"file_path": "src/auth.py", "hunks": []}]},
        settings=settings,
    )
    tools = [inv.tool_name for inv in plan.invocations]
    actions = [inv.arguments.get("action") for inv in plan.invocations]
    assert "repository" in tools
    assert "compare" in actions
    assert "summarize_changes" in actions
    assert "structure" in actions
    assert "dependents" in actions
    assert "dependencies" in actions
    assert "retrieve_context" in actions
    assert len(plan.invocations) <= settings.pr_review_max_tool_steps


def test_build_tool_plan_without_source_branch_is_minimal():
    settings = Settings(pr_review_max_tool_steps=8)
    pull_request = _make_pull_request(source_branch=None, target_branch="main")
    plan = _build_tool_plan(pull_request, changed_files=[], changes={}, settings=settings)
    assert len(plan.invocations) == 1
    assert plan.invocations[0].tool_name == "repository"


@pytest.mark.asyncio
async def test_planner_handles_missing_branch_diff(monkeypatch):
    pull_request = _make_pull_request(source_branch=None)
    settings = Settings()

    monkeypatch.setattr(
        "app.services.pr_review.planner.branch_query_service.summarize_branch_changes",
        AsyncMock(),
    )

    planner = CodeReviewPlanner()
    plan = await planner.plan(
        AsyncMock(),
        repository_id=uuid4(),
        pull_request=pull_request,
        settings=settings,
    )

    assert plan.pull_request_id == pull_request.id
    assert "No source branch available" in plan.diff_context_text
    assert plan.tool_plan.invocations[0].tool_name == "repository"


@pytest.mark.asyncio
async def test_planner_assembles_diff_context_from_chunks(monkeypatch):
    pull_request = _make_pull_request()
    settings = Settings(pr_review_max_diff_chunks=5, pr_review_max_graph_files=2)

    chunk = MagicMock()
    chunk.file_path = "src/auth.py"
    chunk.symbol_name = "authenticate"
    chunk.start_line = 10
    chunk.end_line = 20
    chunk.change_type = MagicMock(value="modified")
    chunk.content = "+def authenticate():\n+    pass"

    monkeypatch.setattr(
        "app.services.pr_review.planner.branch_query_service.summarize_branch_changes",
        AsyncMock(
            return_value={
                "changed_files": [
                    {"file_path": "src/auth.py", "hunks": [{"symbol_name": "authenticate"}]}
                ],
                "total_diff_chunks": 1,
                "change_type_counts": {"modified": 1},
            }
        ),
    )
    monkeypatch.setattr(
        "app.services.pr_review.planner.code_chunk_repository.list_by_repository",
        AsyncMock(return_value=([chunk], 1)),
    )

    planner = CodeReviewPlanner()
    plan = await planner.plan(
        AsyncMock(),
        repository_id=uuid4(),
        pull_request=pull_request,
        settings=settings,
    )

    assert "src/auth.py" in plan.diff_context_text
    assert "authenticate" in plan.diff_context_text
    assert plan.title == "PR #42: Add feature"
