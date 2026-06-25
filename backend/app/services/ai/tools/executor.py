import logging
from collections.abc import Awaitable, Callable

from app.core.config import Settings
from app.services.ai.tools.registry import ToolRegistry
from app.services.ai.tools.types import ToolExecutionContext, ToolPlan, ToolResult

logger = logging.getLogger(__name__)

TOOL_LABELS = {
    "repository": "Inspecting repository…",
    "search": "Searching code…",
    "branch": "Checking branches…",
    "graph": "Analyzing dependency graph…",
}


class ToolExecutor:
    def __init__(self, registry: ToolRegistry, settings: Settings) -> None:
        self.registry = registry
        self.settings = settings

    def label_for(self, tool_name: str) -> str:
        return TOOL_LABELS.get(tool_name, f"Running {tool_name}…")

    async def run(
        self,
        plan: ToolPlan,
        ctx: ToolExecutionContext,
        *,
        on_tool_start: Callable[[str, str], Awaitable[None]] | None = None,
        on_tool_end: Callable[[str, ToolResult], Awaitable[None]] | None = None,
    ) -> list[ToolResult]:
        results: list[ToolResult] = []
        for invocation in plan.invocations:
            label = self.label_for(invocation.tool_name)
            if on_tool_start:
                await on_tool_start(invocation.tool_name, label)

            tool = self.registry.get(invocation.tool_name)
            if tool is None:
                result = ToolResult(
                    tool_name=invocation.tool_name,
                    success=False,
                    text=f"Unknown tool: {invocation.tool_name}",
                    error=f"Unknown tool: {invocation.tool_name}",
                )
            else:
                valid, error = self.registry.validate(invocation.tool_name, invocation.arguments)
                if not valid:
                    result = ToolResult(
                        tool_name=invocation.tool_name,
                        success=False,
                        text=f"Invalid arguments: {error}",
                        error=error,
                    )
                else:
                    try:
                        result = await tool.execute(ctx, invocation.arguments)
                    except Exception as exc:
                        logger.exception("Tool %s failed", invocation.tool_name)
                        result = ToolResult(
                            tool_name=invocation.tool_name,
                            success=False,
                            text=f"Tool execution failed: {exc}",
                            error=str(exc),
                        )

            results.append(result)
            if on_tool_end:
                await on_tool_end(invocation.tool_name, result)

        return results
