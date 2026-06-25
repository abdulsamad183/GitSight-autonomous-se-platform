from app.services.ai.tools.registry import ToolRegistry
from app.services.ai.tools.repository_metadata_tool import RepositoryMetadataTool
from app.services.ai.tools.search_tool import SearchTool


class DummySearchService:
    pass


def test_registry_register_and_get():
    registry = ToolRegistry()
    tool = RepositoryMetadataTool()
    registry.register(tool)
    assert registry.get("repository") is tool
    assert registry.get("missing") is None


def test_registry_list_tools():
    registry = ToolRegistry()
    registry.register(RepositoryMetadataTool())
    registry.register(SearchTool(DummySearchService()))  # type: ignore[arg-type]
    names = {tool.name for tool in registry.list_tools()}
    assert names == {"repository", "search"}


def test_registry_validate_success():
    registry = ToolRegistry()
    registry.register(RepositoryMetadataTool())
    valid, error = registry.validate("repository", {"action": "summary"})
    assert valid is True
    assert error is None


def test_registry_validate_unknown_tool():
    registry = ToolRegistry()
    valid, error = registry.validate("missing", {})
    assert valid is False
    assert "Unknown tool" in (error or "")


def test_registry_validate_missing_required():
    registry = ToolRegistry()
    registry.register(RepositoryMetadataTool())
    valid, error = registry.validate("repository", {})
    assert valid is False
    assert "Missing required" in (error or "")
