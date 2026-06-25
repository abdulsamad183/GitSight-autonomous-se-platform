from typing import Any

from app.services.ai.tools.types import ToolExecutionContext, ToolResult
from app.services.graph import graph_query_service


class GraphTool:
    @property
    def name(self) -> str:
        return "graph"

    @property
    def description(self) -> str:
        return (
            "Repository relationship reasoning: structure hierarchy, import dependencies, "
            "symbol lookup, dependents, dependencies, and dependency path tracing."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "structure",
                        "find_symbol",
                        "dependents",
                        "dependencies",
                        "trace_path",
                    ],
                },
                "symbol_name": {"type": "string"},
                "file_path": {"type": "string"},
                "source_file": {"type": "string"},
                "target_file": {"type": "string"},
                "branch": {"type": "string"},
            },
            "required": ["action"],
        }

    async def execute(self, ctx: ToolExecutionContext, arguments: dict[str, Any]) -> ToolResult:
        action = arguments.get("action", "structure")
        branch = arguments.get("branch") or ctx.branch
        try:
            if action == "structure":
                graph = await graph_query_service.get_structure_graph(
                    ctx.db,
                    repository_id=ctx.repository_id,
                    user_id=ctx.user_id,
                    branch=branch,
                )
                data = graph.model_dump()
                text = _format_structure(graph)
            elif action == "find_symbol":
                symbol_name = arguments.get("symbol_name")
                if not symbol_name:
                    raise ValueError("symbol_name is required for find_symbol")
                matches = await graph_query_service.find_symbol(
                    ctx.db,
                    repository_id=ctx.repository_id,
                    user_id=ctx.user_id,
                    symbol_name=symbol_name,
                    branch=branch,
                )
                data = {"matches": matches}
                text = _format_symbol_matches(symbol_name, matches)
            elif action == "dependents":
                file_path = arguments.get("file_path")
                if not file_path:
                    raise ValueError("file_path is required for dependents")
                deps = await graph_query_service.dependents(
                    ctx.db,
                    repository_id=ctx.repository_id,
                    user_id=ctx.user_id,
                    file_path=file_path,
                    branch=branch,
                )
                data = {"file_path": file_path, "dependents": deps}
                text = _format_file_list(
                    "# Dependency Graph", f"Files that depend on {file_path}", deps
                )
            elif action == "dependencies":
                file_path = arguments.get("file_path")
                if not file_path:
                    raise ValueError("file_path is required for dependencies")
                deps = await graph_query_service.dependencies(
                    ctx.db,
                    repository_id=ctx.repository_id,
                    user_id=ctx.user_id,
                    file_path=file_path,
                    branch=branch,
                )
                data = {"file_path": file_path, "dependencies": deps}
                text = _format_file_list(
                    "# Dependency Graph", f"Files imported by {file_path}", deps
                )
            elif action == "trace_path":
                source_file = arguments.get("source_file")
                target_file = arguments.get("target_file")
                if not source_file or not target_file:
                    raise ValueError("source_file and target_file are required for trace_path")
                paths = await graph_query_service.trace_path(
                    ctx.db,
                    repository_id=ctx.repository_id,
                    user_id=ctx.user_id,
                    source_file=source_file,
                    target_file=target_file,
                    branch=branch,
                    max_depth=ctx.settings.graph_traversal_max_depth,
                )
                data = {"paths": paths}
                text = _format_paths(source_file, target_file, paths)
            else:
                raise ValueError(f"Unknown action: {action}")

            return ToolResult(tool_name=self.name, success=True, text=text, data=data)
        except Exception as exc:
            return ToolResult(
                tool_name=self.name,
                success=False,
                text=f"Graph analysis failed: {exc}",
                error=str(exc),
            )


def _format_structure(graph) -> str:
    lines = [
        "# Dependency Graph",
        "",
        f"Graph type: {graph.graph_type}",
        f"Branch: {graph.branch}",
        f"Files: {graph.stats.files_count}",
        f"Classes: {graph.stats.classes_count}",
        f"Methods: {graph.stats.methods_count}",
        "",
        "Structure sample (files and classes):",
    ]
    file_nodes = [n for n in graph.nodes if n.type == "file"][:20]
    for node in file_nodes:
        lines.append(f"- {node.label}")
    return "\n".join(lines)


def _format_symbol_matches(symbol_name: str, matches: list[dict]) -> str:
    lines = ["# Dependency Graph", "", f"Symbol matches for '{symbol_name}':", ""]
    if not matches:
        lines.append("No symbols found.")
        return "\n".join(lines)
    for match in matches:
        lines.append(
            f"- {match['symbol_name']} ({match['symbol_type']}) in {match['file_path']}"
            f" lines {match['start_line']}-{match['end_line']}"
        )
    return "\n".join(lines)


def _format_file_list(header: str, title: str, files: list[str]) -> str:
    lines = [header, "", title, ""]
    if not files:
        lines.append("None found.")
    else:
        for path in files:
            lines.append(f"- {path}")
    return "\n".join(lines)


def _format_paths(source: str, target: str, paths: list[list[str]]) -> str:
    lines = ["# Dependency Graph", "", f"Paths from {source} to {target}:", ""]
    if not paths:
        lines.append("No import paths found within depth limit.")
    else:
        for index, path in enumerate(paths, start=1):
            lines.append(f"{index}. {' -> '.join(path)}")
    return "\n".join(lines)
