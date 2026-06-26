import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.models.repository_document import DocumentGeneratedBy, DocumentType
from app.services.documentation.service import DocumentationService, parse_document_type


def test_parse_document_type_valid():
    assert parse_document_type("repository_overview") == DocumentType.REPOSITORY_OVERVIEW


def test_parse_document_type_invalid():
    from app.services.exceptions import ValidationError

    with pytest.raises(ValidationError):
        parse_document_type("invalid_type")


@pytest.mark.asyncio
async def test_get_document_returns_cached(monkeypatch):
    from datetime import datetime, timezone

    repo_id = uuid4()
    user_id = uuid4()
    cached = MagicMock()
    cached.document_type = DocumentType.REPOSITORY_OVERVIEW
    cached.title = "Repository Overview"
    cached.content = "# Cached"
    cached.generated_by = DocumentGeneratedBy.AI
    cached.generated_at = datetime.now(timezone.utc)
    cached.source_path = None

    db = AsyncMock()
    engine = AsyncMock()

    monkeypatch.setattr(
        "app.services.documentation.service.repository_document_repository.get_by_type",
        AsyncMock(return_value=cached),
    )

    service = DocumentationService(db, engine, MagicMock())
    result = await service.get_document(
        repository_id=repo_id,
        user_id=user_id,
        document_type=DocumentType.REPOSITORY_OVERVIEW,
    )

    assert result.content == "# Cached"
    engine.generate_documentation.assert_not_called()


@pytest.mark.asyncio
async def test_get_document_uses_repository_source_without_llm(monkeypatch):
    from app.services.documentation.discovery import DiscoveredDocument
    from app.services.documentation.planner import DocumentationPlan

    repo_id = uuid4()
    user_id = uuid4()

    plan = DocumentationPlan(
        document_type=DocumentType.REPOSITORY_OVERVIEW,
        title="Repository Overview",
        requires_ai=False,
        existing_document=DiscoveredDocument(
            file_path="README.md",
            content="# Hello\n\n" + ("content " * 20),
            title="Repository Overview",
        ),
    )

    stored = MagicMock()
    stored.document_type = DocumentType.REPOSITORY_OVERVIEW
    stored.title = "Repository Overview"
    stored.content = plan.existing_document.content
    stored.generated_by = DocumentGeneratedBy.REPOSITORY
    stored.generated_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    stored.source_path = "README.md"

    db = AsyncMock()
    engine = AsyncMock()
    planner = AsyncMock()
    planner.plan = AsyncMock(return_value=plan)

    monkeypatch.setattr(
        "app.services.documentation.service.repository_document_repository.get_by_type",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.services.documentation.service.repository_document_repository.upsert",
        AsyncMock(return_value=stored),
    )
    monkeypatch.setattr(
        "app.services.documentation.service.repository_detail_service.get_repository_or_raise",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "app.services.documentation.service.repository_detail_service.get_repository_summary",
        AsyncMock(return_value=MagicMock(default_branch="main")),
    )

    service = DocumentationService(db, engine, MagicMock(), planner=planner)
    result = await service.get_document(
        repository_id=repo_id,
        user_id=user_id,
        document_type=DocumentType.REPOSITORY_OVERVIEW,
    )

    assert result.generated_by == "repository"
    assert result.source_path == "README.md"
    engine.generate_documentation.assert_not_called()
    db.commit.assert_awaited()
