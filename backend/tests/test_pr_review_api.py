from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.schemas.pr_review import PullRequestReviewResponse

GET_URL = "/api/v1/repositories/{repository_id}/pull-requests/{pull_request_id}/review"
REGEN_URL = "/api/v1/repositories/{repository_id}/pull-requests/{pull_request_id}/review/regenerate"


@pytest.mark.asyncio
async def test_pr_review_get_requires_auth(client):
    response = await client.get(
        GET_URL.format(repository_id=uuid4(), pull_request_id=uuid4()),
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_pr_review_get_success(authenticated_client):
    repo_id = uuid4()
    pull_request_id = uuid4()
    mock_response = PullRequestReviewResponse(
        pull_request_id=pull_request_id,
        title="PR #1: Feature",
        content="# Summary\n\nGood change.",
        generated_at=datetime.now(timezone.utc),
    )

    with patch(
        "app.api.v1.endpoints.repositories._build_pr_review_service",
    ) as mock_build:
        mock_service = AsyncMock()
        mock_service.get_review = AsyncMock(return_value=mock_response)
        mock_build.return_value = mock_service
        response = await authenticated_client.get(
            GET_URL.format(repository_id=repo_id, pull_request_id=pull_request_id),
        )

    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "# Summary\n\nGood change."
    assert data["pull_request_id"] == str(pull_request_id)


@pytest.mark.asyncio
async def test_pr_review_get_not_found(authenticated_client):
    from app.services.exceptions import NotFoundError

    repo_id = uuid4()
    pull_request_id = uuid4()

    with patch(
        "app.api.v1.endpoints.repositories._build_pr_review_service",
    ) as mock_build:
        mock_service = AsyncMock()
        mock_service.get_review = AsyncMock(side_effect=NotFoundError("Pull request not found"))
        mock_build.return_value = mock_service
        response = await authenticated_client.get(
            GET_URL.format(repository_id=repo_id, pull_request_id=pull_request_id),
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_pr_review_regenerate(authenticated_client):
    repo_id = uuid4()
    pull_request_id = uuid4()
    mock_response = PullRequestReviewResponse(
        pull_request_id=pull_request_id,
        title="PR #1: Feature",
        content="# Summary\n\nRegenerated.",
        generated_at=datetime.now(timezone.utc),
    )

    with patch(
        "app.api.v1.endpoints.repositories._build_pr_review_service",
    ) as mock_build:
        mock_service = AsyncMock()
        mock_service.regenerate = AsyncMock(return_value=mock_response)
        mock_build.return_value = mock_service
        response = await authenticated_client.post(
            REGEN_URL.format(repository_id=repo_id, pull_request_id=pull_request_id),
            json={},
        )

    assert response.status_code == 200
    assert response.json()["content"] == "# Summary\n\nRegenerated."
