from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

BLAST_URL = "/api/v1/repositories/{repository_id}/graph/blast-radius"
PATH_URL = "/api/v1/repositories/{repository_id}/graph/path"
SUMMARY_URL = "/api/v1/repositories/{repository_id}/graph/import-summary"


@pytest.mark.asyncio
async def test_blast_radius_requires_auth(client):
    response = await client.get(
        BLAST_URL.format(repository_id=uuid4()),
        params={"file_path": "a.py"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_blast_radius_success(authenticated_client):
    repo_id = uuid4()
    payload = {
        "file_path": "a.py",
        "direction": "dependents",
        "max_depth": 2,
        "branch": "main",
        "nodes": [{"file_path": "b.py", "hop": 1}],
        "total": 1,
        "message": None,
        "suggested_direction": None,
    }
    with patch(
        "app.api.v1.endpoints.repositories.graph_query_service.blast_radius",
        new_callable=AsyncMock,
        return_value=payload,
    ) as mock_blast:
        response = await authenticated_client.get(
            BLAST_URL.format(repository_id=repo_id),
            params={"file_path": "a.py", "direction": "dependents", "max_depth": 2},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["nodes"][0]["file_path"] == "b.py"
    mock_blast.assert_awaited_once()


@pytest.mark.asyncio
async def test_blast_radius_invalid_direction(authenticated_client):
    repo_id = uuid4()
    with patch(
        "app.api.v1.endpoints.repositories.graph_query_service.blast_radius",
        new_callable=AsyncMock,
        side_effect=__import__(
            "app.services.exceptions", fromlist=["ValidationError"]
        ).ValidationError("direction must be dependents or dependencies"),
    ):
        response = await authenticated_client.get(
            BLAST_URL.format(repository_id=repo_id),
            params={"file_path": "a.py", "direction": "sideways"},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_graph_path_success(authenticated_client):
    repo_id = uuid4()
    payload = {
        "source_file": "a.py",
        "target_file": "c.py",
        "max_depth": 5,
        "branch": "main",
        "paths": [["a.py", "b.py", "c.py"]],
        "total_paths": 1,
        "bidirectional": False,
        "message": None,
    }
    with patch(
        "app.api.v1.endpoints.repositories.graph_query_service.find_path",
        new_callable=AsyncMock,
        return_value=payload,
    ) as mock_find:
        response = await authenticated_client.get(
            PATH_URL.format(repository_id=repo_id),
            params={
                "source_file": "a.py",
                "target_file": "c.py",
                "bidirectional": "true",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["total_paths"] == 1
    assert data["paths"][0] == ["a.py", "b.py", "c.py"]
    mock_find.assert_awaited_once()
    assert mock_find.await_args.kwargs["bidirectional"] is True


@pytest.mark.asyncio
async def test_import_summary_success(authenticated_client):
    repo_id = uuid4()
    payload = {
        "branch": "main",
        "edges": [
            {
                "source_path": "a.py",
                "target_path": "b.py",
                "dependency_type": "import",
            }
        ],
        "connected_files": ["a.py", "b.py"],
        "source_files": ["a.py"],
        "target_files": ["b.py"],
        "total_edges": 1,
    }
    with patch(
        "app.api.v1.endpoints.repositories.graph_query_service.import_graph_summary",
        new_callable=AsyncMock,
        return_value=payload,
    ):
        response = await authenticated_client.get(SUMMARY_URL.format(repository_id=repo_id))
    assert response.status_code == 200
    data = response.json()
    assert data["total_edges"] == 1
    assert data["connected_files"] == ["a.py", "b.py"]
