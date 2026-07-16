from app.repositories.search_repository import _filter_clauses


def test_filter_clauses_empty_by_default():
    sql, params = _filter_clauses()
    assert sql == ""
    assert params == {}


def test_filter_clauses_include_branch_path_type_and_language():
    sql, params = _filter_clauses(
        branch_name="main",
        file_path="src/",
        chunk_type="function",
        language="Python",
    )
    assert "c.branch_name = :branch_name" in sql
    assert "c.file_path LIKE :file_path_prefix" in sql
    assert "c.chunk_type::text = :chunk_type" in sql
    assert "lower(f.language) = lower(:language)" in sql
    assert params == {
        "branch_name": "main",
        "file_path_prefix": "src/%",
        "chunk_type": "function",
        "language": "Python",
    }


def test_filter_clauses_ignore_blank_optional_filters():
    sql, params = _filter_clauses(file_path="  ", chunk_type="", language="   ")
    assert sql == ""
    assert params == {}
