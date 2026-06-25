from uuid import UUID

from app.core.config import Settings
from app.schemas.search import RetrievalContextItem
from app.services.ai.types import BuiltContext, ChatSource
from app.services.search_service import SearchService


def _format_chunk_block(item: RetrievalContextItem) -> str:
    clean_symbol = item.symbol_name.replace("<mark>", "").replace("</mark>", "")
    lines = [
        f"File: {item.file_path}",
        f"Symbol: {clean_symbol}",
        f"Type: {item.chunk_type}",
    ]
    if item.branch_name:
        lines.append(f"Branch: {item.branch_name}")
    if item.change_type:
        lines.append(f"Change: {item.change_type}")
    lines.append("Code:")
    lines.append(item.content)
    return "\n".join(lines)


def _group_by_file(items: list[RetrievalContextItem]) -> dict[str, list[RetrievalContextItem]]:
    grouped: dict[str, list[RetrievalContextItem]] = {}
    file_order: list[str] = []
    for item in items:
        if item.file_path not in grouped:
            grouped[item.file_path] = []
            file_order.append(item.file_path)
        grouped[item.file_path].append(item)
    return {path: grouped[path] for path in file_order}


class ContextBuilder:
    def __init__(self, search_service: SearchService, settings: Settings) -> None:
        self.search_service = search_service
        self.settings = settings

    async def build(
        self,
        *,
        repository_id: UUID,
        user_query: str,
        branch: str | None = None,
    ) -> BuiltContext:
        items = await self.search_service.retrieve_context(
            repository_id,
            user_query,
            top_k=self.settings.rag_top_k,
            branch=branch,
        )
        if not items:
            return BuiltContext(
                text="Repository Context\n\n(No relevant code chunks found.)",
                sources=[],
                chunks_used=0,
            )

        included: list[RetrievalContextItem] = []
        for item in items:
            trial = included + [item]
            text = self._render_context(trial)
            if len(text) <= self.settings.rag_max_context_chars:
                included.append(item)
            else:
                break

        if not included and items:
            included = [items[0]]

        sources = [
            ChatSource(
                chunk_id=item.chunk_id,
                file_path=item.file_path,
                symbol_name=item.symbol_name.replace("<mark>", "").replace("</mark>", ""),
                chunk_type=item.chunk_type,
                branch_name=item.branch_name,
            )
            for item in included
        ]
        return BuiltContext(
            text=self._render_context(included),
            sources=sources,
            chunks_used=len(included),
        )

    def _render_context(self, items: list[RetrievalContextItem]) -> str:
        if not items:
            return "Repository Context\n\n(No relevant code chunks found.)"

        grouped = _group_by_file(items)
        sections: list[str] = ["Repository Context", ""]
        for file_path, file_items in grouped.items():
            sections.append(f"## File: {file_path}")
            sections.append("")
            for item in file_items:
                sections.append(_format_chunk_block(item))
                sections.append("")
        return "\n".join(sections).strip()
