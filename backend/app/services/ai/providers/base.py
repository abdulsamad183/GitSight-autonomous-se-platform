from collections.abc import AsyncIterator
from typing import Any, Protocol

from app.services.ai.types import ChatMessage, LLMCompletion


class LLMProvider(Protocol):
    async def generate(self, messages: list[ChatMessage]) -> LLMCompletion: ...

    def stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]: ...

    async def generate_structured(self, messages: list[ChatMessage]) -> dict[str, Any]: ...

    async def health(self) -> bool: ...
