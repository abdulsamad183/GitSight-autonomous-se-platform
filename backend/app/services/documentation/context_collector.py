from app.services.ai.context_builder import ContextBuilder
from app.services.ai.tools.executor import ToolExecutor
from app.services.ai.tools.types import ToolExecutionContext, ToolPlan
from app.services.ai.types import BuiltContext


class DocumentationContextCollector:
    def __init__(
        self,
        executor: ToolExecutor,
        context_builder: ContextBuilder,
    ) -> None:
        self.executor = executor
        self.context_builder = context_builder

    async def collect(
        self,
        plan: ToolPlan,
        ctx: ToolExecutionContext,
    ) -> BuiltContext:
        results = await self.executor.run(plan, ctx)
        return self.context_builder.build_from_tool_results(results)
