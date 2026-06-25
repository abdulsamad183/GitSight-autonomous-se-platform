from typing import Any

from app.services import indexing_service, repository_detail_service
from app.services.ai.tools.types import ToolExecutionContext, ToolResult


class RepositoryMetadataTool:
    @property
    def name(self) -> str:
        return "repository"

    @property
    def description(self) -> str:
        return (
            "Answer repository metadata questions: branch count, languages, file/class counts, "
            "owner, default branch, analysis status, indexing status."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["summary", "stats", "index_status"],
                    "description": "Type of metadata to retrieve",
                },
            },
            "required": ["action"],
        }

    async def execute(self, ctx: ToolExecutionContext, arguments: dict[str, Any]) -> ToolResult:
        action = arguments.get("action", "summary")
        try:
            if action == "index_status":
                data = await indexing_service.get_index_status(
                    ctx.db,
                    repository_id=ctx.repository_id,
                    user_id=ctx.user_id,
                )
                text = _format_index_status(data)
            else:
                summary = await repository_detail_service.get_repository_summary(
                    ctx.db,
                    repository_id=ctx.repository_id,
                    user_id=ctx.user_id,
                    branch=ctx.branch,
                )
                branches = await repository_detail_service.list_repository_branches(
                    ctx.db,
                    repository_id=ctx.repository_id,
                    user_id=ctx.user_id,
                )
                data = {
                    "summary": summary.model_dump(),
                    "branches": [b.model_dump() for b in branches],
                }
                if action == "stats":
                    detail = await repository_detail_service.get_repository_detail(
                        ctx.db,
                        repository_id=ctx.repository_id,
                        user_id=ctx.user_id,
                        branch=ctx.branch,
                    )
                    languages: dict[str, int] = {}
                    for file in detail.files:
                        lang = file.language or file.extension or "unknown"
                        languages[lang] = languages.get(lang, 0) + 1
                    data["language_breakdown"] = languages
                    data["files_count"] = len(detail.files)
                    data["symbols_count"] = len(detail.symbols)
                text = _format_repository_metadata(data, action)
            return ToolResult(tool_name=self.name, success=True, text=text, data=data)
        except Exception as exc:
            return ToolResult(
                tool_name=self.name,
                success=False,
                text=f"Repository metadata lookup failed: {exc}",
                error=str(exc),
            )


def _format_index_status(data: dict) -> str:
    lines = [
        "# Repository Metadata",
        "",
        f"Indexing status: {data.get('indexing_status')}",
        f"Total chunks: {data.get('total_chunks')}",
        f"Embedded chunks: {data.get('embedded_chunks')}",
        f"Indexing started: {data.get('indexing_started_at')}",
        f"Indexing completed: {data.get('indexing_completed_at')}",
        f"Duration (seconds): {data.get('indexing_duration_seconds')}",
        f"Chunk type distribution: {data.get('chunk_type_distribution')}",
    ]
    return "\n".join(lines)


def _format_repository_metadata(data: dict, action: str) -> str:
    summary = data.get("summary", {})
    lines = [
        "# Repository Metadata",
        "",
        f"Owner: {summary.get('owner')}",
        f"Repository: {summary.get('repository_name')}",
        f"Default branch: {summary.get('default_branch')}",
        f"Status: {summary.get('status')}",
        f"Analysis status: {summary.get('analysis_status')}",
        f"Branches count: {summary.get('branches_count')}",
        f"Files count: {summary.get('files_count')}",
        f"Classes count: {summary.get('classes_count')}",
        f"Functions count: {summary.get('functions_count')}",
        f"Methods count: {summary.get('methods_count')}",
        f"Dependencies count: {summary.get('dependencies_count')}",
    ]
    if action == "stats" and "language_breakdown" in data:
        lines.append("")
        lines.append("Language breakdown:")
        for lang, count in sorted(data["language_breakdown"].items()):
            lines.append(f"- {lang}: {count}")
    branches = data.get("branches", [])
    if branches:
        lines.append("")
        lines.append("Branches:")
        for branch in branches:
            lines.append(
                f"- {branch['branch']}: {branch['files_count']} files, "
                f"{branch['classes_count']} classes"
            )
    return "\n".join(lines)
