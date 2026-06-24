from uuid import UUID

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    chunk_id: UUID
    symbol_name: str
    file_path: str
    chunk_type: str
    content_snippet: str
    keyword_score: float | None = None
    semantic_score: float | None = None
    final_score: float | None = None
    start_line: int
    end_line: int
    branch_name: str


class SearchResponse(BaseModel):
    query: str
    mode: str
    total_results: int
    limit: int
    offset: int
    execution_time_ms: float
    results: list[SearchResult] = Field(default_factory=list)


class RetrievalContextItem(BaseModel):
    symbol_name: str
    file_path: str
    chunk_type: str
    content: str
