from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.schemas.chat import (
    ChatResponse,
    ChatSourceResponse,
    ChatTimingResponse,
    TokenUsageResponse,
)
from app.services import repository_detail_service
from app.services.ai.engine import AIEngine
from app.services.ai.types import ChatSource, ChatStreamEvent, ChatTiming, TokenUsage
from app.services.exceptions import LLMProviderError, ValidationError


def _source_to_response(source: ChatSource) -> ChatSourceResponse:
    return ChatSourceResponse(
        chunk_id=source.chunk_id,
        file_path=source.file_path,
        symbol_name=source.symbol_name,
        chunk_type=source.chunk_type,
        branch_name=source.branch_name,
        source_tool=source.source_tool,
    )


def _timing_to_response(timing: ChatTiming) -> ChatTimingResponse:
    return ChatTimingResponse(
        planning_ms=timing.planning_ms,
        tool_execution_ms=timing.tool_execution_ms,
        retrieval_ms=timing.retrieval_ms,
        prompt_build_ms=timing.prompt_build_ms,
        llm_ms=timing.llm_ms,
        total_ms=timing.total_ms,
    )


def _token_usage_to_response(usage: TokenUsage | None) -> TokenUsageResponse | None:
    if usage is None:
        return None
    return TokenUsageResponse(
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        total_tokens=usage.total_tokens,
    )


class RepositoryChatService:
    def __init__(self, db: AsyncSession, engine: AIEngine, settings: Settings) -> None:
        self.db = db
        self.engine = engine
        self.settings = settings

    async def _validate_repository(self, repository_id: UUID, user_id: UUID) -> None:
        await repository_detail_service.get_repository_or_raise(
            self.db,
            repository_id=repository_id,
            user_id=user_id,
        )

    @staticmethod
    def _validate_message(message: str) -> str:
        trimmed = message.strip()
        if not trimmed:
            raise ValidationError("Message cannot be empty")
        return trimmed

    async def _ensure_llm_ready(self) -> None:
        if not self.settings.groq_api_key:
            raise LLMProviderError("GROQ_API_KEY is not configured")

    async def answer(
        self,
        *,
        repository_id: UUID,
        user_id: UUID,
        message: str,
        branch: str | None = None,
    ) -> ChatResponse:
        await self._ensure_llm_ready()
        await self._validate_repository(repository_id, user_id)
        question = self._validate_message(message)

        answer, sources, timing, token_usage, tools_used = await self.engine.answer_question(
            repository_id,
            user_id,
            question,
            branch=branch,
        )
        return ChatResponse(
            answer=answer,
            sources=[_source_to_response(source) for source in sources],
            execution_time_ms=timing.total_ms,
            timing=_timing_to_response(timing),
            token_usage=_token_usage_to_response(token_usage),
            tools_used=tools_used,
        )

    async def stream_answer(
        self,
        *,
        repository_id: UUID,
        user_id: UUID,
        message: str,
        branch: str | None = None,
    ):
        await self._ensure_llm_ready()
        await self._validate_repository(repository_id, user_id)
        question = self._validate_message(message)

        async for event in self.engine.stream_answer(
            repository_id,
            user_id,
            question,
            branch=branch,
        ):
            yield self._stream_event_to_dict(event)

    @staticmethod
    def _stream_event_to_dict(event: ChatStreamEvent) -> dict:
        if event.type == "token":
            return {"type": "token", "content": event.content or ""}
        if event.type == "tool_start":
            return {
                "type": "tool_start",
                "tool": event.tool,
                "label": event.label,
            }
        if event.type == "tool_end":
            return {
                "type": "tool_end",
                "tool": event.tool,
                "success": event.success,
            }
        if event.type == "error":
            return {"type": "error", "message": event.message or "Unknown error"}
        return {
            "type": "done",
            "sources": [
                {
                    "chunk_id": str(source.chunk_id),
                    "file_path": source.file_path,
                    "symbol_name": source.symbol_name,
                    "chunk_type": source.chunk_type,
                    "branch_name": source.branch_name,
                    "source_tool": source.source_tool,
                }
                for source in (event.sources or [])
            ],
            "execution_time_ms": event.execution_time_ms,
            "timing": _timing_to_response(event.timing).model_dump() if event.timing else None,
            "token_usage": (
                _token_usage_to_response(event.token_usage).model_dump()
                if event.token_usage
                else None
            ),
            "tools_used": event.tools_used or [],
        }
