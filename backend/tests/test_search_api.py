from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

SEARCH_URL = "/api/v1/repositories/{repository_id}/search"


@pytest.mark.asyncio
async def test_search_requires_auth(client):
    response = await client.get(SEARCH_URL.format(repository_id=uuid4()), params={"q": "jwt"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_search_empty_query(authenticated_client):
    repo_id = uuid4()
    response = await authenticated_client.get(
        SEARCH_URL.format(repository_id=repo_id),
        params={"q": "   "},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_search_invalid_mode(authenticated_client):
    repo_id = uuid4()
    with patch(
        "app.api.v1.endpoints.repositories.repository_detail_service.get_repository_or_raise",
        new_callable=AsyncMock,
    ):
        response = await authenticated_client.get(
            SEARCH_URL.format(repository_id=repo_id),
            params={"q": "jwt", "mode": "invalid"},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_search_not_found(authenticated_client):
    response = await authenticated_client.get(
        SEARCH_URL.format(repository_id=uuid4()),
        params={"q": "jwt"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_success(authenticated_client):
    repo_id = uuid4()
    mock_response = MagicMock()
    mock_response.query = "jwt"
    mock_response.mode = "hybrid"
    mock_response.total_results = 1
    mock_response.limit = 20
    mock_response.offset = 0
    mock_response.execution_time_ms = 12.5
    mock_response.results = []

    with (
        patch(
            "app.api.v1.endpoints.repositories.repository_detail_service.get_repository_or_raise",
            new_callable=AsyncMock,
        ),
        patch(
            "app.api.v1.endpoints.repositories.SearchService.search",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_search,
    ):
        response = await authenticated_client.get(
            SEARCH_URL.format(repository_id=repo_id),
            params={
                "q": "jwt",
                "mode": "hybrid",
                "file_path": "src/",
                "chunk_type": "function",
                "language": "python",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "jwt"
    assert data["mode"] == "hybrid"
    assert data["total_results"] == 1
    mock_search.assert_awaited_once()
    kwargs = mock_search.await_args.kwargs
    assert kwargs["file_path"] == "src/"
    assert kwargs["chunk_type"] == "function"
    assert kwargs["language"] == "python"


@pytest.mark.asyncio
async def test_search_invalid_chunk_type(authenticated_client):
    repo_id = uuid4()
    with patch(
        "app.api.v1.endpoints.repositories.repository_detail_service.get_repository_or_raise",
        new_callable=AsyncMock,
    ):
        response = await authenticated_client.get(
            SEARCH_URL.format(repository_id=repo_id),
            params={"q": "jwt", "chunk_type": "not-a-type"},
        )
    assert response.status_code == 400
    assert "chunk_type" in response.json()["detail"]
