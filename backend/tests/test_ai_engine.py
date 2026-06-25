from collections.abc import AsyncIterator
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.services.ai.context_builder import ContextBuilder
from app.services.ai.engine import AIEngine
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.tools.executor import ToolExecutor
from app.services.ai.tools.planner import LLMToolPlanner
from app.services.ai.tools.registry import ToolRegistry
from app.services.ai.tools.types import ToolResult
from app.services.ai.types import ChatMessage, LLMCompletion, TokenUsage


class FakeLLM:
    async def generate(self, messages: list[ChatMessage]) -> LLMCompletion:
        return LLMCompletion(
            content="Auth uses JWT.",
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )

    async def stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        for token in ["Auth ", "uses ", "JWT."]:
            yield token

    async def generate_structured(self, messages):
        return {
            "reasoning": "search auth",
            "steps": [
                {
                    "tool": "search",
                    "arguments": {"action": "retrieve_context", "query": "auth"},
                }
            ],
        }

    async def health(self) -> bool:
        return True


class FakeSearchTool:
    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return "search"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "query": {"type": "string"},
            },
            "required": ["action", "query"],
        }

    async def execute(self, ctx, arguments):
        from app.services.ai.types import ChatSource

        return ToolResult(
            tool_name="search",
            success=True,
            text="# Retrieved Code\n\ndef auth(): pass",
            sources=[
                ChatSource(
                    chunk_id=uuid4(),
                    file_path="auth.py",
                    symbol_name="auth",
                    chunk_type="function",
                    source_tool="search",
                )
            ],
        )


@pytest.mark.asyncio
async def test_ai_engine_answer_question():
    registry = ToolRegistry()
    registry.register(FakeSearchTool())
    settings = Settings()
    planner = LLMToolPlanner(registry, PromptBuilder(), FakeLLM(), settings)
    executor = ToolExecutor(registry, settings)
    engine = AIEngine(
        AsyncMock(),
        planner,
        executor,
        ContextBuilder(settings),
        PromptBuilder(),
        FakeLLM(),
        settings,
    )

    answer, sources, timing, token_usage, tools_used = await engine.answer_question(
        uuid4(), uuid4(), "auth flow"
    )
    assert answer == "Auth uses JWT."
    assert len(sources) == 1
    assert timing.planning_ms >= 0
    assert timing.tool_execution_ms >= 0
    assert token_usage is not None
    assert tools_used == ["search"]


@pytest.mark.asyncio
async def test_ai_engine_stream_answer():
    registry = ToolRegistry()
    registry.register(FakeSearchTool())
    settings = Settings()
    planner = LLMToolPlanner(registry, PromptBuilder(), FakeLLM(), settings)
    executor = ToolExecutor(registry, settings)
    engine = AIEngine(
        AsyncMock(),
        planner,
        executor,
        ContextBuilder(settings),
        PromptBuilder(),
        FakeLLM(),
        settings,
    )

    events = [event async for event in engine.stream_answer(uuid4(), uuid4(), "auth flow")]
    types = [event.type for event in events]
    assert "tool_start" in types
    assert "tool_end" in types
    token_events = [event for event in events if event.type == "token"]
    done_events = [event for event in events if event.type == "done"]
    assert "".join(event.content or "" for event in token_events) == "Auth uses JWT."
    assert len(done_events) == 1
    assert done_events[0].tools_used == ["search"]
