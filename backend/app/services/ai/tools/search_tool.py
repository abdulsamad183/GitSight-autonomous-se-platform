from typing import Any

from app.services.ai.tools.types import ToolExecutionContext, ToolResult
from app.services.ai.types import ChatSource
from app.services.search_service import SearchService


class SearchTool:
    def __init__(self, search_service: SearchService) -> None:
        self.search_service = search_service

    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return (
            "Hybrid code search over repository chunks. Use for explaining implementations, "
            "finding symbols, locating auth/JWT/retry logic, and retrieving code context."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["search", "retrieve_context"],
                    "description": (
                        "search returns ranked hits; retrieve_context returns full chunk content"
                    ),
                },
                "query": {
                    "type": "string",
                    "description": "Search query text",
                },
                "branch": {
                    "type": "string",
                    "description": "Optional branch to scope search",
                },
            },
            "required": ["action", "query"],
        }

    async def execute(self, ctx: ToolExecutionContext, arguments: dict[str, Any]) -> ToolResult:
        action = arguments.get("action", "retrieve_context")
        query = arguments.get("query", "")
        branch = arguments.get("branch") or ctx.branch

        try:
            sources: list[ChatSource] = []
            if action == "search":
                response = await self.search_service.search(
                    ctx.repository_id,
                    query,
                    mode="hybrid",
                    limit=ctx.settings.rag_top_k,
                    branch=branch,
                )
                lines = ["# Retrieved Code", "", f"Query: {query}", ""]
                for result in response.results:
                    lines.append(f"File: {result.file_path}")
                    lines.append(f"Symbol: {result.symbol_name}")
                    lines.append(f"Type: {result.chunk_type}")
                    score = result.final_score
                    score_text = f"{score:.4f}" if score is not None else "N/A"
                    lines.append(f"Score: {score_text}")
                    lines.append(f"Snippet: {result.content_snippet}")
                    lines.append("")
                    sources.append(
                        ChatSource(
                            chunk_id=result.chunk_id,
                            file_path=result.file_path,
                            symbol_name=result.symbol_name.replace("<mark>", "").replace(
                                "</mark>", ""
                            ),
                            chunk_type=result.chunk_type,
                            branch_name=result.branch_name,
                            source_tool=self.name,
                        )
                    )
                data = {"results": [r.model_dump() for r in response.results]}
            else:
                items = await self.search_service.retrieve_context(
                    ctx.repository_id,
                    query,
                    top_k=ctx.settings.rag_top_k,
                    branch=branch,
                )
                lines = ["# Retrieved Code", "", f"Query: {query}", ""]
                for item in items:
                    clean_symbol = item.symbol_name.replace("<mark>", "").replace("</mark>", "")
                    lines.append(f"File: {item.file_path}")
                    lines.append(f"Symbol: {clean_symbol}")
                    lines.append(f"Type: {item.chunk_type}")
                    if item.branch_name:
                        lines.append(f"Branch: {item.branch_name}")
                    lines.append("Code:")
                    lines.append(item.content)
                    lines.append("")
                    sources.append(
                        ChatSource(
                            chunk_id=item.chunk_id,
                            file_path=item.file_path,
                            symbol_name=clean_symbol,
                            chunk_type=item.chunk_type,
                            branch_name=item.branch_name,
                            source_tool=self.name,
                        )
                    )
                data = {"chunks": len(items)}
            return ToolResult(
                tool_name=self.name,
                success=True,
                text="\n".join(lines).strip(),
                data=data,
                sources=sources,
            )
        except Exception as exc:
            return ToolResult(
                tool_name=self.name,
                success=False,
                text=f"Search failed: {exc}",
                error=str(exc),
            )
