from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


@dataclass
class ChunkCreate:
    repository_id: UUID
    branch_name: str
    file_path: str
    chunk_type: str
    symbol_name: str
    parent_symbol: str | None
    start_line: int
    end_line: int
    content: str
    content_hash: str
    chunk_source: str = "symbol"
    base_commit_hash: str | None = None
    head_commit_hash: str | None = None
    change_type: str | None = None


class ChunkResponse(BaseModel):
    id: UUID
    repository_id: UUID
    branch_name: str
    file_path: str
    chunk_type: str
    symbol_name: str
    parent_symbol: str | None
    start_line: int
    end_line: int
    content: str
    content_hash: str
    chunk_source: str
    base_commit_hash: str | None
    head_commit_hash: str | None
    change_type: str | None
    created_at: datetime
    updated_at: datetime


class ChunkListResponse(BaseModel):
    items: list[ChunkResponse]
    total: int
    limit: int
    offset: int


class IndexStatusResponse(BaseModel):
    repository_id: UUID
    indexing_status: str
    total_chunks: int
    embedded_chunks: int
    indexing_started_at: datetime | None
    indexing_completed_at: datetime | None
    indexing_duration_seconds: float | None
    chunk_type_distribution: dict[str, int] = Field(default_factory=dict)


class ReindexResponse(BaseModel):
    repository_id: UUID
    job_id: UUID
    status: str = "PENDING"
