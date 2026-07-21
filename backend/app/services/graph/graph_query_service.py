from collections import deque
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import repository_detail_repository, repository_repository
from app.services.exceptions import NotFoundError, ValidationError
from app.services.graph import repository_graph_service
from app.services.repository_detail_service import _resolve_snapshot

DEFAULT_MAX_DEPTH = 3
MAX_ALLOWED_DEPTH = 8
MAX_PATHS = 10


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


def compute_blast_radius(
    adjacency: dict[str, list[str]],
    *,
    start_file: str,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> list[tuple[str, int]]:
    """BFS outward from start_file. Returns (file_path, hop) excluding the start."""
    if max_depth < 1:
        return []

    results: list[tuple[str, int]] = []
    visited = {start_file}
    queue: deque[tuple[str, int]] = deque([(start_file, 0)])

    while queue:
        current, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for neighbor in adjacency.get(current, []):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            hop = depth + 1
            results.append((neighbor, hop))
            queue.append((neighbor, hop))

    results.sort(key=lambda item: (item[1], item[0]))
    return results


def find_import_paths(
    adjacency: dict[str, list[str]],
    *,
    source_file: str,
    target_file: str,
    max_depth: int = 5,
    limit: int = MAX_PATHS,
) -> list[list[str]]:
    if source_file == target_file:
        return []

    paths: list[list[str]] = []
    queue: deque[tuple[str, list[str]]] = deque([(source_file, [source_file])])
    visited_paths: set[tuple[str, ...]] = set()

    while queue and len(paths) < limit:
        current, path = queue.popleft()
        if len(path) > max_depth + 1:
            continue
        if current == target_file and len(path) > 1:
            paths.append(path)
            continue
        for neighbor in adjacency.get(current, []):
            if neighbor in path:
                continue
            next_path = path + [neighbor]
            key = tuple(next_path)
            if key in visited_paths:
                continue
            visited_paths.add(key)
            queue.append((neighbor, next_path))

    return paths


def _clamp_depth(max_depth: int | None, default: int = DEFAULT_MAX_DEPTH) -> int:
    depth = default if max_depth is None else max_depth
    if depth < 1 or depth > MAX_ALLOWED_DEPTH:
        raise ValidationError(f"max_depth must be between 1 and {MAX_ALLOWED_DEPTH}")
    return depth


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


async def blast_radius(
    db: AsyncSession,
    *,
    repository_id: UUID,
    user_id: UUID,
    file_path: str,
    branch: str | None = None,
    max_depth: int | None = None,
    direction: str = "dependents",
) -> dict:
    if not file_path or not file_path.strip():
        raise ValidationError("file_path is required")
    if direction not in {"dependents", "dependencies"}:
        raise ValidationError("direction must be dependents or dependencies")

    depth = _clamp_depth(max_depth)
    repository = await repository_repository.get_by_id_for_user(db, repository_id, user_id)
    if repository is None:
        raise NotFoundError("Repository not found")

    edges = await get_import_edges(db, repository_id=repository_id, user_id=user_id, branch=branch)
    adjacency = _build_adjacency(edges)
    walk_adj = _reverse_adjacency(adjacency) if direction == "dependents" else adjacency
    nodes = compute_blast_radius(walk_adj, start_file=file_path.strip(), max_depth=depth)
    snapshot, _, selected_branch = await _resolve_snapshot(db, repository, branch)

    return {
        "file_path": file_path.strip(),
        "direction": direction,
        "max_depth": depth,
        "branch": selected_branch if snapshot else branch,
        "nodes": [{"file_path": path, "hop": hop} for path, hop in nodes],
        "total": len(nodes),
    }


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
    return find_import_paths(
        adjacency,
        source_file=source_file,
        target_file=target_file,
        max_depth=max_depth,
        limit=MAX_PATHS,
    )


async def find_path(
    db: AsyncSession,
    *,
    repository_id: UUID,
    user_id: UUID,
    source_file: str,
    target_file: str,
    branch: str | None = None,
    max_depth: int | None = None,
) -> dict:
    if not source_file or not source_file.strip():
        raise ValidationError("source_file is required")
    if not target_file or not target_file.strip():
        raise ValidationError("target_file is required")

    depth = _clamp_depth(max_depth, default=5)
    repository = await repository_repository.get_by_id_for_user(db, repository_id, user_id)
    if repository is None:
        raise NotFoundError("Repository not found")

    paths = await trace_path(
        db,
        repository_id=repository_id,
        user_id=user_id,
        source_file=source_file.strip(),
        target_file=target_file.strip(),
        branch=branch,
        max_depth=depth,
    )
    snapshot, _, selected_branch = await _resolve_snapshot(db, repository, branch)

    return {
        "source_file": source_file.strip(),
        "target_file": target_file.strip(),
        "max_depth": depth,
        "branch": selected_branch if snapshot else branch,
        "paths": paths,
        "total_paths": len(paths),
    }
