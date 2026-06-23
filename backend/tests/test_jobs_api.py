from unittest.mock import AsyncMock, patch

import pytest

ANALYZE_URL = "/api/v1/repositories/analyze"
JOBS_URL = "/api/v1/jobs"


@pytest.mark.asyncio
async def test_get_job_requires_auth(client):
    response = await client.get(f"{JOBS_URL}/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_job_status(authenticated_client):
    with (
        patch(
            "app.services.analysis_service.validate_public_repo",
            new_callable=AsyncMock,
        ),
        patch("app.services.analysis_service.run_analysis_job", new_callable=AsyncMock),
    ):
        analyze_response = await authenticated_client.post(
            ANALYZE_URL,
            json={"github_url": "https://github.com/octocat/Hello-World"},
        )

    job_id = analyze_response.json()["job_id"]
    response = await authenticated_client.get(f"{JOBS_URL}/{job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["status"] == "PENDING"
    assert data["progress"] == 0
    assert "events" in data
    assert isinstance(data["events"], list)


@pytest.mark.asyncio
async def test_get_job_not_found(authenticated_client):
    response = await authenticated_client.get(f"{JOBS_URL}/00000000-0000-0000-0000-000000000099")
    assert response.status_code == 404
