import pytest

from app.core.config import Settings
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.tools.planner import LLMToolPlanner
from app.services.ai.tools.registry import ToolRegistry
from app.services.ai.tools.repository_metadata_tool import RepositoryMetadataTool
from app.services.ai.tools.search_tool import SearchTool
from app.services.exceptions import ToolPlannerError


class FakeLLM:
    def __init__(self, payload: dict):
        self.payload = payload

    async def generate(self, messages):
        raise NotImplementedError

    def stream(self, messages):
        raise NotImplementedError

    async def generate_structured(self, messages):
        return self.payload

    async def health(self):
        return True


class DummySearch:
    pass


@pytest.mark.asyncio
async def test_planner_single_tool():
    registry = ToolRegistry()
    registry.register(RepositoryMetadataTool())
    registry.register(SearchTool(DummySearch()))  # type: ignore[arg-type]
    planner = LLMToolPlanner(
        registry,
        PromptBuilder(),
        FakeLLM(
            {
                "reasoning": "count branches",
                "steps": [{"tool": "repository", "arguments": {"action": "summary"}}],
            }
        ),
        Settings(),
    )
    plan = await planner.plan("How many branches?", None)
    assert len(plan.invocations) == 1
    assert plan.invocations[0].tool_name == "repository"


@pytest.mark.asyncio
async def test_planner_multi_tool():
    registry = ToolRegistry()
    registry.register(RepositoryMetadataTool())
    registry.register(SearchTool(DummySearch()))  # type: ignore[arg-type]
    planner = LLMToolPlanner(
        registry,
        PromptBuilder(),
        FakeLLM(
            {
                "reasoning": "branch then search",
                "steps": [
                    {"tool": "repository", "arguments": {"action": "summary"}},
                    {
                        "tool": "search",
                        "arguments": {"action": "retrieve_context", "query": "OAuth"},
                    },
                ],
            }
        ),
        Settings(),
    )
    plan = await planner.plan("Which branch contains OAuth?", "main")
    assert len(plan.invocations) == 2


@pytest.mark.asyncio
async def test_planner_empty_plan_allowed():
    registry = ToolRegistry()
    registry.register(RepositoryMetadataTool())
    planner = LLMToolPlanner(
        registry,
        PromptBuilder(),
        FakeLLM({"reasoning": "none", "steps": []}),
        Settings(),
    )
    plan = await planner.plan("Hello", None)
    assert plan.invocations == []


@pytest.mark.asyncio
async def test_planner_invalid_steps_raises():
    registry = ToolRegistry()
    registry.register(RepositoryMetadataTool())
    planner = LLMToolPlanner(
        registry,
        PromptBuilder(),
        FakeLLM(
            {
                "reasoning": "bad",
                "steps": [{"tool": "unknown_tool", "arguments": {}}],
            }
        ),
        Settings(),
    )
    with pytest.raises(ToolPlannerError):
        await planner.plan("stats", None)
