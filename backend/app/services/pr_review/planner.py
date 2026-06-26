from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.code_chunk import ChunkType
from app.models.pull_request import PullRequest
from app.repositories import code_chunk_repository
from app.services import branch_query_service
from app.services.ai.tools.types import ToolInvocation, ToolPlan
from app.services.pr_review.types import CodeReviewPlan


def _format_pr_metadata(pull_request: PullRequest) -> str:
    lines = [
        "# Pull Request Metadata",
        "",
        f"Number: #{pull_request.number}",
        f"Title: {pull_request.title}",
        f"Author: {pull_request.author_username}",
        f"State: {pull_request.state.value}",
        f"Source branch: {pull_request.source_branch or 'unknown'}",
        f"Target branch: {pull_request.target_branch or 'unknown'}",
        f"Draft: {pull_request.is_draft}",
        f"Merged: {pull_request.is_merged}",
        "",
    ]
    if pull_request.description and pull_request.description.strip():
        lines.extend(["Description:", pull_request.description.strip(), ""])
    return "\n".join(lines)


async def _build_diff_context_text(
    db: AsyncSession,
    *,
    repository_id: UUID,
    source_branch: str | None,
    settings: Settings,
) -> tuple[str, list[str]]:
    if not source_branch:
        return "# Pull Request Changes\n\n(No source branch available.)", []

    changes = await branch_query_service.summarize_branch_changes(
        db,
        repository_id=repository_id,
        branch=source_branch,
        limit=settings.pr_review_max_diff_chunks,
    )
    changed_files = changes.get("changed_files", [])
    if not changed_files:
        return "# Pull Request Changes\n\n(No indexed diff chunks for source branch.)", []

    chunks, _ = await code_chunk_repository.list_by_repository(
        db,
        repository_id=repository_id,
        branch_name=source_branch,
        chunk_type=ChunkType.DIFF_HUNK,
        limit=settings.pr_review_max_diff_chunks,
    )

    lines = [
        "# Pull Request Changes",
        "",
        f"Branch: {source_branch}",
        f"Total diff chunks: {changes.get('total_diff_chunks', 0)}",
        f"Change types: {changes.get('change_type_counts', {})}",
        "",
        "Changed files:",
    ]
    file_paths: list[str] = []
    for item in changed_files[: settings.pr_review_max_graph_files * 2]:
        file_paths.append(item["file_path"])
        lines.append(f"- {item['file_path']} ({len(item.get('hunks', []))} hunks)")

    lines.append("")
    lines.append("Diff hunks:")
    budget = settings.rag_max_context_chars // 2
    used = len("\n".join(lines))
    for chunk in chunks:
        block = (
            f"\nFile: {chunk.file_path}\n"
            f"Symbol: {chunk.symbol_name}\n"
            f"Lines: {chunk.start_line}-{chunk.end_line}\n"
            f"Change: {chunk.change_type.value if chunk.change_type else 'unknown'}\n"
            f"```\n{chunk.content.strip()}\n```"
        )
        if used + len(block) > budget:
            lines.append("\n(Diff content truncated due to context limit.)")
            break
        lines.append(block)
        used += len(block)

    return "\n".join(lines).strip(), file_paths


def _build_search_query(changed_files: list[str], changes: dict) -> str:
    symbols: list[str] = []
    for item in changes.get("changed_files", [])[:5]:
        for hunk in item.get("hunks", [])[:3]:
            name = hunk.get("symbol_name")
            if name:
                symbols.append(name)
    parts = symbols[:5] + [path.rsplit("/", 1)[-1] for path in changed_files[:3]]
    return " ".join(dict.fromkeys(parts)) or "pull request changed code implementation"


def _build_tool_plan(
    pull_request: PullRequest,
    changed_files: list[str],
    changes: dict,
    settings: Settings,
) -> ToolPlan:
    source = pull_request.source_branch
    target = pull_request.target_branch
    branch_arg = {"branch": source} if source else {}
    invocations: list[ToolInvocation] = [
        ToolInvocation("repository", {"action": "summary"}),
    ]

    if source and target:
        invocations.append(
            ToolInvocation(
                "branch",
                {
                    "action": "compare",
                    "base_branch": target,
                    "head_branch": source,
                },
            )
        )

    if source:
        invocations.append(
            ToolInvocation("branch", {"action": "summarize_changes", "branch": source})
        )
        invocations.append(ToolInvocation("graph", {"action": "structure", **branch_arg}))

    for file_path in changed_files[: settings.pr_review_max_graph_files]:
        invocations.append(
            ToolInvocation("graph", {"action": "dependents", "file_path": file_path, **branch_arg})
        )
        invocations.append(
            ToolInvocation(
                "graph",
                {"action": "dependencies", "file_path": file_path, **branch_arg},
            )
        )

    if changed_files or changes.get("changed_files"):
        invocations.append(
            ToolInvocation(
                "search",
                {
                    "action": "retrieve_context",
                    "query": _build_search_query(changed_files, changes),
                    **branch_arg,
                },
            )
        )

    return ToolPlan(invocations=invocations[: settings.pr_review_max_tool_steps])


class CodeReviewPlanner:
    async def plan(
        self,
        db: AsyncSession,
        *,
        repository_id: UUID,
        pull_request: PullRequest,
        settings: Settings,
    ) -> CodeReviewPlan:
        pr_metadata_text = _format_pr_metadata(pull_request)
        diff_context_text, changed_files = await _build_diff_context_text(
            db,
            repository_id=repository_id,
            source_branch=pull_request.source_branch,
            settings=settings,
        )
        changes = {}
        if pull_request.source_branch:
            changes = await branch_query_service.summarize_branch_changes(
                db,
                repository_id=repository_id,
                branch=pull_request.source_branch,
            )
        tool_plan = _build_tool_plan(pull_request, changed_files, changes, settings)
        title = f"PR #{pull_request.number}: {pull_request.title}"

        return CodeReviewPlan(
            pull_request_id=pull_request.id,
            title=title,
            pr_metadata_text=pr_metadata_text,
            diff_context_text=diff_context_text,
            tool_plan=tool_plan,
            source_branch=pull_request.source_branch,
        )
