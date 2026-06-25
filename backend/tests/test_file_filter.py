from app.utils.file_filter import (
    detect_language,
    is_binary_content,
    is_parseable_file,
    is_too_large,
    should_skip_dir,
    should_skip_file,
)


def test_should_skip_dir():
    assert should_skip_dir("node_modules")
    assert not should_skip_dir("src")


def test_should_skip_file():
    assert should_skip_file(".env")
    assert not should_skip_file("main.py")


def test_detect_language():
    assert detect_language(".py") == "python"
    assert detect_language(".tsx") == "typescript"
    assert detect_language(".go") == "go"
    assert detect_language(".c") == "c"
    assert detect_language(".cpp") == "cpp"
    assert detect_language(".hpp") == "cpp"
    assert detect_language(".md") == "markdown"
    assert detect_language(".mdx") == "markdown"
    assert detect_language(".rst") == "restructuredtext"
    assert detect_language(".xyz") is None


def test_is_binary_content():
    assert is_binary_content(b"hello\x00world")
    assert not is_binary_content(b"print('ok')")


def test_is_too_large():
    assert is_too_large(2_000_000, 1_048_576)
    assert not is_too_large(100, 1_048_576)


def test_is_parseable_file():
    assert is_parseable_file(".py", "python", False)
    assert is_parseable_file(".go", "go", False)
    assert is_parseable_file(".c", "c", False)
    assert is_parseable_file(".cpp", "cpp", False)
    assert not is_parseable_file(".py", "python", True)
    assert not is_parseable_file(".md", None, False)
