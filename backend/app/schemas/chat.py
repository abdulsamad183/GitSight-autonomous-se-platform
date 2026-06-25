from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    branch: str | None = None
    stream: bool = False


class ChatSourceResponse(BaseModel):
    chunk_id: UUID
    file_path: str
    symbol_name: str
    chunk_type: str
    branch_name: str | None = None


class ChatTimingResponse(BaseModel):
    retrieval_ms: float
    prompt_build_ms: float
    llm_ms: float
    total_ms: float


class TokenUsageResponse(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSourceResponse] = Field(default_factory=list)
    execution_time_ms: float
    timing: ChatTimingResponse
    token_usage: TokenUsageResponse | None = None
