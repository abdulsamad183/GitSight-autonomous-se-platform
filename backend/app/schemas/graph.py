from typing import Any, Literal

from pydantic import BaseModel

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
