from uuid import uuid4

from app.repositories.search_repository import SearchRow
from app.services.search_service import SearchService


def _make_row(
    *,
    symbol_name: str = "create_user",
    keyword_score: float | None = None,
    semantic_score: float | None = None,
    content: str = "def create_user():\n    pass\n",
) -> SearchRow:
    return SearchRow(
        chunk_id=uuid4(),
        symbol_name=symbol_name,
        file_path="services/user.py",
        chunk_type="function",
        content_snippet=content[:200],
        content=content,
        keyword_score=keyword_score,
        semantic_score=semantic_score,
        start_line=1,
        end_line=2,
        branch_name="main",
    )


def test_merge_hybrid_deduplicates_by_chunk_id():
    service = SearchService(db=None)  # type: ignore[arg-type]
    shared_id = uuid4()
    kw_row = _make_row(keyword_score=0.8)
    kw_row.chunk_id = shared_id
    sem_row = _make_row(semantic_score=0.9)
    sem_row.chunk_id = shared_id

    results = service._merge_hybrid_results([kw_row], [sem_row], "create_user")
    assert len(results) == 1
    assert results[0].keyword_score is not None
    assert results[0].semantic_score is not None
    assert results[0].final_score is not None


def test_merge_hybrid_sorts_by_final_score():
    service = SearchService(db=None)  # type: ignore[arg-type]
    high = _make_row(symbol_name="high", keyword_score=1.0)
    low = _make_row(symbol_name="low", keyword_score=0.1)

    results = service._merge_hybrid_results([low, high], [], "test")
    assert results[0].symbol_name.replace("<mark>", "").replace("</mark>", "") == "high"


def test_merge_hybrid_uses_configurable_weights():
    from app.core.config import Settings

    settings = Settings(search_keyword_weight=1.0, search_semantic_weight=0.0)
    service = SearchService(db=None, settings=settings)  # type: ignore[arg-type]
    kw_row = _make_row(keyword_score=0.5)
    sem_row = _make_row(semantic_score=1.0)

    results = service._merge_hybrid_results([kw_row], [sem_row], "test")
    kw_only = [r for r in results if r.chunk_id == kw_row.chunk_id][0]
    assert kw_only.final_score == kw_only.keyword_score
