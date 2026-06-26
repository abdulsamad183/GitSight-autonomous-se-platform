from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.repository_document import (
    DOCUMENT_TYPE_TITLES,
    DocumentGeneratedBy,
    DocumentType,
)
from app.repositories import repository_document_repository
from app.schemas.documentation import (
    DocumentationListResponse,
    DocumentationResponse,
    DocumentationTypeItem,
)
from app.services import repository_detail_service
from app.services.ai.engine import AIEngine
from app.services.documentation.planner import DocumentationPlanner
from app.services.exceptions import LLMProviderError, ValidationError


def parse_document_type(value: str) -> DocumentType:
    try:
        return DocumentType(value)
    except ValueError as exc:
        raise ValidationError(f"Invalid document type: {value}") from exc


def _to_response(document) -> DocumentationResponse:
    return DocumentationResponse(
        document_type=document.document_type.value,
        title=document.title,
        content=document.content,
        generated_by=document.generated_by.value,
        generated_at=document.generated_at,
        source_path=document.source_path,
    )


class DocumentationService:
    def __init__(
        self,
        db: AsyncSession,
        engine: AIEngine,
        settings: Settings,
        planner: DocumentationPlanner | None = None,
    ) -> None:
        self.db = db
        self.engine = engine
        self.settings = settings
        self.planner = planner or DocumentationPlanner()

    async def _resolve_branch(
        self,
        repository_id: UUID,
        user_id: UUID,
        branch: str | None,
    ) -> str:
        repository = await repository_detail_service.get_repository_or_raise(
            self.db, repository_id=repository_id, user_id=user_id
        )
        if branch:
            await repository_detail_service.get_repository_detail(
                self.db,
                repository_id=repository_id,
                user_id=user_id,
                branch=branch,
            )
            return branch

        summary = await repository_detail_service.get_repository_summary(
            self.db,
            repository_id=repository_id,
            user_id=user_id,
        )
        if summary.default_branch:
            return summary.default_branch

        branches = await repository_detail_service.list_repository_branches(
            self.db,
            repository_id=repository_id,
            user_id=user_id,
        )
        if not branches:
            raise ValidationError("Repository has no analyzed branches")
        return branches[0].branch

    async def _ensure_llm_ready(self) -> None:
        if not self.settings.groq_api_key:
            raise LLMProviderError("GROQ_API_KEY is not configured")

    async def list_types(
        self,
        *,
        repository_id: UUID,
        user_id: UUID,
        branch: str | None = None,
    ) -> DocumentationListResponse:
        await repository_detail_service.get_repository_or_raise(
            self.db, repository_id=repository_id, user_id=user_id
        )
        cached = {
            doc.document_type: doc
            for doc in await repository_document_repository.list_for_repository(
                self.db, repository_id=repository_id
            )
        }

        items: list[DocumentationTypeItem] = []
        for doc_type in DocumentType:
            cached_doc = cached.get(doc_type)
            items.append(
                DocumentationTypeItem(
                    document_type=doc_type.value,
                    title=DOCUMENT_TYPE_TITLES[doc_type],
                    available=cached_doc is not None,
                    generated_by=cached_doc.generated_by.value if cached_doc else None,
                    generated_at=cached_doc.generated_at if cached_doc else None,
                    source_path=cached_doc.source_path if cached_doc else None,
                )
            )
        return DocumentationListResponse(types=items)

    async def get_document(
        self,
        *,
        repository_id: UUID,
        user_id: UUID,
        document_type: DocumentType,
        branch: str | None = None,
        force_regenerate: bool = False,
    ) -> DocumentationResponse:
        if not force_regenerate:
            cached = await repository_document_repository.get_by_type(
                self.db,
                repository_id=repository_id,
                document_type=document_type,
            )
            if cached is not None:
                return _to_response(cached)

        resolved_branch = await self._resolve_branch(repository_id, user_id, branch)

        plan = await self.planner.plan(
            self.db,
            repository_id=repository_id,
            document_type=document_type,
            branch=resolved_branch,
            skip_discovery=force_regenerate,
        )

        if not plan.requires_ai and plan.existing_document is not None:
            stored = await repository_document_repository.upsert(
                self.db,
                repository_id=repository_id,
                document_type=document_type,
                title=plan.title,
                content=plan.existing_document.content,
                generated_by=DocumentGeneratedBy.REPOSITORY,
                source_path=plan.existing_document.file_path,
            )
            await self.db.commit()
            return _to_response(stored)

        await self._ensure_llm_ready()
        if plan.tool_plan is None:
            raise ValidationError("No tool plan available for documentation generation")

        content, _ = await self.engine.generate_documentation(
            repository_id,
            user_id,
            plan.tool_plan,
            document_type=document_type.value,
            title=plan.title,
            branch=resolved_branch,
        )

        stored = await repository_document_repository.upsert(
            self.db,
            repository_id=repository_id,
            document_type=document_type,
            title=plan.title,
            content=content,
            generated_by=DocumentGeneratedBy.AI,
            source_path=None,
        )
        await self.db.commit()
        return _to_response(stored)

    async def regenerate(
        self,
        *,
        repository_id: UUID,
        user_id: UUID,
        document_type: DocumentType,
        branch: str | None = None,
    ) -> DocumentationResponse:
        await repository_document_repository.delete_by_type(
            self.db,
            repository_id=repository_id,
            document_type=document_type,
        )
        await self.db.flush()
        return await self.get_document(
            repository_id=repository_id,
            user_id=user_id,
            document_type=document_type,
            branch=branch,
            force_regenerate=True,
        )
