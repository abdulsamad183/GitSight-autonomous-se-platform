from app.utils.source_extractor import compute_content_hash, extract_lines


def test_extract_lines_preserves_formatting():
    source = b"def foo():\n    return 1\n\ndef bar():\n    pass\n"
    result = extract_lines(source, 1, 2)
    assert result == "def foo():\n    return 1\n"


def test_extract_lines_single_line():
    source = b"line one\nline two\nline three\n"
    result = extract_lines(source, 2, 2)
    assert result == "line two\n"


def test_extract_lines_invalid_range():
    source = b"hello\n"
    assert extract_lines(source, 0, 1) == ""
    assert extract_lines(source, 5, 6) == ""
    assert extract_lines(source, 2, 1) == ""


def test_compute_content_hash_is_deterministic():
    content = "def create_user(user_data):\n    pass\n"
    assert compute_content_hash(content) == compute_content_hash(content)
    assert len(compute_content_hash(content)) == 64
