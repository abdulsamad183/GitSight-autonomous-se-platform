from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.repositories import pr_review_repository, pull_request_repository
from app.schemas.pr_review import PullRequestReviewResponse
from app.services import repository_detail_service
from app.services.ai.engine import AIEngine
from app.services.exceptions import LLMProviderError, NotFoundError
from app.services.pr_review.context_collector import PrReviewContextCollector
from app.services.pr_review.planner import CodeReviewPlanner


def _to_response(review, *, pull_request_id: UUID) -> PullRequestReviewResponse:
    return PullRequestReviewResponse(
        pull_request_id=pull_request_id,
        title=review.title,
        content=review.content,
        generated_at=review.generated_at,
    )


class PullRequestReviewService:
    def __init__(
        self,
        db: AsyncSession,
        engine: AIEngine,
        settings: Settings,
        planner: CodeReviewPlanner | None = None,
        context_collector: PrReviewContextCollector | None = None,
    ) -> None:
        self.db = db
        self.engine = engine
        self.settings = settings
        self.planner = planner or CodeReviewPlanner()
        self.context_collector = context_collector or PrReviewContextCollector(
            engine.executor,
            engine.context_builder,
        )

    async def _get_pull_request_or_raise(
        self,
        *,
        repository_id: UUID,
        user_id: UUID,
        pull_request_id: UUID,
    ):
        await repository_detail_service.get_repository_or_raise(
            self.db,
            repository_id=repository_id,
            user_id=user_id,
        )
        pull_request = await pull_request_repository.get_by_id_for_repository(
            self.db,
            repository_id=repository_id,
            pull_request_id=pull_request_id,
        )
        if pull_request is None:
            raise NotFoundError("Pull request not found")
        return pull_request

    async def _ensure_llm_ready(self) -> None:
        if not self.settings.groq_api_key:
            raise LLMProviderError("GROQ_API_KEY is not configured")

    async def get_review(
        self,
        *,
        repository_id: UUID,
        user_id: UUID,
        pull_request_id: UUID,
        force_regenerate: bool = False,
    ) -> PullRequestReviewResponse:
        if not force_regenerate:
            cached = await pr_review_repository.get_by_pull_request(
                self.db,
                repository_id=repository_id,
                pull_request_id=pull_request_id,
            )
            if cached is not None:
                return _to_response(cached, pull_request_id=pull_request_id)

        pull_request = await self._get_pull_request_or_raise(
            repository_id=repository_id,
            user_id=user_id,
            pull_request_id=pull_request_id,
        )
        await self._ensure_llm_ready()

        review_plan = await self.planner.plan(
            self.db,
            repository_id=repository_id,
            pull_request=pull_request,
            settings=self.settings,
        )
        content, _ = await self.engine.generate_pr_review(
            repository_id,
            user_id,
            review_plan,
            pr_number=pull_request.number,
            branch=review_plan.source_branch,
            context_collector=self.context_collector,
        )

        stored = await pr_review_repository.upsert(
            self.db,
            repository_id=repository_id,
            pull_request_id=pull_request.id,
            title=review_plan.title,
            content=content,
        )
        await self.db.commit()
        return _to_response(stored, pull_request_id=pull_request.id)

    async def regenerate(
        self,
        *,
        repository_id: UUID,
        user_id: UUID,
        pull_request_id: UUID,
    ) -> PullRequestReviewResponse:
        await pr_review_repository.delete_by_pull_request(
            self.db,
            repository_id=repository_id,
            pull_request_id=pull_request_id,
        )
        await self.db.flush()
        return await self.get_review(
            repository_id=repository_id,
            user_id=user_id,
            pull_request_id=pull_request_id,
            force_regenerate=True,
        )
