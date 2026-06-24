from app.utils.search_highlight import (
    build_content_snippet,
    highlight_terms,
    sanitize_headline,
)


def test_sanitize_headline_converts_b_tags():
    assert sanitize_headline("hello <b>world</b>") == "hello <mark>world</mark>"


def test_sanitize_headline_preserves_mark_tags():
    assert sanitize_headline("hello <mark>world</mark>") == "hello <mark>world</mark>"


def test_build_content_snippet_finds_query():
    content = "def create_user(data):\n    return User(data)\n"
    snippet = build_content_snippet(content, "create_user")
    assert "create_user" in snippet or "<mark>" in snippet


def test_build_content_snippet_truncates_long_content():
    content = "x" * 1000
    snippet = build_content_snippet(content, "missing", max_len=100)
    assert len(snippet) <= 110


def test_highlight_terms_wraps_matches():
    result = highlight_terms("authenticate user", "authenticate")
    assert "<mark>authenticate</mark>" in result
