from typing import Any, Protocol

from app.services.ai.tools.types import ToolExecutionContext, ToolResult


class AgentTool(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def parameters(self) -> dict[str, Any]: ...

    async def execute(self, ctx: ToolExecutionContext, arguments: dict[str, Any]) -> ToolResult: ...
