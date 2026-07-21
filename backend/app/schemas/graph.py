from typing import Any, Literal

from pydantic import BaseModel, Field

GraphNodeType = Literal["repository", "file", "class", "method"]


class GraphNode(BaseModel):
    id: str
    type: GraphNodeType
    label: str
    metadata: dict[str, Any]


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str


class GraphStats(BaseModel):
    files_count: int
    classes_count: int
    methods_count: int
    functions_count: int = 0


class RepositoryGraphResponse(BaseModel):
    graph_type: str = "structure"
    branch: str | None = None
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    stats: GraphStats
    empty_state: str | None = None


class BlastRadiusNode(BaseModel):
    file_path: str
    hop: int


class BlastRadiusResponse(BaseModel):
    file_path: str
    direction: str
    max_depth: int
    branch: str | None = None
    nodes: list[BlastRadiusNode] = Field(default_factory=list)
    total: int = 0
    message: str | None = None
    suggested_direction: str | None = None


class GraphPathResponse(BaseModel):
    source_file: str
    target_file: str
    max_depth: int
    branch: str | None = None
    paths: list[list[str]] = Field(default_factory=list)
    total_paths: int = 0
    bidirectional: bool = False
    message: str | None = None


class ImportEdgeItem(BaseModel):
    source_path: str
    target_path: str
    dependency_type: str


class ImportGraphSummaryResponse(BaseModel):
    branch: str | None = None
    edges: list[ImportEdgeItem] = Field(default_factory=list)
    connected_files: list[str] = Field(default_factory=list)
    source_files: list[str] = Field(default_factory=list)
    target_files: list[str] = Field(default_factory=list)
    total_edges: int = 0
