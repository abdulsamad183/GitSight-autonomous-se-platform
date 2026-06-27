from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from groq import AuthenticationError, RateLimitError

from app.core.config import Settings
from app.services.ai.providers.groq_provider import GroqProvider
from app.services.ai.types import ChatMessage
from app.services.exceptions import LLMProviderError


def _mock_response(status_code: int) -> httpx.Response:
    return httpx.Response(
        status_code=status_code, request=httpx.Request("POST", "https://api.groq.com")
    )


def _rate_limit_error() -> RateLimitError:
    return RateLimitError("rate limit exceeded", response=_mock_response(429), body=None)


def _auth_error() -> AuthenticationError:
    return AuthenticationError("invalid api key", response=_mock_response(401), body=None)


def _success_response(content: str = "Hello") -> MagicMock:
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=content))]
    mock_response.usage = MagicMock(prompt_tokens=1, completion_tokens=2, total_tokens=3)
    return mock_response


@pytest.mark.asyncio
async def test_groq_provider_generate():
    settings = Settings(groq_api_key="test-key", llm_model="groq/compound-mini")
    provider = GroqProvider(settings)

    mock_response = _success_response()

    with patch("app.services.ai.providers.groq_provider.AsyncGroq") as mock_cls:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        completion = await provider.generate([ChatMessage(role="user", content="hi")])

    assert completion.content == "Hello"
    assert completion.token_usage is not None
    assert completion.token_usage.total_tokens == 3


@pytest.mark.asyncio
async def test_generate_falls_back_on_rate_limit():
    settings = Settings(
        groq_api_key="test-key",
        llm_model="groq/compound-mini",
        llm_model_fallbacks=["groq/compound"],
    )
    provider = GroqProvider(settings)

    with patch("app.services.ai.providers.groq_provider.AsyncGroq") as mock_cls:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=[_rate_limit_error(), _success_response("Fallback response")]
        )
        mock_cls.return_value = mock_client

        completion = await provider.generate([ChatMessage(role="user", content="hi")])

    assert completion.content == "Fallback response"
    assert mock_client.chat.completions.create.await_count == 2
    first_call = mock_client.chat.completions.create.await_args_list[0]
    second_call = mock_client.chat.completions.create.await_args_list[1]
    assert first_call.kwargs["model"] == "groq/compound-mini"
    assert second_call.kwargs["model"] == "groq/compound"


@pytest.mark.asyncio
async def test_generate_fails_when_all_models_rate_limited():
    settings = Settings(
        groq_api_key="test-key",
        llm_model="groq/compound-mini",
        llm_model_fallbacks=["groq/compound"],
    )
    provider = GroqProvider(settings)

    with patch("app.services.ai.providers.groq_provider.AsyncGroq") as mock_cls:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=[_rate_limit_error(), _rate_limit_error()]
        )
        mock_cls.return_value = mock_client

        with pytest.raises(LLMProviderError, match="All Groq models rate-limited"):
            await provider.generate([ChatMessage(role="user", content="hi")])

    assert mock_client.chat.completions.create.await_count == 2


@pytest.mark.asyncio
async def test_generate_does_not_fallback_on_auth_error():
    settings = Settings(
        groq_api_key="test-key",
        llm_model="groq/compound-mini",
        llm_model_fallbacks=["groq/compound"],
    )
    provider = GroqProvider(settings)

    with patch("app.services.ai.providers.groq_provider.AsyncGroq") as mock_cls:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=_auth_error())
        mock_cls.return_value = mock_client

        with pytest.raises(LLMProviderError, match="Groq completion failed"):
            await provider.generate([ChatMessage(role="user", content="hi")])

    assert mock_client.chat.completions.create.await_count == 1


@pytest.mark.asyncio
async def test_groq_provider_missing_api_key():
    provider = GroqProvider(Settings(groq_api_key=None))
    with pytest.raises(LLMProviderError):
        await provider.generate([ChatMessage(role="user", content="hi")])


@pytest.mark.asyncio
async def test_groq_provider_generate_structured():
    settings = Settings(groq_api_key="test-key", llm_model="groq/compound-mini")
    provider = GroqProvider(settings)

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"reasoning":"ok","steps":[]}'))]

    with patch("app.services.ai.providers.groq_provider.AsyncGroq") as mock_cls:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        payload = await provider.generate_structured([ChatMessage(role="user", content="plan")])

    assert payload["reasoning"] == "ok"
    assert payload["steps"] == []


@pytest.mark.asyncio
async def test_generate_structured_falls_back_on_rate_limit():
    settings = Settings(
        groq_api_key="test-key",
        llm_model="groq/compound-mini",
        llm_model_fallbacks=["groq/compound"],
    )
    provider = GroqProvider(settings)

    fallback_response = MagicMock()
    fallback_response.choices = [
        MagicMock(message=MagicMock(content='{"reasoning":"fallback","steps":[]}'))
    ]

    with patch("app.services.ai.providers.groq_provider.AsyncGroq") as mock_cls:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=[_rate_limit_error(), fallback_response]
        )
        mock_cls.return_value = mock_client

        payload = await provider.generate_structured([ChatMessage(role="user", content="plan")])

    assert payload["reasoning"] == "fallback"
    assert mock_client.chat.completions.create.await_count == 2


@pytest.mark.asyncio
async def test_stream_falls_back_on_rate_limit():
    settings = Settings(
        groq_api_key="test-key",
        llm_model="groq/compound-mini",
        llm_model_fallbacks=["groq/compound"],
    )
    provider = GroqProvider(settings)

    async def fallback_stream():
        chunk = MagicMock()
        chunk.choices = [MagicMock(delta=MagicMock(content="Hi"))]
        yield chunk

    with patch("app.services.ai.providers.groq_provider.AsyncGroq") as mock_cls:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=[_rate_limit_error(), fallback_stream()]
        )
        mock_cls.return_value = mock_client

        tokens = [
            token async for token in provider.stream([ChatMessage(role="user", content="hi")])
        ]

    assert tokens == ["Hi"]
    assert mock_client.chat.completions.create.await_count == 2


@pytest.mark.asyncio
async def test_groq_provider_health_false_without_key():
    provider = GroqProvider(Settings(groq_api_key=None))
    assert await provider.health() is False
