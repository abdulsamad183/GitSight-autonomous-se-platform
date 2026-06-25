from collections import deque
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import repository_detail_repository, repository_repository
from app.services.graph import repository_graph_service
from app.services.repository_detail_service import _resolve_snapshot


async def get_structure_graph(
    db: AsyncSession,
    *,
    repository_id: UUID,
    user_id: UUID,
    branch: str | None = None,
):
    return await repository_graph_service.get_repository_graph(
        db,
        repository_id=repository_id,
        user_id=user_id,
        branch=branch,
    )


async def find_symbol(
    db: AsyncSession,
    *,
    repository_id: UUID,
    user_id: UUID,
    symbol_name: str,
    branch: str | None = None,
) -> list[dict]:
    repository = await repository_repository.get_by_id_for_user(db, repository_id, user_id)
    if repository is None:
        return []
    snapshot, _, _ = await _resolve_snapshot(db, repository, branch)
    if snapshot is None:
        return []

    symbol_rows = await repository_detail_repository.list_symbols_by_snapshot(db, snapshot.id)
    matches = []
    needle = symbol_name.lower()
    for symbol, file_path in symbol_rows:
        if needle in symbol.symbol_name.lower():
            matches.append(
                {
                    "symbol_name": symbol.symbol_name,
                    "symbol_type": symbol.symbol_type.value,
                    "file_path": file_path,
                    "start_line": symbol.start_line,
                    "end_line": symbol.end_line,
                    "signature": symbol.signature,
                }
            )
    return matches[:20]


async def get_import_edges(
    db: AsyncSession,
    *,
    repository_id: UUID,
    user_id: UUID,
    branch: str | None = None,
) -> list[dict]:
    repository = await repository_repository.get_by_id_for_user(db, repository_id, user_id)
    if repository is None:
        return []
    snapshot, _, _ = await _resolve_snapshot(db, repository, branch)
    if snapshot is None:
        return []

    rows = await repository_detail_repository.list_dependencies_by_snapshot(db, snapshot.id)
    return [
        {
            "source_path": source_path,
            "target_path": target_path,
            "dependency_type": edge.dependency_type.value,
        }
        for edge, source_path, target_path in rows
    ]


def _build_adjacency(edges: list[dict]) -> dict[str, list[str]]:
    adjacency: dict[str, list[str]] = {}
    for edge in edges:
        source = edge["source_path"]
        target = edge["target_path"]
        adjacency.setdefault(source, []).append(target)
    return adjacency


def _reverse_adjacency(adjacency: dict[str, list[str]]) -> dict[str, list[str]]:
    reversed_adj: dict[str, list[str]] = {}
    for source, targets in adjacency.items():
        for target in targets:
            reversed_adj.setdefault(target, []).append(source)
    return reversed_adj


async def dependents(
    db: AsyncSession,
    *,
    repository_id: UUID,
    user_id: UUID,
    file_path: str,
    branch: str | None = None,
) -> list[str]:
    edges = await get_import_edges(db, repository_id=repository_id, user_id=user_id, branch=branch)
    rev = _reverse_adjacency(_build_adjacency(edges))
    return sorted(rev.get(file_path, []))


async def dependencies(
    db: AsyncSession,
    *,
    repository_id: UUID,
    user_id: UUID,
    file_path: str,
    branch: str | None = None,
) -> list[str]:
    edges = await get_import_edges(db, repository_id=repository_id, user_id=user_id, branch=branch)
    adjacency = _build_adjacency(edges)
    return sorted(adjacency.get(file_path, []))


async def trace_path(
    db: AsyncSession,
    *,
    repository_id: UUID,
    user_id: UUID,
    source_file: str,
    target_file: str,
    branch: str | None = None,
    max_depth: int = 5,
) -> list[list[str]]:
    edges = await get_import_edges(db, repository_id=repository_id, user_id=user_id, branch=branch)
    adjacency = _build_adjacency(edges)
    paths: list[list[str]] = []
    queue: deque[tuple[str, list[str]]] = deque([(source_file, [source_file])])
    visited_paths: set[tuple[str, ...]] = set()

    while queue:
        current, path = queue.popleft()
        if len(path) > max_depth + 1:
            continue
        if current == target_file and len(path) > 1:
            paths.append(path)
            continue
        for neighbor in adjacency.get(current, []):
            next_path = path + [neighbor]
            key = tuple(next_path)
            if key in visited_paths:
                continue
            visited_paths.add(key)
            queue.append((neighbor, next_path))

    return paths[:10]
