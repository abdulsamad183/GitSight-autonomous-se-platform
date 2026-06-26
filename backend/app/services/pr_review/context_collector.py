from app.services.ai.context_builder import ContextBuilder
from app.services.ai.tools.executor import ToolExecutor
from app.services.ai.tools.types import ToolExecutionContext
from app.services.pr_review.types import CodeReviewPlan


def merge_review_context(plan: CodeReviewPlan, tool_context_text: str) -> str:
    sections = [
        "Repository Context",
        "",
        plan.pr_metadata_text.strip(),
        "",
        plan.diff_context_text.strip(),
        "",
        tool_context_text.strip(),
    ]
    return "\n".join(sections).strip()


class PrReviewContextCollector:
    def __init__(
        self,
        executor: ToolExecutor,
        context_builder: ContextBuilder,
    ) -> None:
        self.executor = executor
        self.context_builder = context_builder

    async def collect(self, plan: CodeReviewPlan, ctx: ToolExecutionContext) -> str:
        tool_results = await self.executor.run(plan.tool_plan, ctx)
        built = self.context_builder.build_from_tool_results(tool_results)
        return merge_review_context(plan, built.text)
