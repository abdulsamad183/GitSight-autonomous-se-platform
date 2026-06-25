from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.ai.repository_chat_service import RepositoryChatService
from app.services.ai.types import ChatSource, ChatTiming, TokenUsage
from app.services.exceptions import ValidationError


@pytest.mark.asyncio
async def test_repository_chat_service_answer():
    engine = AsyncMock()
    engine.answer_question = AsyncMock(
        return_value=(
            "JWT is validated in middleware.",
            [
                ChatSource(
                    chunk_id=uuid4(),
                    file_path="auth.py",
                    symbol_name="validate",
                    chunk_type="function",
                    source_tool="search",
                )
            ],
            ChatTiming(
                planning_ms=1,
                tool_execution_ms=2,
                retrieval_ms=3,
                prompt_build_ms=1,
                llm_ms=10,
                total_ms=17,
            ),
            TokenUsage(1, 2, 3),
            ["search"],
        )
    )

    service = RepositoryChatService(AsyncMock(), engine, MagicMock(groq_api_key="key"))
    with patch(
        "app.services.ai.repository_chat_service.repository_detail_service.get_repository_or_raise",
        new_callable=AsyncMock,
    ):
        response = await service.answer(
            repository_id=uuid4(),
            user_id=uuid4(),
            message="How does auth work?",
        )

    assert "JWT" in response.answer
    assert len(response.sources) == 1
    assert response.tools_used == ["search"]


@pytest.mark.asyncio
async def test_repository_chat_service_rejects_empty_message():
    service = RepositoryChatService(AsyncMock(), AsyncMock(), MagicMock(groq_api_key="key"))
    with patch(
        "app.services.ai.repository_chat_service.repository_detail_service.get_repository_or_raise",
        new_callable=AsyncMock,
    ):
        with pytest.raises(ValidationError):
            await service.answer(
                repository_id=uuid4(),
                user_id=uuid4(),
                message="   ",
            )
