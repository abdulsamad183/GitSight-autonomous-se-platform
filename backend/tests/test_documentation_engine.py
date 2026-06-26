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


class FakeLLM:
    def __init__(self) -> None:
        self.messages: list[ChatMessage] = []

    async def generate(self, messages: list[ChatMessage]) -> LLMCompletion:
        self.messages = messages
        return LLMCompletion(
            content="# Generated Doc\n\nOverview here.",
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )

    async def stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        yield "doc"

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
            text="# Repository Metadata\n\nFiles: 10",
        )


@pytest.mark.asyncio
async def test_generate_documentation_single_llm_call():
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

    plan = ToolPlan(
        invocations=[ToolInvocation("repository", {"action": "summary"})],
    )
    content, usage = await engine.generate_documentation(
        uuid4(),
        uuid4(),
        plan,
        document_type="repository_overview",
        title="Repository Overview",
    )

    assert content.startswith("# Generated Doc")
    assert usage is not None
    assert len(llm.messages) == 2
    assert "repository_overview" in llm.messages[1].content
    assert "Repository Metadata" in llm.messages[1].content
