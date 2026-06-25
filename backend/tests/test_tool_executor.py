from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.services.ai.tools.executor import ToolExecutor
from app.services.ai.tools.registry import ToolRegistry
from app.services.ai.tools.types import ToolExecutionContext, ToolInvocation, ToolPlan, ToolResult


class DummyTool:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"{self._name} tool"

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, ctx, arguments):
        return ToolResult(tool_name=self._name, success=True, text=f"output-{self._name}")


@pytest.mark.asyncio
async def test_executor_runs_tools_sequentially():
    registry = ToolRegistry()
    registry.register(DummyTool("repository"))
    registry.register(DummyTool("search"))
    executor = ToolExecutor(registry, Settings())
    ctx = ToolExecutionContext(
        db=AsyncMock(),
        user_id=uuid4(),
        repository_id=uuid4(),
        branch=None,
        settings=Settings(),
    )
    plan = ToolPlan(
        invocations=[
            ToolInvocation("repository", {}),
            ToolInvocation("search", {}),
        ]
    )
    results = await executor.run(plan, ctx)
    assert [r.tool_name for r in results] == ["repository", "search"]
    assert all(r.success for r in results)


@pytest.mark.asyncio
async def test_executor_progress_callbacks():
    registry = ToolRegistry()
    registry.register(DummyTool("graph"))
    executor = ToolExecutor(registry, Settings())
    ctx = ToolExecutionContext(
        db=AsyncMock(),
        user_id=uuid4(),
        repository_id=uuid4(),
        branch=None,
        settings=Settings(),
    )
    starts: list[str] = []
    ends: list[str] = []

    async def on_start(name, label):
        starts.append(name)

    async def on_end(name, result):
        ends.append(name)

    await executor.run(
        ToolPlan(invocations=[ToolInvocation("graph", {})]),
        ctx,
        on_tool_start=on_start,
        on_tool_end=on_end,
    )
    assert starts == ["graph"]
    assert ends == ["graph"]
