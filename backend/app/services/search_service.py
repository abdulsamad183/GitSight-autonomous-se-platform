import logging
import time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.repositories import code_chunk_repository, search_repository
from app.repositories.search_repository import SearchRow
from app.schemas.search import RetrievalContextItem, SearchResponse, SearchResult
from app.services.indexing.embedding_service import EmbeddingService
from app.utils.search_highlight import build_content_snippet, highlight_terms, sanitize_headline

logger = logging.getLogger(__name__)

VALID_MODES = frozenset({"keyword", "semantic", "hybrid"})


class SearchService:
    def __init__(self, db: AsyncSession, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self._embedding_service = EmbeddingService(db, self.settings)

    def _row_to_result(
        self,
        row: SearchRow,
        *,
        query: str,
        keyword_score: float | None = None,
        semantic_score: float | None = None,
        final_score: float | None = None,
        prefer_keyword_snippet: bool = False,
    ) -> SearchResult:
        symbol_name = sanitize_headline(row.symbol_name)
        if "<mark>" not in symbol_name:
            symbol_name = highlight_terms(row.symbol_name, query)

        if prefer_keyword_snippet and row.content_snippet:
            content_snippet = sanitize_headline(row.content_snippet)
        elif row.keyword_score is not None and row.content_snippet:
            content_snippet = sanitize_headline(row.content_snippet)
        else:
            content_snippet = build_content_snippet(row.content, query)

        return SearchResult(
            chunk_id=row.chunk_id,
            symbol_name=symbol_name,
            file_path=row.file_path,
            chunk_type=row.chunk_type,
            content_snippet=content_snippet,
            keyword_score=keyword_score,
            semantic_score=semantic_score,
            final_score=final_score,
            start_line=row.start_line,
            end_line=row.end_line,
            branch_name=row.branch_name,
        )

    async def keyword_search(
        self,
        repository_id: UUID,
        query: str,
        *,
        limit: int | None = None,
        offset: int = 0,
        branch: str | None = None,
    ) -> list[SearchResult]:
        limit = limit or self.settings.search_default_limit
        rows = await search_repository.keyword_search(
            self.db,
            repository_id=repository_id,
            query=query,
            limit=limit,
            offset=offset,
            branch_name=branch,
        )
        return [
            self._row_to_result(
                row,
                query=query,
                keyword_score=row.keyword_score,
                final_score=row.keyword_score,
                prefer_keyword_snippet=True,
            )
            for row in rows
        ]

    async def semantic_search(
        self,
        repository_id: UUID,
        query: str,
        *,
        limit: int | None = None,
        offset: int = 0,
        branch: str | None = None,
        threshold: float | None = None,
    ) -> list[SearchResult]:
        limit = limit or self.settings.search_default_limit
        threshold = (
            threshold if threshold is not None else self.settings.search_similarity_threshold
        )
        query_vector = self._embedding_service.generate_embedding(query)
        rows = await search_repository.semantic_search(
            self.db,
            repository_id=repository_id,
            query_vector=query_vector,
            limit=limit,
            offset=offset,
            threshold=threshold,
            branch_name=branch,
        )
        return [
            self._row_to_result(
                row,
                query=query,
                semantic_score=row.semantic_score,
                final_score=row.semantic_score,
            )
            for row in rows
        ]

    def _merge_hybrid_results(
        self,
        keyword_rows: list[SearchRow],
        semantic_rows: list[SearchRow],
        query: str,
    ) -> list[SearchResult]:
        merged: dict[UUID, dict] = {}

        max_keyword = max((r.keyword_score or 0.0 for r in keyword_rows), default=0.0)

        for row in keyword_rows:
            norm_kw = (row.keyword_score or 0.0) / max_keyword if max_keyword > 0 else 0.0
            merged[row.chunk_id] = {
                "row": row,
                "keyword_score": norm_kw,
                "semantic_score": 0.0,
                "has_keyword_snippet": True,
            }

        for row in semantic_rows:
            sem_score = row.semantic_score or 0.0
            if row.chunk_id in merged:
                merged[row.chunk_id]["semantic_score"] = sem_score
                if not merged[row.chunk_id]["has_keyword_snippet"]:
                    merged[row.chunk_id]["row"] = row
            else:
                merged[row.chunk_id] = {
                    "row": row,
                    "keyword_score": 0.0,
                    "semantic_score": sem_score,
                    "has_keyword_snippet": False,
                }

        kw_weight = self.settings.search_keyword_weight
        sem_weight = self.settings.search_semantic_weight

        results: list[SearchResult] = []
        for entry in merged.values():
            final = entry["keyword_score"] * kw_weight + entry["semantic_score"] * sem_weight
            results.append(
                self._row_to_result(
                    entry["row"],
                    query=query,
                    keyword_score=entry["keyword_score"],
                    semantic_score=entry["semantic_score"],
                    final_score=final,
                    prefer_keyword_snippet=entry["has_keyword_snippet"],
                )
            )

        results.sort(key=lambda r: r.final_score or 0.0, reverse=True)
        return results

    async def hybrid_search(
        self,
        repository_id: UUID,
        query: str,
        *,
        limit: int | None = None,
        offset: int = 0,
        branch: str | None = None,
    ) -> list[SearchResult]:
        limit = limit or self.settings.search_default_limit
        candidate_limit = limit * self.settings.search_candidate_multiplier

        query_vector = self._embedding_service.generate_embedding(query)
        keyword_rows = await search_repository.keyword_search(
            self.db,
            repository_id=repository_id,
            query=query,
            limit=candidate_limit,
            offset=0,
            branch_name=branch,
        )
        semantic_rows = await search_repository.semantic_search(
            self.db,
            repository_id=repository_id,
            query_vector=query_vector,
            limit=candidate_limit,
            offset=0,
            threshold=self.settings.search_similarity_threshold,
            branch_name=branch,
        )

        merged = self._merge_hybrid_results(keyword_rows, semantic_rows, query)
        return merged[offset : offset + limit]

    async def search(
        self,
        repository_id: UUID,
        query: str,
        *,
        mode: str = "hybrid",
        limit: int | None = None,
        offset: int = 0,
        branch: str | None = None,
    ) -> SearchResponse:
        if mode not in VALID_MODES:
            raise ValueError(f"Invalid search mode: {mode}")

        limit = min(limit or self.settings.search_default_limit, self.settings.search_max_limit)
        start = time.perf_counter()

        if mode == "keyword":
            results = await self.keyword_search(
                repository_id, query, limit=limit, offset=offset, branch=branch
            )
            total = await search_repository.keyword_search_count(
                self.db,
                repository_id=repository_id,
                query=query,
                branch_name=branch,
            )
        elif mode == "semantic":
            results = await self.semantic_search(
                repository_id, query, limit=limit, offset=offset, branch=branch
            )
            query_vector = self._embedding_service.generate_embedding(query)
            total = await search_repository.semantic_search_count(
                self.db,
                repository_id=repository_id,
                query_vector=query_vector,
                threshold=self.settings.search_similarity_threshold,
                branch_name=branch,
            )
        else:
            results = await self.hybrid_search(
                repository_id, query, limit=limit, offset=offset, branch=branch
            )
            # For hybrid, total is approximate from merged candidate pool
            total = len(results) if offset == 0 else len(results) + offset

        elapsed_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "search_completed",
            extra={
                "search_type": mode,
                "query": query,
                "repository_id": str(repository_id),
                "result_count": len(results),
                "execution_time_ms": round(elapsed_ms, 2),
            },
        )

        return SearchResponse(
            query=query,
            mode=mode,
            total_results=total,
            limit=limit,
            offset=offset,
            execution_time_ms=round(elapsed_ms, 2),
            results=results,
        )

    async def retrieve_context(
        self,
        repository_id: UUID,
        query: str,
        top_k: int = 5,
        *,
        branch: str | None = None,
    ) -> list[RetrievalContextItem]:
        results = await self.hybrid_search(
            repository_id, query, limit=top_k, offset=0, branch=branch
        )
        if not results:
            return []

        chunk_ids = [r.chunk_id for r in results]
        chunks = await code_chunk_repository.get_by_ids(self.db, chunk_ids=chunk_ids)
        chunk_map = {chunk.id: chunk for chunk in chunks}

        items: list[RetrievalContextItem] = []
        for result in results:
            chunk = chunk_map.get(result.chunk_id)
            content = chunk.content if chunk is not None else ""
            items.append(
                RetrievalContextItem(
                    symbol_name=result.symbol_name.replace("<mark>", "").replace("</mark>", ""),
                    file_path=result.file_path,
                    chunk_type=result.chunk_type,
                    content=content,
                    branch_name=result.branch_name,
                    base_commit_hash=chunk.base_commit_hash if chunk else None,
                    head_commit_hash=chunk.head_commit_hash if chunk else None,
                    change_type=chunk.change_type.value if chunk and chunk.change_type else None,
                )
            )
        return items
