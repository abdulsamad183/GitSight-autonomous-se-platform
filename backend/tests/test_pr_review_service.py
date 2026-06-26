from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.pr_review.service import PullRequestReviewService


@pytest.mark.asyncio
async def test_get_review_returns_cached(monkeypatch):
    repo_id = uuid4()
    user_id = uuid4()
    pull_request_id = uuid4()

    cached = MagicMock()
    cached.title = "PR #1: Cached"
    cached.content = "# Cached Review"
    cached.generated_at = datetime.now(timezone.utc)

    db = AsyncMock()
    engine = AsyncMock()

    monkeypatch.setattr(
        "app.services.pr_review.service.pr_review_repository.get_by_pull_request",
        AsyncMock(return_value=cached),
    )

    service = PullRequestReviewService(db, engine, MagicMock())
    result = await service.get_review(
        repository_id=repo_id,
        user_id=user_id,
        pull_request_id=pull_request_id,
    )

    assert result.content == "# Cached Review"
    engine.generate_pr_review.assert_not_called()


@pytest.mark.asyncio
async def test_get_review_generates_and_stores(monkeypatch):
    repo_id = uuid4()
    user_id = uuid4()
    pull_request_id = uuid4()

    pull_request = MagicMock()
    pull_request.id = pull_request_id
    pull_request.number = 5

    review_plan = MagicMock()
    review_plan.title = "PR #5: Feature"
    review_plan.source_branch = "feature/x"

    stored = MagicMock()
    stored.title = review_plan.title
    stored.content = "# Generated Review"
    stored.generated_at = datetime.now(timezone.utc)

    db = AsyncMock()
    engine = AsyncMock()
    engine.generate_pr_review = AsyncMock(return_value=("# Generated Review", None))
    planner = AsyncMock()
    planner.plan = AsyncMock(return_value=review_plan)
    settings = MagicMock()
    settings.groq_api_key = "test-key"

    monkeypatch.setattr(
        "app.services.pr_review.service.pr_review_repository.get_by_pull_request",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.services.pr_review.service.repository_detail_service.get_repository_or_raise",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.services.pr_review.service.pull_request_repository.get_by_id_for_repository",
        AsyncMock(return_value=pull_request),
    )
    monkeypatch.setattr(
        "app.services.pr_review.service.pr_review_repository.upsert",
        AsyncMock(return_value=stored),
    )

    service = PullRequestReviewService(db, engine, settings, planner=planner)
    result = await service.get_review(
        repository_id=repo_id,
        user_id=user_id,
        pull_request_id=pull_request_id,
    )

    assert result.content == "# Generated Review"
    engine.generate_pr_review.assert_awaited_once()
    db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_regenerate_deletes_cache_and_forces_generation(monkeypatch):
    repo_id = uuid4()
    user_id = uuid4()
    pull_request_id = uuid4()

    delete_mock = AsyncMock()
    get_review_mock = AsyncMock(
        return_value=MagicMock(
            pull_request_id=pull_request_id,
            title="PR #1",
            content="# New",
            generated_at=datetime.now(timezone.utc),
        )
    )

    monkeypatch.setattr(
        "app.services.pr_review.service.pr_review_repository.delete_by_pull_request",
        delete_mock,
    )

    service = PullRequestReviewService(AsyncMock(), AsyncMock(), MagicMock())
    service.get_review = get_review_mock

    await service.regenerate(
        repository_id=repo_id,
        user_id=user_id,
        pull_request_id=pull_request_id,
    )

    delete_mock.assert_awaited_once()
    get_review_mock.assert_awaited_once_with(
        repository_id=repo_id,
        user_id=user_id,
        pull_request_id=pull_request_id,
        force_regenerate=True,
    )
