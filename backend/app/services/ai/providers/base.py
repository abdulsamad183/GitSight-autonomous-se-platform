from collections.abc import AsyncIterator
from typing import Protocol

from app.services.ai.types import ChatMessage, LLMCompletion


class LLMProvider(Protocol):
    async def generate(self, messages: list[ChatMessage]) -> LLMCompletion: ...

    def stream(self, messages: list[ChatMessage]) -> AsyncIterator[str]: ...

    async def health(self) -> bool: ...
