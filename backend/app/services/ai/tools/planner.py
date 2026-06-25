import logging

from app.core.config import Settings
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.providers.base import LLMProvider
from app.services.ai.tools.registry import ToolRegistry
from app.services.ai.tools.types import ToolInvocation, ToolPlan
from app.services.exceptions import ToolPlannerError

logger = logging.getLogger(__name__)


class LLMToolPlanner:
    def __init__(
        self,
        registry: ToolRegistry,
        prompt_builder: PromptBuilder,
        llm_provider: LLMProvider,
        settings: Settings,
    ) -> None:
        self.registry = registry
        self.prompt_builder = prompt_builder
        self.llm_provider = llm_provider
        self.settings = settings

    async def plan(self, question: str, branch: str | None = None) -> ToolPlan:
        tools = self.registry.list_tools()
        messages = self.prompt_builder.build_planning_prompt(question, branch, tools)
        try:
            payload = await self.llm_provider.generate_structured(messages)
        except Exception as exc:
            raise ToolPlannerError(f"Tool planning failed: {exc}") from exc

        if not isinstance(payload, dict):
            raise ToolPlannerError("Tool planner returned invalid JSON structure")

        reasoning = str(payload.get("reasoning", ""))
        raw_steps = payload.get("steps", [])
        if not isinstance(raw_steps, list):
            raise ToolPlannerError("Tool planner 'steps' must be a list")

        invocations: list[ToolInvocation] = []
        for step in raw_steps[: self.settings.tool_max_steps]:
            if not isinstance(step, dict):
                logger.warning("Skipping non-object planner step: %s", step)
                continue
            tool_name = step.get("tool")
            arguments = step.get("arguments", {})
            if not tool_name or not isinstance(arguments, dict):
                logger.warning("Skipping invalid planner step: %s", step)
                continue
            valid, error = self.registry.validate(tool_name, arguments)
            if not valid:
                logger.warning("Dropping invalid planner step for %s: %s", tool_name, error)
                continue
            invocations.append(ToolInvocation(tool_name=tool_name, arguments=arguments))

        if raw_steps and not invocations:
            raise ToolPlannerError("All planner steps were invalid after validation")

        return ToolPlan(reasoning=reasoning, invocations=invocations)
