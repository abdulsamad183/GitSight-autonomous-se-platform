from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

INDEX_STATUS_URL = "/api/v1/repositories/{repository_id}/index-status"
CHUNKS_URL = "/api/v1/repositories/{repository_id}/chunks"
REINDEX_URL = "/api/v1/repositories/{repository_id}/reindex"


@pytest.mark.asyncio
async def test_index_status_requires_auth(client):
    response = await client.get(INDEX_STATUS_URL.format(repository_id=uuid4()))
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_index_status_not_found(authenticated_client):
    response = await authenticated_client.get(INDEX_STATUS_URL.format(repository_id=uuid4()))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_chunks_requires_auth(client):
    response = await client.get(CHUNKS_URL.format(repository_id=uuid4()))
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_reindex_requires_auth(client):
    response = await client.post(REINDEX_URL.format(repository_id=uuid4()))
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_reindex_not_found(authenticated_client):
    response = await authenticated_client.post(REINDEX_URL.format(repository_id=uuid4()))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reindex_success(authenticated_client):
    repo_id = uuid4()
    job_id = uuid4()

    with (
        patch(
            "app.services.indexing_service.start_reindex",
            new_callable=AsyncMock,
            return_value=(repo_id, job_id),
        ),
        patch("app.services.indexing_service.run_indexing_job", new_callable=AsyncMock),
    ):
        response = await authenticated_client.post(REINDEX_URL.format(repository_id=repo_id))

    assert response.status_code == 202
    data = response.json()
    assert data["repository_id"] == str(repo_id)
    assert data["job_id"] == str(job_id)
    assert data["status"] == "PENDING"
