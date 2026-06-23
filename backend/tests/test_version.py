import pytest


@pytest.mark.asyncio
async def test_version_endpoint(client):
    response = await client.get("/api/v1/version")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "autonomous-software-engineer"
    assert data["version"] == "0.1.0"
