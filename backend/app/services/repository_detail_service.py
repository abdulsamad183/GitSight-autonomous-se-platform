from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import JobStatus
from app.repositories import (
    job_event_repository,
    job_repository,
    repository_detail_repository,
    repository_repository,
    repository_stats_repository,
    snapshot_repository,
)
from app.schemas.job import JobEventItem, JobStatusResponse
from app.schemas.repository import (
    BranchSummaryResponse,
    DependencyItem,
    FileItem,
    RepositoryDetailResponse,
    RepositoryListItem,
    RepositorySummaryResponse,
    SymbolItem,
)
from app.services.exceptions import NotFoundError


def _map_job_status(status: JobStatus) -> str:
    if status == JobStatus.QUEUED:
        return "PENDING"
    return status.value.upper()


async def _resolve_snapshot(db, repository, branch: str | None):
    snapshots = await snapshot_repository.list_for_repository(db, repository.id)
    available = [snap.branch for snap in snapshots]

    if branch:
        snapshot = await snapshot_repository.get_for_branch(db, repository.id, branch)
        if snapshot is None:
            raise NotFoundError(f"Branch '{branch}' not found")
        return snapshot, available, branch

    if repository.default_branch:
        snapshot = await snapshot_repository.get_for_branch(
            db, repository.id, repository.default_branch
        )
        if snapshot:
            return snapshot, available, repository.default_branch

    if snapshots:
        snapshot = snapshots[0]
        return snapshot, available, snapshot.branch

    return None, available, None


async def _build_branch_summary(db, snapshot) -> BranchSummaryResponse:
    stats = await repository_stats_repository.get_stats_for_snapshot(db, snapshot.id)
    return BranchSummaryResponse(
        branch=snapshot.branch,
        commit_hash=snapshot.commit_hash,
        files_count=stats.files_count,
        classes_count=stats.classes_count,
        functions_count=stats.functions_count,
        methods_count=stats.methods_count,
        dependencies_count=stats.dependencies_count,
    )


async def get_job_status(db: AsyncSession, *, job_id: UUID, user_id: UUID) -> JobStatusResponse:
    job = await job_repository.get_by_id_for_user(db, job_id, user_id)
    if job is None:
        raise NotFoundError("Job not found")

    events = await job_event_repository.list_for_job(db, job.id)
    return JobStatusResponse(
        id=job.id,
        status=_map_job_status(job.status),
        progress=int(job.progress),
        current_stage=job.current_stage,
        error_message=job.error_message,
        events=[
            JobEventItem(message=event.message, created_at=event.created_at) for event in events
        ],
    )


async def _build_summary(
    db: AsyncSession,
    repository,
    *,
    branch: str | None = None,
) -> RepositorySummaryResponse:
    analysis_status = await repository_stats_repository.get_latest_job_status(db, repository.id)
    snapshot, available_branches, selected_branch = await _resolve_snapshot(db, repository, branch)

    stats = (
        await repository_stats_repository.get_stats_for_snapshot(db, snapshot.id)
        if snapshot
        else None
    )

    return RepositorySummaryResponse(
        id=repository.id,
        owner=repository.owner,
        repository_name=repository.repository_name,
        github_url=repository.repo_url,
        latest_commit_hash=snapshot.commit_hash if snapshot else repository.latest_commit_hash,
        default_branch=repository.default_branch,
        status=repository.status.value,
        analysis_status=analysis_status,
        files_count=stats.files_count if stats else 0,
        classes_count=stats.classes_count if stats else 0,
        functions_count=stats.functions_count if stats else 0,
        methods_count=stats.methods_count if stats else 0,
        dependencies_count=stats.dependencies_count if stats else 0,
        branches_count=repository.branches_analyzed_count,
        branches_truncated=repository.branches_truncated,
        available_branches=available_branches,
    )


async def list_user_repositories(
    db: AsyncSession,
    *,
    user_id: UUID,
) -> list[RepositoryListItem]:
    repositories = await repository_repository.get_by_user_id(db, user_id)
    items: list[RepositoryListItem] = []

    for repository in repositories:
        summary = await _build_summary(db, repository)
        items.append(
            RepositoryListItem(
                id=summary.id,
                owner=summary.owner,
                repository_name=summary.repository_name,
                github_url=summary.github_url,
                latest_commit_hash=summary.latest_commit_hash,
                default_branch=summary.default_branch,
                status=summary.status,
                analysis_status=summary.analysis_status,
                files_count=summary.files_count,
                branches_count=repository.branches_analyzed_count,
                branches_truncated=repository.branches_truncated,
                updated_at=repository.updated_at.isoformat(),
            )
        )

    return items


async def list_repository_branches(
    db: AsyncSession,
    *,
    repository_id: UUID,
    user_id: UUID,
) -> list[BranchSummaryResponse]:
    repository = await repository_repository.get_by_id_for_user(db, repository_id, user_id)
    if repository is None:
        raise NotFoundError("Repository not found")

    snapshots = await snapshot_repository.list_for_repository(db, repository.id)
    summaries: list[BranchSummaryResponse] = []
    for snapshot in snapshots:
        summaries.append(await _build_branch_summary(db, snapshot))
    return summaries


async def get_repository_summary(
    db: AsyncSession,
    *,
    repository_id: UUID,
    user_id: UUID,
    branch: str | None = None,
) -> RepositorySummaryResponse:
    repository = await repository_repository.get_by_id_for_user(db, repository_id, user_id)
    if repository is None:
        raise NotFoundError("Repository not found")

    return await _build_summary(db, repository, branch=branch)


async def get_repository_detail(
    db: AsyncSession,
    *,
    repository_id: UUID,
    user_id: UUID,
    branch: str | None = None,
) -> RepositoryDetailResponse:
    repository = await repository_repository.get_by_id_for_user(db, repository_id, user_id)
    if repository is None:
        raise NotFoundError("Repository not found")

    summary = await _build_summary(db, repository, branch=branch)
    snapshot, _, selected_branch = await _resolve_snapshot(
        db, repository, branch or summary.default_branch
    )

    files: list[FileItem] = []
    symbols: list[SymbolItem] = []
    dependencies: list[DependencyItem] = []

    if snapshot:
        file_records = await repository_detail_repository.list_by_snapshot(db, snapshot.id)
        files = [
            FileItem(
                id=file.id,
                relative_path=file.relative_path,
                file_name=file.file_name,
                extension=file.extension,
                language=file.language,
                size_bytes=file.size_bytes,
                is_binary=file.is_binary,
            )
            for file in file_records
        ]

        symbol_rows = await repository_detail_repository.list_symbols_by_snapshot(db, snapshot.id)
        symbols = [
            SymbolItem(
                symbol_name=symbol.symbol_name,
                symbol_type=symbol.symbol_type.value,
                file_path=file_path,
                start_line=symbol.start_line,
                end_line=symbol.end_line,
                signature=symbol.signature,
            )
            for symbol, file_path in symbol_rows
        ]

        dependency_rows = await repository_detail_repository.list_dependencies_by_snapshot(
            db, snapshot.id
        )
        dependencies = [
            DependencyItem(
                source_path=source_path,
                target_path=target_path,
                dependency_type=edge.dependency_type.value,
            )
            for edge, source_path, target_path in dependency_rows
        ]

    return RepositoryDetailResponse(
        **summary.model_dump(),
        selected_branch=selected_branch,
        files=files,
        symbols=symbols,
        dependencies=dependencies,
    )


async def delete_repository(
    db: AsyncSession,
    *,
    repository_id: UUID,
    user_id: UUID,
) -> None:
    deleted = await repository_repository.delete_for_user(db, repository_id, user_id)
    if not deleted:
        raise NotFoundError("Repository not found")
    await db.commit()


async def delete_all_repositories(db: AsyncSession, *, user_id: UUID) -> int:
    count = await repository_repository.delete_all_for_user(db, user_id)
    await db.commit()
    return count
