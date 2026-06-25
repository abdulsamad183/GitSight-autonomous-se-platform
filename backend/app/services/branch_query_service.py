from collections import Counter
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_chunk import ChunkType
from app.repositories import code_chunk_repository, snapshot_repository
from app.services import repository_detail_service
from app.services.search_service import SearchService


async def list_branches(
    db: AsyncSession,
    *,
    repository_id: UUID,
    user_id: UUID,
) -> list[dict]:
    branches = await repository_detail_service.list_repository_branches(
        db, repository_id=repository_id, user_id=user_id
    )
    return [branch.model_dump() for branch in branches]


async def branch_summary(
    db: AsyncSession,
    *,
    repository_id: UUID,
    user_id: UUID,
    branch: str,
) -> dict:
    branches = await list_branches(db, repository_id=repository_id, user_id=user_id)
    for item in branches:
        if item["branch"] == branch:
            return item
    return {"error": f"Branch '{branch}' not found"}


async def summarize_branch_changes(
    db: AsyncSession,
    *,
    repository_id: UUID,
    branch: str,
    limit: int = 50,
) -> dict:
    chunks, total = await code_chunk_repository.list_by_repository(
        db,
        repository_id=repository_id,
        branch_name=branch,
        chunk_type=ChunkType.DIFF_HUNK,
        limit=limit,
    )
    files: dict[str, list[dict]] = {}
    change_types: Counter[str] = Counter()
    for chunk in chunks:
        change_types[chunk.change_type.value if chunk.change_type else "unknown"] += 1
        files.setdefault(chunk.file_path, []).append(
            {
                "symbol_name": chunk.symbol_name,
                "change_type": chunk.change_type.value if chunk.change_type else None,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
            }
        )
    return {
        "branch": branch,
        "total_diff_chunks": total,
        "change_type_counts": dict(change_types),
        "changed_files": [
            {"file_path": path, "hunks": hunks} for path, hunks in sorted(files.items())
        ],
    }


async def compare_branches(
    db: AsyncSession,
    *,
    repository_id: UUID,
    user_id: UUID,
    base_branch: str,
    head_branch: str,
) -> dict:
    base = await branch_summary(
        db, repository_id=repository_id, user_id=user_id, branch=base_branch
    )
    head = await branch_summary(
        db, repository_id=repository_id, user_id=user_id, branch=head_branch
    )
    head_changes = await summarize_branch_changes(
        db, repository_id=repository_id, branch=head_branch
    )
    return {
        "base_branch": base_branch,
        "head_branch": head_branch,
        "base_stats": base,
        "head_stats": head,
        "head_changes": head_changes,
    }


async def find_feature_across_branches(
    db: AsyncSession,
    *,
    repository_id: UUID,
    user_id: UUID,
    query: str,
    settings,
    max_branches: int,
) -> dict:
    search_service = SearchService(db, settings)
    branches = await list_branches(db, repository_id=repository_id, user_id=user_id)
    results_by_branch: dict[str, list[dict]] = {}

    for branch_info in branches[:max_branches]:
        branch_name = branch_info["branch"]
        response = await search_service.search(
            repository_id,
            query,
            mode="hybrid",
            limit=5,
            branch=branch_name,
        )
        if response.results:
            results_by_branch[branch_name] = [
                {
                    "file_path": r.file_path,
                    "symbol_name": r.symbol_name,
                    "chunk_type": r.chunk_type,
                    "score": r.final_score,
                }
                for r in response.results
            ]

    return {"query": query, "results_by_branch": results_by_branch}


async def get_available_branch_names(db: AsyncSession, repository_id: UUID) -> list[str]:
    snapshots = await snapshot_repository.list_for_repository(db, repository_id)
    return [snap.branch for snap in snapshots]
