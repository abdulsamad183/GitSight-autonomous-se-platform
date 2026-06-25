import logging
import time
from collections.abc import AsyncIterator
from uuid import UUID

from app.core.config import Settings
from app.services.ai.context_builder import ContextBuilder
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.providers.base import LLMProvider
from app.services.ai.types import ChatStreamEvent, ChatTiming, TokenUsage

logger = logging.getLogger(__name__)


class AIEngine:
    def __init__(
        self,
        context_builder: ContextBuilder,
        prompt_builder: PromptBuilder,
        llm_provider: LLMProvider,
        settings: Settings,
    ) -> None:
        self.context_builder = context_builder
        self.prompt_builder = prompt_builder
        self.llm_provider = llm_provider
        self.settings = settings

    async def answer_question(
        self,
        repository_id: UUID,
        question: str,
        *,
        branch: str | None = None,
    ) -> tuple[str, list, ChatTiming, TokenUsage | None]:
        total_start = time.perf_counter()

        retrieval_start = time.perf_counter()
        built = await self.context_builder.build(
            repository_id=repository_id,
            user_query=question,
            branch=branch,
        )
        retrieval_ms = (time.perf_counter() - retrieval_start) * 1000

        prompt_start = time.perf_counter()
        messages = self.prompt_builder.build_chat_prompt(built.text, question)
        prompt_build_ms = (time.perf_counter() - prompt_start) * 1000

        llm_start = time.perf_counter()
        completion = await self.llm_provider.generate(messages)
        llm_ms = (time.perf_counter() - llm_start) * 1000

        total_ms = (time.perf_counter() - total_start) * 1000
        timing = ChatTiming(
            retrieval_ms=round(retrieval_ms, 2),
            prompt_build_ms=round(prompt_build_ms, 2),
            llm_ms=round(llm_ms, 2),
            total_ms=round(total_ms, 2),
        )

        logger.info(
            "chat_completed",
            extra={
                "repository_id": str(repository_id),
                "chunks_used": built.chunks_used,
                "retrieval_time_ms": timing.retrieval_ms,
                "prompt_build_time_ms": timing.prompt_build_ms,
                "llm_time_ms": timing.llm_ms,
                "total_time_ms": timing.total_ms,
                "stream": False,
            },
        )

        return completion.content, built.sources, timing, completion.token_usage

    async def stream_answer(
        self,
        repository_id: UUID,
        question: str,
        *,
        branch: str | None = None,
    ) -> AsyncIterator[ChatStreamEvent]:
        total_start = time.perf_counter()

        try:
            retrieval_start = time.perf_counter()
            built = await self.context_builder.build(
                repository_id=repository_id,
                user_query=question,
                branch=branch,
            )
            retrieval_ms = (time.perf_counter() - retrieval_start) * 1000

            prompt_start = time.perf_counter()
            messages = self.prompt_builder.build_chat_prompt(built.text, question)
            prompt_build_ms = (time.perf_counter() - prompt_start) * 1000

            llm_start = time.perf_counter()
            async for token in self.llm_provider.stream(messages):
                yield ChatStreamEvent(type="token", content=token)
            llm_ms = (time.perf_counter() - llm_start) * 1000

            total_ms = (time.perf_counter() - total_start) * 1000
            timing = ChatTiming(
                retrieval_ms=round(retrieval_ms, 2),
                prompt_build_ms=round(prompt_build_ms, 2),
                llm_ms=round(llm_ms, 2),
                total_ms=round(total_ms, 2),
            )

            logger.info(
                "chat_completed",
                extra={
                    "repository_id": str(repository_id),
                    "chunks_used": built.chunks_used,
                    "retrieval_time_ms": timing.retrieval_ms,
                    "prompt_build_time_ms": timing.prompt_build_ms,
                    "llm_time_ms": timing.llm_ms,
                    "total_time_ms": timing.total_ms,
                    "stream": True,
                },
            )

            yield ChatStreamEvent(
                type="done",
                sources=built.sources,
                execution_time_ms=timing.total_ms,
                timing=timing,
            )
        except Exception as exc:
            logger.exception("chat_stream_failed for repository %s", repository_id)
            yield ChatStreamEvent(type="error", message=str(exc))
