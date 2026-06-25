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
    source_tool: str | None = None


@dataclass
class BuiltContext:
    text: str
    sources: list[ChatSource] = field(default_factory=list)
    chunks_used: int = 0
    tools_used: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ChatTiming:
    planning_ms: float = 0.0
    tool_execution_ms: float = 0.0
    retrieval_ms: float = 0.0
    prompt_build_ms: float = 0.0
    llm_ms: float = 0.0
    total_ms: float = 0.0


@dataclass(frozen=True)
class ChatStreamEvent:
    type: Literal["token", "done", "error", "tool_start", "tool_end"]
    content: str | None = None
    sources: list[ChatSource] | None = None
    execution_time_ms: float | None = None
    timing: ChatTiming | None = None
    token_usage: TokenUsage | None = None
    message: str | None = None
    tool: str | None = None
    label: str | None = None
    success: bool | None = None
    tools_used: list[str] | None = None
