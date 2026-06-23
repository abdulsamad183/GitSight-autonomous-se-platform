from uuid import UUID

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    github_url: str = Field(..., min_length=1, max_length=512)


class AnalyzeResponse(BaseModel):
    repository_id: UUID
    job_id: UUID | None = None
    status: str = "PENDING"
    cached: bool = False


class BranchSummaryResponse(BaseModel):
    branch: str
    commit_hash: str
    files_count: int
    classes_count: int
    functions_count: int
    methods_count: int
    dependencies_count: int


class RepositoryListItem(BaseModel):
    id: UUID
    owner: str
    repository_name: str
    github_url: str
    latest_commit_hash: str | None
    default_branch: str | None = None
    status: str
    analysis_status: str
    files_count: int
    branches_count: int = 0
    branches_truncated: bool = False
    updated_at: str


class RepositorySummaryResponse(BaseModel):
    id: UUID
    owner: str
    repository_name: str
    github_url: str
    latest_commit_hash: str | None
    default_branch: str | None = None
    status: str
    analysis_status: str
    files_count: int
    classes_count: int
    functions_count: int
    methods_count: int
    dependencies_count: int
    branches_count: int = 0
    branches_truncated: bool = False
    available_branches: list[str] = []


class FileItem(BaseModel):
    id: UUID
    relative_path: str
    file_name: str
    extension: str | None
    language: str | None
    size_bytes: int
    is_binary: bool


class SymbolItem(BaseModel):
    symbol_name: str
    symbol_type: str
    file_path: str
    start_line: int
    end_line: int
    signature: str | None


class DependencyItem(BaseModel):
    source_path: str
    target_path: str
    dependency_type: str


class RepositoryDetailResponse(RepositorySummaryResponse):
    selected_branch: str | None = None
    files: list[FileItem] = []
    symbols: list[SymbolItem] = []
    dependencies: list[DependencyItem] = []


class DeleteAllResponse(BaseModel):
    deleted_count: int
