"""Line-window and file-based chunking for HTML, CSS, and other text files."""

from __future__ import annotations

from dataclasses import dataclass

from app.utils.source_extractor import compute_content_hash


@dataclass(frozen=True)
class FileChunkDraft:
    chunk_type: str
    chunk_source: str
    symbol_name: str
    start_line: int
    end_line: int
    content: str
    content_hash: str


def _line_count(text: str) -> int:
    if not text:
        return 0
    return len(text.splitlines())


def chunk_text_file(
    *,
    file_path: str,
    content: str,
    max_section_lines: int = 120,
    whole_file_max_lines: int = 200,
) -> list[FileChunkDraft]:
    """Split a text file into whole-file or section chunks."""
    lines = content.splitlines(keepends=True)
    total_lines = len(lines)
    if total_lines == 0:
        return []

    if total_lines <= whole_file_max_lines:
        body = "".join(lines)
        return [
            FileChunkDraft(
                chunk_type="file",
                chunk_source="file",
                symbol_name=file_path,
                start_line=1,
                end_line=total_lines,
                content=body,
                content_hash=compute_content_hash(body),
            )
        ]

    drafts: list[FileChunkDraft] = []
    start = 1
    while start <= total_lines:
        end = min(start + max_section_lines - 1, total_lines)
        section = "".join(lines[start - 1 : end])
        drafts.append(
            FileChunkDraft(
                chunk_type="section",
                chunk_source="section",
                symbol_name=f"{file_path}:L{start}-{end}",
                start_line=start,
                end_line=end,
                content=section,
                content_hash=compute_content_hash(section),
            )
        )
        start = end + 1

    return drafts


def chunk_css_file(
    *,
    file_path: str,
    content: str,
    max_section_lines: int = 120,
    whole_file_max_lines: int = 200,
) -> list[FileChunkDraft]:
    """Chunk CSS by rule blocks when possible, otherwise fall back to line windows."""
    if _line_count(content) <= whole_file_max_lines:
        return chunk_text_file(
            file_path=file_path,
            content=content,
            max_section_lines=max_section_lines,
            whole_file_max_lines=whole_file_max_lines,
        )

    drafts: list[FileChunkDraft] = []
    current: list[str] = []
    start_line = 1
    line_number = 0
    brace_depth = 0

    for line in content.splitlines(keepends=True):
        line_number += 1
        current.append(line)
        brace_depth += line.count("{") - line.count("}")

        if brace_depth <= 0 and current:
            body = "".join(current)
            if body.strip():
                drafts.append(
                    FileChunkDraft(
                        chunk_type="section",
                        chunk_source="section",
                        symbol_name=f"{file_path}:L{start_line}-{line_number}",
                        start_line=start_line,
                        end_line=line_number,
                        content=body,
                        content_hash=compute_content_hash(body),
                    )
                )
            current = []
            start_line = line_number + 1
            brace_depth = 0

    if current:
        body = "".join(current)
        if body.strip():
            drafts.append(
                FileChunkDraft(
                    chunk_type="section",
                    chunk_source="section",
                    symbol_name=f"{file_path}:L{start_line}-{line_number}",
                    start_line=start_line,
                    end_line=line_number,
                    content=body,
                    content_hash=compute_content_hash(body),
                )
            )

    if drafts:
        return drafts

    return chunk_text_file(
        file_path=file_path,
        content=content,
        max_section_lines=max_section_lines,
        whole_file_max_lines=whole_file_max_lines,
    )
