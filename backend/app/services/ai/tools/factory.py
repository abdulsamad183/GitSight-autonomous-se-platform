from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.services.ai.tools.branch_tool import BranchTool
from app.services.ai.tools.graph_tool import GraphTool
from app.services.ai.tools.registry import ToolRegistry
from app.services.ai.tools.repository_metadata_tool import RepositoryMetadataTool
from app.services.ai.tools.search_tool import SearchTool
from app.services.search_service import SearchService


def build_default_tool_registry(db: AsyncSession, settings: Settings) -> ToolRegistry:
    registry = ToolRegistry()
    search_service = SearchService(db, settings)
    registry.register(RepositoryMetadataTool())
    registry.register(SearchTool(search_service))
    registry.register(BranchTool())
    registry.register(GraphTool())
    return registry
