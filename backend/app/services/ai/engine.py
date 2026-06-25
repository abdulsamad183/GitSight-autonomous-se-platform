import logging
import time
from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.services.ai.context_builder import ContextBuilder
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.providers.base import LLMProvider
from app.services.ai.tools.executor import ToolExecutor
from app.services.ai.tools.planner import LLMToolPlanner
from app.services.ai.tools.types import ToolExecutionContext
from app.services.ai.types import ChatStreamEvent, ChatTiming, TokenUsage

logger = logging.getLogger(__name__)


class AIEngine:
    def __init__(
        self,
        db: AsyncSession,
        planner: LLMToolPlanner,
        executor: ToolExecutor,
        context_builder: ContextBuilder,
        prompt_builder: PromptBuilder,
        llm_provider: LLMProvider,
        settings: Settings,
    ) -> None:
        self.db = db
        self.planner = planner
        self.executor = executor
        self.context_builder = context_builder
        self.prompt_builder = prompt_builder
        self.llm_provider = llm_provider
        self.settings = settings

    def _build_tool_context(
        self,
        repository_id: UUID,
        user_id: UUID,
        branch: str | None,
    ) -> ToolExecutionContext:
        return ToolExecutionContext(
            db=self.db,
            user_id=user_id,
            repository_id=repository_id,
            branch=branch,
            settings=self.settings,
        )

    async def answer_question(
        self,
        repository_id: UUID,
        user_id: UUID,
        question: str,
        *,
        branch: str | None = None,
    ) -> tuple[str, list, ChatTiming, TokenUsage | None, list[str]]:
        total_start = time.perf_counter()

        planning_start = time.perf_counter()
        plan = await self.planner.plan(question, branch)
        planning_ms = (time.perf_counter() - planning_start) * 1000

        tool_ctx = self._build_tool_context(repository_id, user_id, branch)
        tool_start = time.perf_counter()
        tool_results = await self.executor.run(plan, tool_ctx)
        tool_execution_ms = (time.perf_counter() - tool_start) * 1000

        retrieval_start = time.perf_counter()
        built = self.context_builder.build_from_tool_results(tool_results)
        retrieval_ms = (time.perf_counter() - retrieval_start) * 1000

        prompt_start = time.perf_counter()
        messages = self.prompt_builder.build_chat_prompt(built.text, question)
        prompt_build_ms = (time.perf_counter() - prompt_start) * 1000

        llm_start = time.perf_counter()
        completion = await self.llm_provider.generate(messages)
        llm_ms = (time.perf_counter() - llm_start) * 1000

        total_ms = (time.perf_counter() - total_start) * 1000
        timing = ChatTiming(
            planning_ms=round(planning_ms, 2),
            tool_execution_ms=round(tool_execution_ms, 2),
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
                "tools_used": built.tools_used,
                "plan_steps": len(plan.invocations),
                "planning_time_ms": timing.planning_ms,
                "tool_execution_time_ms": timing.tool_execution_ms,
                "retrieval_time_ms": timing.retrieval_ms,
                "prompt_build_time_ms": timing.prompt_build_ms,
                "llm_time_ms": timing.llm_ms,
                "total_time_ms": timing.total_ms,
                "stream": False,
            },
        )

        return (
            completion.content,
            built.sources,
            timing,
            completion.token_usage,
            built.tools_used,
        )

    async def stream_answer(
        self,
        repository_id: UUID,
        user_id: UUID,
        question: str,
        *,
        branch: str | None = None,
    ) -> AsyncIterator[ChatStreamEvent]:
        total_start = time.perf_counter()
        planning_ms = 0.0
        tool_execution_ms = 0.0
        retrieval_ms = 0.0
        prompt_build_ms = 0.0
        llm_ms = 0.0
        built = None
        tools_used: list[str] = []

        try:
            planning_start = time.perf_counter()
            plan = await self.planner.plan(question, branch)
            planning_ms = (time.perf_counter() - planning_start) * 1000

            tool_ctx = self._build_tool_context(repository_id, user_id, branch)

            pending_events: list[ChatStreamEvent] = []

            async def on_tool_start(tool_name: str, label: str) -> None:
                pending_events.append(
                    ChatStreamEvent(type="tool_start", tool=tool_name, label=label)
                )

            async def on_tool_end(tool_name: str, result) -> None:
                pending_events.append(
                    ChatStreamEvent(type="tool_end", tool=tool_name, success=result.success)
                )

            tool_start = time.perf_counter()
            tool_results = await self.executor.run(
                plan,
                tool_ctx,
                on_tool_start=on_tool_start,
                on_tool_end=on_tool_end,
            )
            tool_execution_ms = (time.perf_counter() - tool_start) * 1000

            for event in pending_events:
                yield event

            retrieval_start = time.perf_counter()
            built = self.context_builder.build_from_tool_results(tool_results)
            retrieval_ms = (time.perf_counter() - retrieval_start) * 1000
            tools_used = built.tools_used

            prompt_start = time.perf_counter()
            messages = self.prompt_builder.build_chat_prompt(built.text, question)
            prompt_build_ms = (time.perf_counter() - prompt_start) * 1000

            llm_start = time.perf_counter()
            async for token in self.llm_provider.stream(messages):
                yield ChatStreamEvent(type="token", content=token)
            llm_ms = (time.perf_counter() - llm_start) * 1000

            total_ms = (time.perf_counter() - total_start) * 1000
            timing = ChatTiming(
                planning_ms=round(planning_ms, 2),
                tool_execution_ms=round(tool_execution_ms, 2),
                retrieval_ms=round(retrieval_ms, 2),
                prompt_build_ms=round(prompt_build_ms, 2),
                llm_ms=round(llm_ms, 2),
                total_ms=round(total_ms, 2),
            )

            logger.info(
                "chat_completed",
                extra={
                    "repository_id": str(repository_id),
                    "chunks_used": built.chunks_used if built else 0,
                    "tools_used": tools_used,
                    "plan_steps": len(plan.invocations),
                    "planning_time_ms": timing.planning_ms,
                    "tool_execution_time_ms": timing.tool_execution_ms,
                    "retrieval_time_ms": timing.retrieval_ms,
                    "prompt_build_time_ms": timing.prompt_build_ms,
                    "llm_time_ms": timing.llm_ms,
                    "total_time_ms": timing.total_ms,
                    "stream": True,
                },
            )

            yield ChatStreamEvent(
                type="done",
                sources=built.sources if built else [],
                execution_time_ms=timing.total_ms,
                timing=timing,
                tools_used=tools_used,
            )
        except Exception as exc:
            logger.exception("chat_stream_failed for repository %s", repository_id)
            yield ChatStreamEvent(type="error", message=str(exc))
