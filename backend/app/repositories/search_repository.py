from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class SearchRow:
    chunk_id: UUID
    symbol_name: str
    file_path: str
    chunk_type: str
    content_snippet: str
    content: str
    keyword_score: float | None
    semantic_score: float | None
    start_line: int
    end_line: int
    branch_name: str


def _filter_clauses(
    *,
    branch_name: str | None = None,
    file_path: str | None = None,
    chunk_type: str | None = None,
    language: str | None = None,
) -> tuple[str, dict]:
    clauses: list[str] = []
    params: dict = {}

    if branch_name is not None:
        clauses.append(" AND c.branch_name = :branch_name")
        params["branch_name"] = branch_name

    if file_path is not None and file_path.strip():
        clauses.append(" AND c.file_path LIKE :file_path_prefix")
        params["file_path_prefix"] = f"{file_path.strip()}%"

    if chunk_type is not None and chunk_type.strip():
        clauses.append(" AND c.chunk_type::text = :chunk_type")
        params["chunk_type"] = chunk_type.strip()

    if language is not None and language.strip():
        clauses.append("""
          AND EXISTS (
            SELECT 1
            FROM files f
            JOIN repository_snapshots rs ON rs.id = f.snapshot_id
            WHERE f.repository_id = c.repository_id
              AND f.relative_path = c.file_path
              AND rs.branch = c.branch_name
              AND lower(f.language) = lower(:language)
          )
            """)
        params["language"] = language.strip()

    return "".join(clauses), params


async def keyword_search(
    db: AsyncSession,
    *,
    repository_id: UUID,
    query: str,
    limit: int,
    offset: int,
    branch_name: str | None = None,
    file_path: str | None = None,
    chunk_type: str | None = None,
    language: str | None = None,
) -> list[SearchRow]:
    filter_sql, filter_params = _filter_clauses(
        branch_name=branch_name,
        file_path=file_path,
        chunk_type=chunk_type,
        language=language,
    )
    sql = text(f"""
        SELECT
            c.id AS chunk_id,
            ts_headline(
                'simple',
                c.symbol_name,
                plainto_tsquery('simple', :query),
                'StartSel=<mark>, StopSel=</mark>, MaxFragments=1, MaxWords=20'
            ) AS symbol_name,
            c.file_path,
            c.chunk_type::text AS chunk_type,
            ts_headline(
                'simple',
                c.content,
                plainto_tsquery('simple', :query),
                'StartSel=<mark>, StopSel=</mark>, MaxFragments=2, MaxWords=30, MinWords=10'
            ) AS content_snippet,
            c.content,
            ts_rank_cd(c.search_vector, plainto_tsquery('simple', :query)) AS keyword_score,
            c.start_line,
            c.end_line,
            c.branch_name
        FROM code_chunks c
        WHERE c.repository_id = :repository_id
          AND c.search_vector @@ plainto_tsquery('simple', :query)
          {filter_sql}
        ORDER BY keyword_score DESC
        LIMIT :limit OFFSET :offset
        """)
    params = {
        "repository_id": repository_id,
        "query": query,
        "limit": limit,
        "offset": offset,
        **filter_params,
    }
    result = await db.execute(sql, params)
    return [
        SearchRow(
            chunk_id=row.chunk_id,
            symbol_name=row.symbol_name,
            file_path=row.file_path,
            chunk_type=row.chunk_type,
            content_snippet=row.content_snippet,
            content=row.content,
            keyword_score=float(row.keyword_score),
            semantic_score=None,
            start_line=row.start_line,
            end_line=row.end_line,
            branch_name=row.branch_name,
        )
        for row in result.all()
    ]


async def keyword_search_count(
    db: AsyncSession,
    *,
    repository_id: UUID,
    query: str,
    branch_name: str | None = None,
    file_path: str | None = None,
    chunk_type: str | None = None,
    language: str | None = None,
) -> int:
    filter_sql, filter_params = _filter_clauses(
        branch_name=branch_name,
        file_path=file_path,
        chunk_type=chunk_type,
        language=language,
    )
    sql = text(f"""
        SELECT count(*) AS total
        FROM code_chunks c
        WHERE c.repository_id = :repository_id
          AND c.search_vector @@ plainto_tsquery('simple', :query)
          {filter_sql}
        """)
    params = {"repository_id": repository_id, "query": query, **filter_params}
    result = await db.execute(sql, params)
    return int(result.scalar_one())


async def semantic_search(
    db: AsyncSession,
    *,
    repository_id: UUID,
    query_vector: list[float],
    limit: int,
    offset: int,
    threshold: float,
    branch_name: str | None = None,
    file_path: str | None = None,
    chunk_type: str | None = None,
    language: str | None = None,
) -> list[SearchRow]:
    filter_sql, filter_params = _filter_clauses(
        branch_name=branch_name,
        file_path=file_path,
        chunk_type=chunk_type,
        language=language,
    )
    vector_literal = "[" + ",".join(str(v) for v in query_vector) + "]"
    sql = text(f"""
        SELECT
            c.id AS chunk_id,
            c.symbol_name,
            c.file_path,
            c.chunk_type::text AS chunk_type,
            left(c.content, 500) AS content_snippet,
            c.content,
            (1 - (e.embedding <=> CAST(:query_vector AS vector))) AS semantic_score,
            c.start_line,
            c.end_line,
            c.branch_name
        FROM code_chunks c
        INNER JOIN chunk_embeddings e ON e.chunk_id = c.id
        WHERE c.repository_id = :repository_id
          AND (1 - (e.embedding <=> CAST(:query_vector AS vector))) >= :threshold
          {filter_sql}
        ORDER BY e.embedding <=> CAST(:query_vector AS vector)
        LIMIT :limit OFFSET :offset
        """)
    params = {
        "repository_id": repository_id,
        "query_vector": vector_literal,
        "threshold": threshold,
        "limit": limit,
        "offset": offset,
        **filter_params,
    }
    result = await db.execute(sql, params)
    return [
        SearchRow(
            chunk_id=row.chunk_id,
            symbol_name=row.symbol_name,
            file_path=row.file_path,
            chunk_type=row.chunk_type,
            content_snippet=row.content_snippet,
            content=row.content,
            keyword_score=None,
            semantic_score=float(row.semantic_score),
            start_line=row.start_line,
            end_line=row.end_line,
            branch_name=row.branch_name,
        )
        for row in result.all()
    ]


async def semantic_search_count(
    db: AsyncSession,
    *,
    repository_id: UUID,
    query_vector: list[float],
    threshold: float,
    branch_name: str | None = None,
    file_path: str | None = None,
    chunk_type: str | None = None,
    language: str | None = None,
) -> int:
    filter_sql, filter_params = _filter_clauses(
        branch_name=branch_name,
        file_path=file_path,
        chunk_type=chunk_type,
        language=language,
    )
    vector_literal = "[" + ",".join(str(v) for v in query_vector) + "]"
    sql = text(f"""
        SELECT count(*) AS total
        FROM code_chunks c
        INNER JOIN chunk_embeddings e ON e.chunk_id = c.id
        WHERE c.repository_id = :repository_id
          AND (1 - (e.embedding <=> CAST(:query_vector AS vector))) >= :threshold
          {filter_sql}
        """)
    params = {
        "repository_id": repository_id,
        "query_vector": vector_literal,
        "threshold": threshold,
        **filter_params,
    }
    result = await db.execute(sql, params)
    return int(result.scalar_one())


async def get_chunks_content_by_ids(
    db: AsyncSession,
    *,
    chunk_ids: list[UUID],
) -> dict[UUID, str]:
    if not chunk_ids:
        return {}
    sql = text("""
        SELECT id, content
        FROM code_chunks
        WHERE id = ANY(:chunk_ids)
        """)
    result = await db.execute(sql, {"chunk_ids": chunk_ids})
    return {row.id: row.content for row in result.all()}
