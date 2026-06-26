from dataclasses import dataclass

from app.models.repository_document import DOCUMENT_TYPE_TITLES, DocumentType
from app.services.ai.tools.types import ToolInvocation, ToolPlan
from app.services.documentation.discovery import DiscoveredDocument, ExistingDocumentationDiscovery


@dataclass(frozen=True)
class DocumentationPlan:
    document_type: DocumentType
    title: str
    requires_ai: bool
    existing_document: DiscoveredDocument | None = None
    tool_plan: ToolPlan | None = None


def _tool_plan_for_type(document_type: DocumentType, branch: str | None) -> ToolPlan:
    branch_arg = {"branch": branch} if branch else {}

    if document_type == DocumentType.REPOSITORY_OVERVIEW:
        return ToolPlan(
            invocations=[
                ToolInvocation("repository", {"action": "summary"}),
                ToolInvocation("repository", {"action": "stats"}),
            ]
        )

    if document_type == DocumentType.ARCHITECTURE_OVERVIEW:
        invocations = [
            ToolInvocation("repository", {"action": "stats"}),
            ToolInvocation("graph", {"action": "structure", **branch_arg}),
        ]
        return ToolPlan(invocations=invocations)

    if document_type == DocumentType.MODULES:
        return ToolPlan(
            invocations=[
                ToolInvocation("graph", {"action": "structure", **branch_arg}),
                ToolInvocation(
                    "search",
                    {
                        "action": "retrieve_context",
                        "query": "module package structure organization",
                        **branch_arg,
                    },
                ),
            ]
        )

    if document_type == DocumentType.CLASSES:
        return ToolPlan(
            invocations=[
                ToolInvocation("graph", {"action": "structure", **branch_arg}),
                ToolInvocation(
                    "search",
                    {
                        "action": "retrieve_context",
                        "query": "class definitions interfaces types",
                        **branch_arg,
                    },
                ),
            ]
        )

    if document_type == DocumentType.FUNCTIONS:
        return ToolPlan(
            invocations=[
                ToolInvocation(
                    "search",
                    {
                        "action": "retrieve_context",
                        "query": "public functions methods entry points API",
                        **branch_arg,
                    },
                ),
                ToolInvocation("repository", {"action": "stats"}),
            ]
        )

    if document_type == DocumentType.BRANCH_SUMMARY:
        invocations = [ToolInvocation("branch", {"action": "list"})]
        if branch:
            invocations.append(ToolInvocation("branch", {"action": "summary", "branch": branch}))
            invocations.append(
                ToolInvocation("branch", {"action": "summarize_changes", "branch": branch})
            )
        return ToolPlan(invocations=invocations)

    return ToolPlan(invocations=[])


class DocumentationPlanner:
    def __init__(self, discovery: ExistingDocumentationDiscovery | None = None) -> None:
        self.discovery = discovery or ExistingDocumentationDiscovery()

    async def plan(
        self,
        db,
        *,
        repository_id,
        document_type: DocumentType,
        branch: str,
        skip_discovery: bool = False,
    ) -> DocumentationPlan:
        title = DOCUMENT_TYPE_TITLES[document_type]

        if not skip_discovery:
            existing = await self.discovery.find(
                db,
                repository_id=repository_id,
                document_type=document_type,
                branch=branch,
            )
            if existing is not None:
                return DocumentationPlan(
                    document_type=document_type,
                    title=existing.title or title,
                    requires_ai=False,
                    existing_document=existing,
                )

        return DocumentationPlan(
            document_type=document_type,
            title=title,
            requires_ai=True,
            tool_plan=_tool_plan_for_type(document_type, branch),
        )
