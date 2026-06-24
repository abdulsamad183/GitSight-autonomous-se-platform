from app.services.indexing.repository_indexing_service import resolve_indexing_plan


def test_resolve_indexing_plan_initial_ingest():
    full, diff = resolve_indexing_plan(
        branches=["main", "gh-pages"],
        default_branch="main",
        updated_branches=None,
    )
    assert full == ["main"]
    assert diff == ["gh-pages"]


def test_resolve_indexing_plan_default_branch_updated_on_refresh():
    full, diff = resolve_indexing_plan(
        branches=["main", "feature", "gh-pages"],
        default_branch="main",
        updated_branches=["main"],
    )
    assert full == ["main"]
    assert diff == ["feature", "gh-pages"]


def test_resolve_indexing_plan_secondary_branch_updated_on_refresh():
    full, diff = resolve_indexing_plan(
        branches=["main", "feature"],
        default_branch="main",
        updated_branches=["feature"],
    )
    assert full == []
    assert diff == ["feature"]
