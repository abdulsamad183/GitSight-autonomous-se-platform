import json
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.models.code_chunk import ChunkType
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.chunk import ChunkListResponse, ChunkResponse, IndexStatusResponse, ReindexResponse
from app.schemas.documentation import DocumentationListResponse, DocumentationResponse
from app.schemas.graph import RepositoryGraphResponse
from app.schemas.pr_review import PullRequestReviewResponse
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
from app.schemas.search import SearchResponse
from app.services import analysis_service, indexing_service, repository_detail_service
from app.services.ai.context_builder import ContextBuilder
from app.services.ai.engine import AIEngine
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.providers.factory import get_llm_provider
from app.services.ai.repository_chat_service import RepositoryChatService
from app.services.ai.tools.executor import ToolExecutor
from app.services.ai.tools.factory import build_default_tool_registry
from app.services.ai.tools.planner import LLMToolPlanner
from app.services.documentation.service import DocumentationService, parse_document_type
from app.services.exceptions import (
    ConflictError,
    ForbiddenError,
    LLMProviderError,
    NotFoundError,
    ToolPlannerError,
    ValidationError,
)
from app.services.graph import repository_graph_service
from app.services.indexing.chunk_service import ChunkService
from app.services.pr_review.service import PullRequestReviewService
from app.services.search_service import SearchService

router = APIRouter()


def _build_ai_engine(db: AsyncSession, settings: Settings) -> AIEngine:
    registry = build_default_tool_registry(db, settings)
    prompt_builder = PromptBuilder()
    llm_provider = get_llm_provider(settings)
    planner = LLMToolPlanner(registry, prompt_builder, llm_provider, settings)
    executor = ToolExecutor(registry, settings)
    context_builder = ContextBuilder(settings)
    return AIEngine(
        db,
        planner,
        executor,
        context_builder,
        prompt_builder,
        llm_provider,
        settings,
    )


def _build_chat_service(db: AsyncSession, settings: Settings) -> RepositoryChatService:
    return RepositoryChatService(db, _build_ai_engine(db, settings), settings)


def _build_documentation_service(db: AsyncSession, settings: Settings) -> DocumentationService:
    return DocumentationService(db, _build_ai_engine(db, settings), settings)


def _build_pr_review_service(db: AsyncSession, settings: Settings) -> PullRequestReviewService:
    return PullRequestReviewService(db, _build_ai_engine(db, settings), settings)


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
        chunk_source=chunk.chunk_source.value,
        base_commit_hash=chunk.base_commit_hash,
        head_commit_hash=chunk.head_commit_hash,
        change_type=chunk.change_type.value if chunk.change_type else None,
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


@router.get(
    "/{repository_id}/pull-requests/{pull_request_id}/review",
    response_model=PullRequestReviewResponse,
)
async def get_pull_request_review(
    repository_id: UUID,
    pull_request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> PullRequestReviewResponse:
    review_service = _build_pr_review_service(db, settings)
    try:
        return await review_service.get_review(
            repository_id=repository_id,
            user_id=current_user.id,
            pull_request_id=pull_request_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except LLMProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


@router.post(
    "/{repository_id}/pull-requests/{pull_request_id}/review/regenerate",
    response_model=PullRequestReviewResponse,
)
async def regenerate_pull_request_review(
    repository_id: UUID,
    pull_request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> PullRequestReviewResponse:
    review_service = _build_pr_review_service(db, settings)
    try:
        return await review_service.regenerate(
            repository_id=repository_id,
            user_id=current_user.id,
            pull_request_id=pull_request_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except LLMProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


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


@router.get("/{repository_id}/search", response_model=SearchResponse)
async def search_repository(
    repository_id: UUID,
    q: str,
    mode: str = "hybrid",
    limit: int | None = None,
    offset: int = 0,
    branch: str | None = None,
    file_path: str | None = None,
    chunk_type: str | None = None,
    language: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> SearchResponse:
    if not q or not q.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty")

    if mode not in {"keyword", "semantic", "hybrid"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mode must be keyword, semantic, or hybrid",
        )

    if chunk_type is not None and chunk_type.strip():
        valid_chunk_types = {item.value for item in ChunkType}
        if chunk_type.strip() not in valid_chunk_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"chunk_type must be one of: {', '.join(sorted(valid_chunk_types))}",
            )

    try:
        await repository_detail_service.get_repository_or_raise(
            db, repository_id=repository_id, user_id=current_user.id
        )
        effective_limit = min(
            limit or settings.search_default_limit,
            settings.search_max_limit,
        )
        search_service = SearchService(db, settings)
        return await search_service.search(
            repository_id,
            q.strip(),
            mode=mode,
            limit=effective_limit,
            offset=offset,
            branch=branch,
            file_path=file_path.strip() if file_path and file_path.strip() else None,
            chunk_type=chunk_type.strip() if chunk_type and chunk_type.strip() else None,
            language=language.strip() if language and language.strip() else None,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{repository_id}/chat", response_model=ChatResponse)
async def chat_repository(
    repository_id: UUID,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    chat_service = _build_chat_service(db, settings)
    try:
        if body.stream:

            async def event_generator():
                async for payload in chat_service.stream_answer(
                    repository_id=repository_id,
                    user_id=current_user.id,
                    message=body.message,
                    branch=body.branch,
                ):
                    yield f"data: {json.dumps(payload)}\n\n"

            return StreamingResponse(event_generator(), media_type="text/event-stream")

        return await chat_service.answer(
            repository_id=repository_id,
            user_id=current_user.id,
            message=body.message,
            branch=body.branch,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except LLMProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except ToolPlannerError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


@router.get("/{repository_id}/documentation", response_model=DocumentationListResponse)
async def list_repository_documentation(
    repository_id: UUID,
    branch: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> DocumentationListResponse:
    doc_service = _build_documentation_service(db, settings)
    try:
        return await doc_service.list_types(
            repository_id=repository_id,
            user_id=current_user.id,
            branch=branch,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{repository_id}/documentation/{document_type}", response_model=DocumentationResponse)
async def get_repository_documentation(
    repository_id: UUID,
    document_type: str,
    branch: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> DocumentationResponse:
    doc_service = _build_documentation_service(db, settings)
    try:
        parsed_type = parse_document_type(document_type)
        return await doc_service.get_document(
            repository_id=repository_id,
            user_id=current_user.id,
            document_type=parsed_type,
            branch=branch,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except LLMProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


@router.post(
    "/{repository_id}/documentation/{document_type}/regenerate",
    response_model=DocumentationResponse,
)
async def regenerate_repository_documentation(
    repository_id: UUID,
    document_type: str,
    branch: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> DocumentationResponse:
    doc_service = _build_documentation_service(db, settings)
    try:
        parsed_type = parse_document_type(document_type)
        return await doc_service.regenerate(
            repository_id=repository_id,
            user_id=current_user.id,
            document_type=parsed_type,
            branch=branch,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except LLMProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


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
