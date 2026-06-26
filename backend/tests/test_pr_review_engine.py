from collections.abc import AsyncIterator
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.services.ai.context_builder import ContextBuilder
from app.services.ai.engine import AIEngine
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.tools.executor import ToolExecutor
from app.services.ai.tools.registry import ToolRegistry
from app.services.ai.tools.types import ToolInvocation, ToolPlan, ToolResult
from app.services.ai.types import ChatMessage, LLMCompletion, TokenUsage
from app.services.pr_review.types import CodeReviewPlan


class FakeLLM:
    def __init__(self) -> None:
        self.messages: list[ChatMessage] = []

    async def generate(self, messages: list[ChatMessage]) -> LLMCompletion:
        self.messages = messages
        return LLMCompletion(
            content="# Summary\n\nLooks good.\n\n# Recommendation\n\nApprove",
            token_usage=TokenUsage(prompt_tokens=20, completion_tokens=10, total_tokens=30),
        )

    async def stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        yield "review"

    async def generate_structured(self, messages):
        return {"reasoning": "", "steps": []}

    async def health(self) -> bool:
        return True


class FakeRepositoryTool:
    @property
    def name(self) -> str:
        return "repository"

    @property
    def description(self) -> str:
        return "repo"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {"action": {"type": "string"}},
            "required": ["action"],
        }

    async def execute(self, ctx, arguments):
        return ToolResult(
            tool_name="repository",
            success=True,
            text="# Repository Metadata\n\nFiles: 3",
        )


@pytest.mark.asyncio
async def test_generate_pr_review_single_llm_call_includes_pr_metadata():
    registry = ToolRegistry()
    registry.register(FakeRepositoryTool())
    settings = Settings(rag_max_context_chars=10_000)
    executor = ToolExecutor(registry, settings)
    llm = FakeLLM()
    engine = AIEngine(
        AsyncMock(),
        AsyncMock(),
        executor,
        ContextBuilder(settings),
        PromptBuilder(),
        llm,
        settings,
    )

    review_plan = CodeReviewPlan(
        pull_request_id=uuid4(),
        title="PR #9: Auth fix",
        pr_metadata_text="# Pull Request Metadata\n\nNumber: #9",
        diff_context_text="# Pull Request Changes\n\nFile: auth.py",
        tool_plan=ToolPlan(
            invocations=[ToolInvocation("repository", {"action": "summary"})],
        ),
        source_branch="feature/auth",
    )

    content, usage = await engine.generate_pr_review(
        uuid4(),
        uuid4(),
        review_plan,
        pr_number=9,
        branch="feature/auth",
    )

    assert content.startswith("# Summary")
    assert usage is not None
    assert len(llm.messages) == 2
    assert "PR #9: Auth fix" in llm.messages[1].content
    assert "Pull Request Metadata" in llm.messages[1].content
    assert "Pull Request Changes" in llm.messages[1].content
    assert "Repository Metadata" in llm.messages[1].content
