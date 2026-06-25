from typing import Any

from app.services import branch_query_service
from app.services.ai.tools.types import ToolExecutionContext, ToolResult


class BranchTool:
    @property
    def name(self) -> str:
        return "branch"

    @property
    def description(self) -> str:
        return (
            "Branch reasoning: list branches, branch statistics, summarize branch changes "
            "from indexed diffs, compare branches, find features across branches."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "list",
                        "summary",
                        "summarize_changes",
                        "compare",
                        "find_feature",
                    ],
                },
                "branch": {"type": "string"},
                "base_branch": {"type": "string"},
                "head_branch": {"type": "string"},
                "query": {"type": "string"},
            },
            "required": ["action"],
        }

    async def execute(self, ctx: ToolExecutionContext, arguments: dict[str, Any]) -> ToolResult:
        action = arguments.get("action", "list")
        try:
            if action == "list":
                data = await branch_query_service.list_branches(
                    ctx.db, repository_id=ctx.repository_id, user_id=ctx.user_id
                )
                text = _format_branch_list(data)
            elif action == "summary":
                branch = arguments.get("branch") or ctx.branch
                if not branch:
                    raise ValueError("branch is required for summary action")
                data = await branch_query_service.branch_summary(
                    ctx.db,
                    repository_id=ctx.repository_id,
                    user_id=ctx.user_id,
                    branch=branch,
                )
                text = _format_branch_summary(data)
            elif action == "summarize_changes":
                branch = arguments.get("branch") or ctx.branch
                if not branch:
                    raise ValueError("branch is required for summarize_changes action")
                data = await branch_query_service.summarize_branch_changes(
                    ctx.db, repository_id=ctx.repository_id, branch=branch
                )
                text = _format_branch_changes(data)
            elif action == "compare":
                base_branch = arguments.get("base_branch")
                head_branch = arguments.get("head_branch")
                if not base_branch or not head_branch:
                    raise ValueError("base_branch and head_branch are required for compare")
                data = await branch_query_service.compare_branches(
                    ctx.db,
                    repository_id=ctx.repository_id,
                    user_id=ctx.user_id,
                    base_branch=base_branch,
                    head_branch=head_branch,
                )
                text = _format_branch_compare(data)
            elif action == "find_feature":
                query = arguments.get("query")
                if not query:
                    raise ValueError("query is required for find_feature action")
                data = await branch_query_service.find_feature_across_branches(
                    ctx.db,
                    repository_id=ctx.repository_id,
                    user_id=ctx.user_id,
                    query=query,
                    settings=ctx.settings,
                    max_branches=ctx.settings.max_branches_to_analyze,
                )
                text = _format_find_feature(data)
            else:
                raise ValueError(f"Unknown action: {action}")

            return ToolResult(tool_name=self.name, success=True, text=text, data=data)
        except Exception as exc:
            return ToolResult(
                tool_name=self.name,
                success=False,
                text=f"Branch analysis failed: {exc}",
                error=str(exc),
            )


def _format_branch_list(data: list[dict]) -> str:
    lines = ["# Branch Analysis", "", f"Total branches: {len(data)}", ""]
    for branch in data:
        lines.append(
            f"- {branch['branch']}: {branch['files_count']} files, "
            f"{branch['classes_count']} classes, commit {branch['commit_hash'][:8]}"
        )
    return "\n".join(lines)


def _format_branch_summary(data: dict) -> str:
    if "error" in data:
        return f"# Branch Analysis\n\n{data['error']}"
    return "\n".join(
        [
            "# Branch Analysis",
            "",
            f"Branch: {data['branch']}",
            f"Commit: {data['commit_hash']}",
            f"Files: {data['files_count']}",
            f"Classes: {data['classes_count']}",
            f"Functions: {data['functions_count']}",
            f"Methods: {data['methods_count']}",
            f"Dependencies: {data['dependencies_count']}",
        ]
    )


def _format_branch_changes(data: dict) -> str:
    lines = [
        "# Branch Analysis",
        "",
        f"Branch: {data['branch']}",
        f"Total diff chunks: {data['total_diff_chunks']}",
        f"Change types: {data['change_type_counts']}",
        "",
        "Changed files:",
    ]
    for item in data.get("changed_files", [])[:30]:
        lines.append(f"- {item['file_path']} ({len(item['hunks'])} hunks)")
    return "\n".join(lines)


def _format_branch_compare(data: dict) -> str:
    lines = [
        "# Branch Analysis",
        "",
        f"Comparing {data['base_branch']} → {data['head_branch']}",
        "",
        f"Base files: {data['base_stats'].get('files_count', 'N/A')}",
        f"Head files: {data['head_stats'].get('files_count', 'N/A')}",
        f"Head diff chunks: {data['head_changes'].get('total_diff_chunks', 0)}",
    ]
    for item in data["head_changes"].get("changed_files", [])[:20]:
        lines.append(f"- changed: {item['file_path']}")
    return "\n".join(lines)


def _format_find_feature(data: dict) -> str:
    lines = ["# Branch Analysis", "", f"Feature search: {data['query']}", ""]
    for branch, hits in data.get("results_by_branch", {}).items():
        lines.append(f"Branch {branch}:")
        for hit in hits:
            if hit.get("score") is not None:
                lines.append(
                    f"  - {hit['file_path']} :: {hit['symbol_name']} (score {hit['score']:.4f})"
                )
            else:
                lines.append(f"  - {hit['file_path']} :: {hit['symbol_name']}")
        lines.append("")
    if not data.get("results_by_branch"):
        lines.append("No matches found across analyzed branches.")
    return "\n".join(lines).strip()
