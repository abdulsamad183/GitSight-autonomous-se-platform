from app.models.repository_document import DocumentType
from app.services.documentation.discovery import (
    _path_priority,
    _title_from_path,
)


def test_path_priority_readme_root():
    assert _path_priority(DocumentType.REPOSITORY_OVERVIEW, "README.md") == 0
    assert _path_priority(DocumentType.REPOSITORY_OVERVIEW, "docs/README.md") is not None


def test_path_priority_architecture():
    assert _path_priority(DocumentType.ARCHITECTURE_OVERVIEW, "docs/architecture.md") == 0
    assert _path_priority(DocumentType.ARCHITECTURE_OVERVIEW, "src/main.py") is None


def test_title_from_readme_path():
    title = _title_from_path("README.md", DocumentType.REPOSITORY_OVERVIEW)
    assert title == "Repository Overview"


def test_title_from_nested_doc():
    title = _title_from_path("docs/my-module.md", DocumentType.MODULES)
    assert "My Module" in title or title == "My Module"
