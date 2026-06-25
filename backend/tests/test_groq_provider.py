from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.services.ai.providers.groq_provider import GroqProvider
from app.services.ai.types import ChatMessage
from app.services.exceptions import LLMProviderError


@pytest.mark.asyncio
async def test_groq_provider_generate():
    settings = Settings(groq_api_key="test-key", llm_model="groq/compound-mini")
    provider = GroqProvider(settings)

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Hello"))]
    mock_response.usage = MagicMock(prompt_tokens=1, completion_tokens=2, total_tokens=3)

    with patch("app.services.ai.providers.groq_provider.AsyncGroq") as mock_cls:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        completion = await provider.generate([ChatMessage(role="user", content="hi")])

    assert completion.content == "Hello"
    assert completion.token_usage is not None
    assert completion.token_usage.total_tokens == 3


@pytest.mark.asyncio
async def test_groq_provider_missing_api_key():
    provider = GroqProvider(Settings(groq_api_key=None))
    with pytest.raises(LLMProviderError):
        await provider.generate([ChatMessage(role="user", content="hi")])


@pytest.mark.asyncio
async def test_groq_provider_health_false_without_key():
    provider = GroqProvider(Settings(groq_api_key=None))
    assert await provider.health() is False
