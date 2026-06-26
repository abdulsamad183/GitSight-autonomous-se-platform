from dataclasses import dataclass
from uuid import UUID

from app.services.ai.tools.types import ToolPlan


@dataclass(frozen=True)
class CodeReviewPlan:
    pull_request_id: UUID
    title: str
    pr_metadata_text: str
    diff_context_text: str
    tool_plan: ToolPlan
    source_branch: str | None = None
