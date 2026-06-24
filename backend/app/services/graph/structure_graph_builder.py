from uuid import UUID

from app.models.symbol import Symbol, SymbolType
from app.schemas.graph import GraphEdge, GraphNode, GraphStats, RepositoryGraphResponse
from app.services.graph.base import GraphBuildContext


def _repo_node_id(repository_id: UUID) -> str:
    return f"repo_{repository_id}"


def _file_node_id(file_id: UUID) -> str:
    return f"file_{file_id}"


def _class_node_id(symbol_id: UUID) -> str:
    return f"class_{symbol_id}"


def _method_node_id(symbol_id: UUID) -> str:
    return f"method_{symbol_id}"


def _find_enclosing_class(
    method: Symbol,
    classes: list[Symbol],
) -> Symbol | None:
    enclosing = [
        cls
        for cls in classes
        if cls.file_id == method.file_id
        and cls.start_line <= method.start_line
        and cls.end_line >= method.end_line
    ]
    if not enclosing:
        return None
    return min(enclosing, key=lambda cls: cls.end_line - cls.start_line)


def _resolve_method_parent(
    method: Symbol,
    classes_by_id: dict[UUID, Symbol],
    classes_by_file: dict[UUID, list[Symbol]],
) -> Symbol | None:
    if method.parent_symbol_id is not None:
        parent = classes_by_id.get(method.parent_symbol_id)
        if parent is not None:
            return parent

    file_classes = classes_by_file.get(method.file_id, [])
    return _find_enclosing_class(method, file_classes)


def _compute_empty_state(
    *,
    has_snapshot_data: bool,
    classes_count: int,
    methods_count: int,
) -> str | None:
    if not has_snapshot_data:
        return "Repository has not been analyzed yet."
    if classes_count == 0:
        return (
            "No classes found — repository may contain only scripts or unsupported languages."
        )
    if methods_count == 0:
        return "Classes found but no methods detected."
    return None


class StructureGraphBuilder:
    def build(self, context: GraphBuildContext) -> RepositoryGraphResponse:
        repository = context.repository
        files = [file for file in context.files if not file.is_binary]
        symbols_with_paths = context.symbols

        classes: list[tuple[Symbol, str]] = []
        methods: list[tuple[Symbol, str]] = []
        functions_count = 0

        for symbol, file_path in symbols_with_paths:
            if symbol.symbol_type == SymbolType.CLASS:
                classes.append((symbol, file_path))
            elif symbol.symbol_type == SymbolType.METHOD:
                methods.append((symbol, file_path))
            elif symbol.symbol_type == SymbolType.FUNCTION:
                functions_count += 1

        classes_by_id = {symbol.id: symbol for symbol, _ in classes}
        classes_by_file: dict[UUID, list[Symbol]] = {}
        for symbol, _ in classes:
            classes_by_file.setdefault(symbol.file_id, []).append(symbol)

        methods_by_class: dict[UUID, list[tuple[Symbol, str]]] = {}
        for method, file_path in methods:
            parent = _resolve_method_parent(method, classes_by_id, classes_by_file)
            if parent is None:
                continue
            methods_by_class.setdefault(parent.id, []).append((method, file_path))

        file_class_counts: dict[UUID, int] = {}
        file_method_counts: dict[UUID, int] = {}
        for symbol, _ in classes:
            file_class_counts[symbol.file_id] = file_class_counts.get(symbol.file_id, 0) + 1
        for method, _ in methods:
            file_method_counts[method.file_id] = file_method_counts.get(method.file_id, 0) + 1

        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        edge_counter = 0

        repo_id = _repo_node_id(repository.id)
        nodes.append(
            GraphNode(
                id=repo_id,
                type="repository",
                label=repository.name,
                metadata={
                    "github_url": repository.repo_url,
                    "default_branch": repository.default_branch,
                    "owner": repository.owner,
                    "repository_name": repository.repository_name,
                    "files_count": len(files),
                    "classes_count": len(classes),
                    "methods_count": len(methods),
                },
            )
        )

        for file in files:
            file_id = _file_node_id(file.id)
            nodes.append(
                GraphNode(
                    id=file_id,
                    type="file",
                    label=file.file_name,
                    metadata={
                        "path": file.relative_path,
                        "language": file.language,
                        "classes_count": file_class_counts.get(file.id, 0),
                        "methods_count": file_method_counts.get(file.id, 0),
                    },
                )
            )
            edge_counter += 1
            edges.append(
                GraphEdge(
                    id=f"edge_{edge_counter}",
                    source=repo_id,
                    target=file_id,
                )
            )

        for symbol, file_path in classes:
            class_id = _class_node_id(symbol.id)
            method_count = len(methods_by_class.get(symbol.id, []))
            nodes.append(
                GraphNode(
                    id=class_id,
                    type="class",
                    label=symbol.symbol_name,
                    metadata={
                        "file_path": file_path,
                        "method_count": method_count,
                        "start_line": symbol.start_line,
                        "end_line": symbol.end_line,
                    },
                )
            )
            edge_counter += 1
            edges.append(
                GraphEdge(
                    id=f"edge_{edge_counter}",
                    source=_file_node_id(symbol.file_id),
                    target=class_id,
                )
            )

            for method, method_file_path in methods_by_class.get(symbol.id, []):
                method_id = _method_node_id(method.id)
                nodes.append(
                    GraphNode(
                        id=method_id,
                        type="method",
                        label=method.symbol_name,
                        metadata={
                            "parent_class": symbol.symbol_name,
                            "file_path": method_file_path,
                            "start_line": method.start_line,
                            "end_line": method.end_line,
                            "signature": method.signature,
                        },
                    )
                )
                edge_counter += 1
                edges.append(
                    GraphEdge(
                        id=f"edge_{edge_counter}",
                        source=class_id,
                        target=method_id,
                    )
                )

        empty_state = _compute_empty_state(
            has_snapshot_data=bool(files or symbols_with_paths),
            classes_count=len(classes),
            methods_count=len(methods),
        )

        return RepositoryGraphResponse(
            graph_type="structure",
            branch=context.branch,
            nodes=nodes,
            edges=edges,
            stats=GraphStats(
                files_count=len(files),
                classes_count=len(classes),
                methods_count=len(methods),
                functions_count=functions_count,
            ),
            empty_state=empty_state,
        )
