from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.chunk import ChunkListResponse, ChunkResponse, IndexStatusResponse, ReindexResponse
from app.schemas.graph import RepositoryGraphResponse
from app.schemas.repository import (
    AnalyzeRequest,
    AnalyzeResponse,
    BranchSummaryResponse,
    DeleteAllResponse,
    PullRequestDetailItem,
    RepositoryDetailResponse,
    RepositoryListItem,
    RepositorySummaryResponse,
)
from app.services import analysis_service, indexing_service, repository_detail_service
from app.services.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.services.graph import repository_graph_service
from app.services.indexing.chunk_service import ChunkService

router = APIRouter()


def _chunk_to_response(chunk) -> ChunkResponse:
    return ChunkResponse(
        id=chunk.id,
        repository_id=chunk.repository_id,
        branch_name=chunk.branch_name,
        file_path=chunk.file_path,
        chunk_type=chunk.chunk_type.value,
        symbol_name=chunk.symbol_name,
        parent_symbol=chunk.parent_symbol,
        start_line=chunk.start_line,
        end_line=chunk.end_line,
        content=chunk.content,
        content_hash=chunk.content_hash,
        created_at=chunk.created_at,
        updated_at=chunk.updated_at,
    )


@router.get("", response_model=list[RepositoryListItem])
async def list_repositories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RepositoryListItem]:
    return await repository_detail_service.list_user_repositories(db, user_id=current_user.id)


@router.delete("", response_model=DeleteAllResponse)
async def clear_all_repositories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeleteAllResponse:
    deleted_count = await repository_detail_service.delete_all_repositories(
        db, user_id=current_user.id
    )
    return DeleteAllResponse(deleted_count=deleted_count)


@router.post("/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_repository(
    data: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> AnalyzeResponse:
    try:
        return await analysis_service.start_analysis(
            db,
            user_id=current_user.id,
            github_url=data.github_url,
            settings=settings,
            background_tasks=background_tasks,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post(
    "/{repository_id}/refresh",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def refresh_repository(
    repository_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyzeResponse:
    try:
        return await analysis_service.start_refresh(
            db,
            user_id=current_user.id,
            repository_id=repository_id,
            background_tasks=background_tasks,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{repository_id}", response_model=RepositorySummaryResponse)
async def get_repository(
    repository_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RepositorySummaryResponse:
    try:
        return await repository_detail_service.get_repository_summary(
            db,
            repository_id=repository_id,
            user_id=current_user.id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{repository_id}/branches", response_model=list[BranchSummaryResponse])
async def list_repository_branches(
    repository_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BranchSummaryResponse]:
    try:
        return await repository_detail_service.list_repository_branches(
            db,
            repository_id=repository_id,
            user_id=current_user.id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{repository_id}/pull-requests", response_model=list[PullRequestDetailItem])
async def list_repository_pull_requests(
    repository_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PullRequestDetailItem]:
    try:
        return await repository_detail_service.list_repository_pull_requests(
            db,
            repository_id=repository_id,
            user_id=current_user.id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{repository_id}/graph", response_model=RepositoryGraphResponse)
async def get_repository_graph(
    repository_id: UUID,
    branch: str | None = None,
    type: str = "structure",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RepositoryGraphResponse:
    try:
        return await repository_graph_service.get_repository_graph(
            db,
            repository_id=repository_id,
            user_id=current_user.id,
            branch=branch,
            graph_type=type,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{repository_id}/details", response_model=RepositoryDetailResponse)
async def get_repository_details(
    repository_id: UUID,
    branch: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RepositoryDetailResponse:
    try:
        return await repository_detail_service.get_repository_detail(
            db,
            repository_id=repository_id,
            user_id=current_user.id,
            branch=branch,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{repository_id}/chunks", response_model=ChunkListResponse)
async def list_repository_chunks(
    repository_id: UUID,
    branch: str | None = None,
    file_path: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChunkListResponse:
    repository = await repository_detail_service.get_repository_or_raise(
        db, repository_id=repository_id, user_id=current_user.id
    )
    chunk_service = ChunkService(db)
    if file_path is not None:
        chunks = await chunk_service.get_chunks_by_file(
            repository.id,
            file_path,
            branch_name=branch,
        )
        total = len(chunks)
        chunks = chunks[offset : offset + limit]
    else:
        chunks, total = await chunk_service.get_chunks_by_repository(
            repository.id,
            branch_name=branch,
            limit=limit,
            offset=offset,
        )

    return ChunkListResponse(
        items=[_chunk_to_response(chunk) for chunk in chunks],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{repository_id}/chunks/{chunk_id}", response_model=ChunkResponse)
async def get_repository_chunk(
    repository_id: UUID,
    chunk_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChunkResponse:
    await repository_detail_service.get_repository_or_raise(
        db, repository_id=repository_id, user_id=current_user.id
    )
    chunk = await ChunkService(db).get_chunk(chunk_id)
    if chunk is None or chunk.repository_id != repository_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
    return _chunk_to_response(chunk)


@router.get("/{repository_id}/index-status", response_model=IndexStatusResponse)
async def get_repository_index_status(
    repository_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IndexStatusResponse:
    try:
        status_data = await indexing_service.get_index_status(
            db,
            repository_id=repository_id,
            user_id=current_user.id,
        )
        return IndexStatusResponse(**status_data)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{repository_id}/reindex",
    response_model=ReindexResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def reindex_repository(
    repository_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReindexResponse:
    try:
        repo_id, job_id = await indexing_service.start_reindex(
            db,
            repository_id=repository_id,
            user_id=current_user.id,
        )
        from app.services.indexing_service import run_indexing_job

        background_tasks.add_task(run_indexing_job, job_id)
        return ReindexResponse(repository_id=repo_id, job_id=job_id, status="PENDING")
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repository_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        await repository_detail_service.delete_repository(
            db,
            repository_id=repository_id,
            user_id=current_user.id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
