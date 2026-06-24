import hashlib


def extract_lines(source: bytes, start_line: int, end_line: int) -> str:
    """Extract a 1-based inclusive line range, preserving formatting."""
    if start_line < 1 or end_line < start_line:
        return ""

    text = source.decode("utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    if start_line > len(lines):
        return ""

    selected = lines[start_line - 1 : end_line]
    return "".join(selected)


def compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
