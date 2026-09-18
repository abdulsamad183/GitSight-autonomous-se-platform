from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AdminStatsResponse(BaseModel):
    total_users: int
    total_repositories: int
    repos_by_status: dict[str, int]
    repos_by_indexing_status: dict[str, int]
    signups_last_7_days: int
    repos_added_last_7_days: int


class AdminUserListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: str
    role: str
    created_at: datetime
    repository_count: int


class AdminUserListResponse(BaseModel):
    items: list[AdminUserListItem]
    total: int
    page: int
    limit: int


class AdminRepositoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    repo_url: str
    status: str
    indexing_status: str
    created_at: datetime
    updated_at: datetime


class AdminUserDetailResponse(BaseModel):
    id: UUID
    username: str
    email: str
    role: str
    created_at: datetime
    repositories: list[AdminRepositoryItem] = Field(default_factory=list)
