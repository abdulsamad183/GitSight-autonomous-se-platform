from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class FileCreate:
    relative_path: str
    file_name: str
    extension: str | None
    language: str | None
    size_bytes: int
    is_binary: bool


@dataclass
class SymbolCreate:
    file_id: UUID
    symbol_name: str
    symbol_type: str
    start_line: int
    end_line: int
    signature: str | None


@dataclass
class DependencyCreate:
    source_file_id: UUID
    target_file_id: UUID
    dependency_type: str


@dataclass
class SnapshotCreate:
    commit_hash: str
    branch: str
    analyzed_at: datetime
