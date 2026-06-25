from pathlib import Path

IGNORED_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".next",
    "venv",
    "__pycache__",
    "target",
    "out",
}

LANGUAGE_BY_EXTENSION: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".go": "go",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hh": "cpp",
    ".hxx": "cpp",
    ".md": "markdown",
    ".mdx": "markdown",
    ".rst": "restructuredtext",
}

PARSEABLE_LANGUAGES = {"python", "javascript", "typescript", "go", "c", "cpp"}

FILE_CHUNK_EXTENSIONS = {".html", ".htm", ".css"}
DOCUMENT_CHUNK_EXTENSIONS = {".md", ".mdx", ".rst"}
CHUNKABLE_FILE_EXTENSIONS = FILE_CHUNK_EXTENSIONS | DOCUMENT_CHUNK_EXTENSIONS


def detect_language(extension: str | None) -> str | None:
    if not extension:
        return None
    return LANGUAGE_BY_EXTENSION.get(extension.lower())


def should_skip_dir(dirname: str) -> bool:
    return dirname in IGNORED_DIRS


def should_skip_file(file_name: str) -> bool:
    return file_name == ".env"


def is_binary_content(sample: bytes) -> bool:
    return b"\x00" in sample


def is_too_large(size_bytes: int, max_size_bytes: int) -> bool:
    return size_bytes > max_size_bytes


def read_binary_sample(path: Path, sample_size: int = 8192) -> bytes:
    with path.open("rb") as handle:
        return handle.read(sample_size)


def is_parseable_file(extension: str | None, language: str | None, is_binary: bool) -> bool:
    if is_binary:
        return False
    if language is None:
        return False
    return language in PARSEABLE_LANGUAGES
