from dataclasses import dataclass, field
from typing import Literal
from uuid import UUID


@dataclass(frozen=True)
class ChatMessage:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class LLMCompletion:
    content: str
    token_usage: TokenUsage | None = None


@dataclass(frozen=True)
class ChatSource:
    chunk_id: UUID
    file_path: str
    symbol_name: str
    chunk_type: str
    branch_name: str | None = None


@dataclass
class BuiltContext:
    text: str
    sources: list[ChatSource] = field(default_factory=list)
    chunks_used: int = 0


@dataclass(frozen=True)
class ChatTiming:
    retrieval_ms: float
    prompt_build_ms: float
    llm_ms: float
    total_ms: float


@dataclass(frozen=True)
class ChatStreamEvent:
    type: Literal["token", "done", "error"]
    content: str | None = None
    sources: list[ChatSource] | None = None
    execution_time_ms: float | None = None
    timing: ChatTiming | None = None
    token_usage: TokenUsage | None = None
    message: str | None = None
