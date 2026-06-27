import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from groq import AsyncGroq

from app.core.config import Settings
from app.services.ai.providers.rate_limit import is_rate_limit_error
from app.services.ai.types import ChatMessage, LLMCompletion, TokenUsage
from app.services.exceptions import LLMProviderError

logger = logging.getLogger(__name__)


class GroqProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: AsyncGroq | None = None

    def _get_client(self) -> AsyncGroq:
        if not self.settings.groq_api_key:
            raise LLMProviderError("GROQ_API_KEY is not configured")
        if self._client is None:
            self._client = AsyncGroq(api_key=self.settings.groq_api_key)
        return self._client

    def _to_api_messages(self, messages: list[ChatMessage]) -> list[dict[str, str]]:
        return [{"role": message.role, "content": message.content} for message in messages]

    async def _create_completion(self, client: AsyncGroq, model: str, **kwargs: Any) -> Any:
        return await client.chat.completions.create(model=model, **kwargs)

    def _completion_from_response(self, response: Any) -> LLMCompletion:
        choice = response.choices[0] if response.choices else None
        content = choice.message.content if choice and choice.message else ""
        token_usage = None
        if response.usage is not None:
            token_usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens or 0,
                completion_tokens=response.usage.completion_tokens or 0,
                total_tokens=response.usage.total_tokens or 0,
            )
        return LLMCompletion(content=content or "", token_usage=token_usage)

    async def generate(self, messages: list[ChatMessage]) -> LLMCompletion:
        client = self._get_client()
        api_messages = self._to_api_messages(messages)
        last_rate_limit_exc: Exception | None = None

        for model in self.settings.llm_models_chain:
            try:
                response = await self._create_completion(
                    client,
                    model,
                    messages=api_messages,
                    temperature=self.settings.llm_temperature,
                    max_tokens=self.settings.llm_max_tokens,
                    stream=False,
                )
                logger.info("Groq completion succeeded with model %s", model)
                return self._completion_from_response(response)
            except Exception as exc:
                if is_rate_limit_error(exc):
                    logger.warning("Groq rate limit on %s, falling back", model)
                    last_rate_limit_exc = exc
                    continue
                logger.exception("Groq completion failed")
                raise LLMProviderError(f"Groq completion failed: {exc}") from exc

        raise LLMProviderError(
            f"All Groq models rate-limited: {last_rate_limit_exc}"
        ) from last_rate_limit_exc

    async def generate_structured(self, messages: list[ChatMessage]) -> dict:
        client = self._get_client()
        api_messages = self._to_api_messages(messages)
        last_rate_limit_exc: Exception | None = None

        for model in self.settings.planner_models_chain:
            try:
                response = await self._create_completion(
                    client,
                    model,
                    messages=api_messages,
                    temperature=self.settings.llm_planner_temperature,
                    max_tokens=self.settings.llm_planner_max_tokens,
                    response_format={"type": "json_object"},
                    stream=False,
                )
                logger.info("Groq structured planning succeeded with model %s", model)
                choice = response.choices[0] if response.choices else None
                content = choice.message.content if choice and choice.message else "{}"
                try:
                    parsed = json.loads(content or "{}")
                except json.JSONDecodeError as exc:
                    raise LLMProviderError(f"Planner returned invalid JSON: {exc}") from exc
                if not isinstance(parsed, dict):
                    raise LLMProviderError("Planner JSON root must be an object")
                return parsed
            except LLMProviderError:
                raise
            except Exception as exc:
                if is_rate_limit_error(exc):
                    logger.warning("Groq rate limit on %s, falling back", model)
                    last_rate_limit_exc = exc
                    continue
                logger.exception("Groq structured planning failed")
                raise LLMProviderError(f"Groq structured planning failed: {exc}") from exc

        raise LLMProviderError(
            f"All Groq models rate-limited: {last_rate_limit_exc}"
        ) from last_rate_limit_exc

    async def stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        client = self._get_client()
        api_messages = self._to_api_messages(messages)
        last_rate_limit_exc: Exception | None = None

        for model in self.settings.llm_models_chain:
            yielded = False
            try:
                stream = await self._create_completion(
                    client,
                    model,
                    messages=api_messages,
                    temperature=self.settings.llm_temperature,
                    max_tokens=self.settings.llm_max_tokens,
                    stream=True,
                )
                async for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yielded = True
                        yield delta.content
                logger.info("Groq stream succeeded with model %s", model)
                return
            except Exception as exc:
                if is_rate_limit_error(exc) and not yielded:
                    logger.warning("Groq rate limit on %s, falling back", model)
                    last_rate_limit_exc = exc
                    continue
                if yielded:
                    logger.exception("Groq streaming failed mid-stream on %s", model)
                else:
                    logger.exception("Groq streaming failed")
                raise LLMProviderError(f"Groq streaming failed: {exc}") from exc

        raise LLMProviderError(
            f"All Groq models rate-limited: {last_rate_limit_exc}"
        ) from last_rate_limit_exc

    async def health(self) -> bool:
        if not self.settings.groq_api_key:
            return False
        try:
            client = self._get_client()
            await client.chat.completions.create(
                model=self.settings.llm_model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
                temperature=0,
            )
            return True
        except Exception:
            logger.warning("Groq health check failed", exc_info=True)
            return False
