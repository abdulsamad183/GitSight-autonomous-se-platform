from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models.repository_document import DocumentGeneratedBy, DocumentType
from app.schemas.documentation import DocumentationListResponse, DocumentationResponse, DocumentationTypeItem

LIST_URL = "/api/v1/repositories/{repository_id}/documentation"
GET_URL = "/api/v1/repositories/{repository_id}/documentation/{document_type}"
REGEN_URL = "/api/v1/repositories/{repository_id}/documentation/{document_type}/regenerate"


@pytest.mark.asyncio
async def test_documentation_list_requires_auth(client):
    response = await client.get(LIST_URL.format(repository_id=uuid4()))
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_documentation_list_success(authenticated_client):
    repo_id = uuid4()
    mock_response = DocumentationListResponse(
        types=[
            DocumentationTypeItem(
                document_type="repository_overview",
                title="Repository Overview",
                available=False,
                generated_by=None,
                generated_at=None,
                source_path=None,
            )
        ]
    )

    with patch(
        "app.api.v1.endpoints.repositories._build_documentation_service",
    ) as mock_build:
        mock_service = AsyncMock()
        mock_service.list_types = AsyncMock(return_value=mock_response)
        mock_build.return_value = mock_service
        response = await authenticated_client.get(LIST_URL.format(repository_id=repo_id))

    assert response.status_code == 200
    data = response.json()
    assert len(data["types"]) == 1
    assert data["types"][0]["document_type"] == "repository_overview"


@pytest.mark.asyncio
async def test_documentation_get_success(authenticated_client):
    repo_id = uuid4()
    mock_response = DocumentationResponse(
        document_type="repository_overview",
        title="Repository Overview",
        content="# Hello",
        generated_by="repository",
        generated_at=datetime.now(timezone.utc),
        source_path="README.md",
    )

    with patch(
        "app.api.v1.endpoints.repositories._build_documentation_service",
    ) as mock_build:
        mock_service = AsyncMock()
        mock_service.get_document = AsyncMock(return_value=mock_response)
        mock_build.return_value = mock_service
        response = await authenticated_client.get(
            GET_URL.format(repository_id=repo_id, document_type="repository_overview")
        )

    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "# Hello"
    assert data["generated_by"] == "repository"


@pytest.mark.asyncio
async def test_documentation_invalid_type(authenticated_client):
    repo_id = uuid4()
    with patch(
        "app.api.v1.endpoints.repositories._build_documentation_service",
    ) as mock_build:
        mock_build.return_value = AsyncMock()
        response = await authenticated_client.get(
            GET_URL.format(repository_id=repo_id, document_type="not_a_type")
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_documentation_regenerate(authenticated_client):
    repo_id = uuid4()
    mock_response = DocumentationResponse(
        document_type="repository_overview",
        title="Repository Overview",
        content="# Regenerated",
        generated_by="ai",
        generated_at=datetime.now(timezone.utc),
        source_path=None,
    )

    with patch(
        "app.api.v1.endpoints.repositories._build_documentation_service",
    ) as mock_build:
        mock_service = AsyncMock()
        mock_service.regenerate = AsyncMock(return_value=mock_response)
        mock_build.return_value = mock_service
        response = await authenticated_client.post(
            REGEN_URL.format(repository_id=repo_id, document_type="repository_overview"),
            json={},
        )

    assert response.status_code == 200
    assert response.json()["content"] == "# Regenerated"
