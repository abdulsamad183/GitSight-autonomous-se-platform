from collections.abc import AsyncIterator
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.services.ai.context_builder import ContextBuilder
from app.services.ai.engine import AIEngine
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.types import ChatMessage, LLMCompletion, TokenUsage


class FakeSearchService:
    async def retrieve_context(self, repository_id, query, top_k=5, branch=None):
        from app.schemas.search import RetrievalContextItem

        return [
            RetrievalContextItem(
                chunk_id=uuid4(),
                symbol_name="hello",
                file_path="main.py",
                chunk_type="function",
                content="def hello(): pass",
            )
        ]


class FakeLLMProvider:
    async def generate(self, messages: list[ChatMessage]) -> LLMCompletion:
        return LLMCompletion(
            content="Auth uses JWT.",
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )

    async def stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        for token in ["Auth ", "uses ", "JWT."]:
            yield token

    async def health(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_ai_engine_answer_question():
    settings = Settings()
    engine = AIEngine(
        ContextBuilder(FakeSearchService(), settings),  # type: ignore[arg-type]
        PromptBuilder(),
        FakeLLMProvider(),
        settings,
    )

    answer, sources, timing, token_usage = await engine.answer_question(uuid4(), "auth flow")
    assert answer == "Auth uses JWT."
    assert len(sources) == 1
    assert timing.total_ms >= 0
    assert token_usage is not None
    assert token_usage.total_tokens == 15


@pytest.mark.asyncio
async def test_ai_engine_stream_answer():
    settings = Settings()
    engine = AIEngine(
        ContextBuilder(FakeSearchService(), settings),  # type: ignore[arg-type]
        PromptBuilder(),
        FakeLLMProvider(),
        settings,
    )

    events = [event async for event in engine.stream_answer(uuid4(), "auth flow")]
    token_events = [event for event in events if event.type == "token"]
    done_events = [event for event in events if event.type == "done"]

    assert "".join(event.content or "" for event in token_events) == "Auth uses JWT."
    assert len(done_events) == 1
    assert done_events[0].sources is not None
