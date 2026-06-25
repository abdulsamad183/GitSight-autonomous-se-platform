from typing import Any

from app.services.ai.tools.base import AgentTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, AgentTool] = {}

    def register(self, tool: AgentTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> AgentTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[AgentTool]:
        return list(self._tools.values())

    def validate(self, tool_name: str, arguments: dict[str, Any]) -> tuple[bool, str | None]:
        tool = self.get(tool_name)
        if tool is None:
            return False, f"Unknown tool: {tool_name}"

        required = tool.parameters.get("required", [])
        properties = tool.parameters.get("properties", {})
        for key in required:
            if key not in arguments:
                return False, f"Missing required argument '{key}' for tool '{tool_name}'"

        for key in arguments:
            if key not in properties:
                return False, f"Unknown argument '{key}' for tool '{tool_name}'"

        return True, None
