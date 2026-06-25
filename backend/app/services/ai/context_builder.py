from uuid import UUID

from app.core.config import Settings
from app.services.ai.tools.types import ToolResult
from app.services.ai.types import BuiltContext, ChatSource

SECTION_ORDER = {
    "repository": 0,
    "branch": 1,
    "graph": 2,
    "search": 3,
}


class ContextBuilder:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_from_tool_results(self, tool_results: list[ToolResult]) -> BuiltContext:
        if not tool_results:
            return BuiltContext(
                text="Repository Context\n\n(No tool outputs available.)",
                sources=[],
                chunks_used=0,
                tools_used=[],
            )

        ordered = sorted(
            [result for result in tool_results if result.text.strip()],
            key=lambda result: SECTION_ORDER.get(result.tool_name, 99),
        )

        included: list[ToolResult] = []
        for result in ordered:
            trial = included + [result]
            text = self._render_sections(trial)
            if len(text) <= self.settings.rag_max_context_chars:
                included.append(result)
            else:
                break

        if not included and ordered:
            included = [ordered[0]]

        sources: list[ChatSource] = []
        seen_chunk_ids: set[UUID] = set()
        chunks_used = 0
        tools_used: list[str] = []
        for result in included:
            tools_used.append(result.tool_name)
            for source in result.sources:
                if source.chunk_id in seen_chunk_ids:
                    continue
                seen_chunk_ids.add(source.chunk_id)
                sources.append(source)
                chunks_used += 1

        return BuiltContext(
            text=self._render_sections(included),
            sources=sources,
            chunks_used=chunks_used,
            tools_used=tools_used,
        )

    def _render_sections(self, results: list[ToolResult]) -> str:
        if not results:
            return "Repository Context\n\n(No tool outputs available.)"
        sections = ["Repository Context", ""]
        for result in results:
            sections.append(result.text.strip())
            sections.append("")
        return "\n".join(sections).strip()
