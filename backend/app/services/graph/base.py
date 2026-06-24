from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID

from app.models.file import File
from app.models.repository import Repository
from app.models.symbol import Symbol
from app.schemas.graph import RepositoryGraphResponse


@dataclass
class GraphBuildContext:
    repository: Repository
    branch: str | None
    files: list[File]
    symbols: list[tuple[Symbol, str]] = field(default_factory=list)


class GraphBuilder(Protocol):
    def build(self, context: GraphBuildContext) -> RepositoryGraphResponse: ...
