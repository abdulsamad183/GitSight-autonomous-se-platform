from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import repository_detail_repository, repository_repository
from app.schemas.graph import RepositoryGraphResponse
from app.services.exceptions import NotFoundError, ValidationError
from app.services.graph.base import GraphBuildContext
from app.services.graph.structure_graph_builder import StructureGraphBuilder
from app.services.repository_detail_service import _resolve_snapshot

_STRUCTURE_BUILDERS = {
    "structure": StructureGraphBuilder(),
}


async def get_repository_graph(
    db: AsyncSession,
    *,
    repository_id: UUID,
    user_id: UUID,
    branch: str | None = None,
    graph_type: str = "structure",
) -> RepositoryGraphResponse:
    repository = await repository_repository.get_by_id_for_user(db, repository_id, user_id)
    if repository is None:
        raise NotFoundError("Repository not found")

    builder = _STRUCTURE_BUILDERS.get(graph_type)
    if builder is None:
        raise ValidationError(f"Unknown graph type: {graph_type}")

    snapshot, _, selected_branch = await _resolve_snapshot(db, repository, branch)

    if snapshot is None:
        return builder.build(
            GraphBuildContext(
                repository=repository,
                branch=selected_branch,
                files=[],
                symbols=[],
            )
        )

    files = await repository_detail_repository.list_files_for_graph(db, snapshot.id)
    symbols = await repository_detail_repository.list_symbols_for_graph(db, snapshot.id)

    return builder.build(
        GraphBuildContext(
            repository=repository,
            branch=selected_branch,
            files=files,
            symbols=symbols,
        )
    )
