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


def _branch_clause(branch_name: str | None) -> tuple[str, dict]:
    if branch_name is None:
        return "", {}
    return " AND c.branch_name = :branch_name", {"branch_name": branch_name}


async def keyword_search(
    db: AsyncSession,
    *,
    repository_id: UUID,
    query: str,
    limit: int,
    offset: int,
    branch_name: str | None = None,
) -> list[SearchRow]:
    branch_sql, branch_params = _branch_clause(branch_name)
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
          {branch_sql}
        ORDER BY keyword_score DESC
        LIMIT :limit OFFSET :offset
        """)
    params = {
        "repository_id": repository_id,
        "query": query,
        "limit": limit,
        "offset": offset,
        **branch_params,
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
) -> int:
    branch_sql, branch_params = _branch_clause(branch_name)
    sql = text(f"""
        SELECT count(*) AS total
        FROM code_chunks c
        WHERE c.repository_id = :repository_id
          AND c.search_vector @@ plainto_tsquery('simple', :query)
          {branch_sql}
        """)
    params = {"repository_id": repository_id, "query": query, **branch_params}
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
) -> list[SearchRow]:
    branch_sql, branch_params = _branch_clause(branch_name)
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
          {branch_sql}
        ORDER BY e.embedding <=> CAST(:query_vector AS vector)
        LIMIT :limit OFFSET :offset
        """)
    params = {
        "repository_id": repository_id,
        "query_vector": vector_literal,
        "threshold": threshold,
        "limit": limit,
        "offset": offset,
        **branch_params,
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
) -> int:
    branch_sql, branch_params = _branch_clause(branch_name)
    vector_literal = "[" + ",".join(str(v) for v in query_vector) + "]"
    sql = text(f"""
        SELECT count(*) AS total
        FROM code_chunks c
        INNER JOIN chunk_embeddings e ON e.chunk_id = c.id
        WHERE c.repository_id = :repository_id
          AND (1 - (e.embedding <=> CAST(:query_vector AS vector))) >= :threshold
          {branch_sql}
        """)
    params = {
        "repository_id": repository_id,
        "query_vector": vector_literal,
        "threshold": threshold,
        **branch_params,
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
