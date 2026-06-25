"""Line-window and file-based chunking for HTML, CSS, markdown, and other text files."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.utils.source_extractor import compute_content_hash

MARKDOWN_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")


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


def _markdown_heading_title(line: str) -> str | None:
    match = MARKDOWN_HEADING_RE.match(line.rstrip("\r\n"))
    if not match:
        return None
    return match.group(2).strip()


def _split_markdown_sections(
    *,
    file_path: str,
    lines: list[str],
) -> list[FileChunkDraft]:
    """Split markdown on ATX headings (# .. ######)."""
    has_heading = any(_markdown_heading_title(line) is not None for line in lines)
    if not has_heading:
        return []

    drafts: list[FileChunkDraft] = []
    current_heading: str | None = None
    current_lines: list[str] = []
    start_line = 1

    def flush(end_line: int) -> None:
        nonlocal current_lines
        if not current_lines:
            return
        body = "".join(current_lines)
        if not body.strip():
            current_lines = []
            return
        symbol_name = f"{file_path}#{current_heading}" if current_heading else file_path
        drafts.append(
            FileChunkDraft(
                chunk_type="section" if current_heading else "file",
                chunk_source="section" if current_heading else "file",
                symbol_name=symbol_name,
                start_line=start_line,
                end_line=end_line,
                content=body,
                content_hash=compute_content_hash(body),
            )
        )
        current_lines = []

    for line_number, line in enumerate(lines, start=1):
        heading = _markdown_heading_title(line)
        if heading is not None:
            flush(line_number - 1)
            current_heading = heading
            start_line = line_number
            current_lines = [line]
        else:
            if not current_lines:
                start_line = line_number
            current_lines.append(line)

    flush(len(lines))
    return drafts


def _subdivide_large_draft(
    draft: FileChunkDraft,
    *,
    max_section_lines: int,
) -> list[FileChunkDraft]:
    line_count = _line_count(draft.content)
    if line_count <= max_section_lines:
        return [draft]

    lines = draft.content.splitlines(keepends=True)
    subdivided: list[FileChunkDraft] = []
    offset = draft.start_line
    start = 1
    while start <= line_count:
        end = min(start + max_section_lines - 1, line_count)
        section = "".join(lines[start - 1 : end])
        subdivided.append(
            FileChunkDraft(
                chunk_type="section",
                chunk_source="section",
                symbol_name=f"{draft.symbol_name}:L{offset + start - 1}-{offset + end - 1}",
                start_line=offset + start - 1,
                end_line=offset + end - 1,
                content=section,
                content_hash=compute_content_hash(section),
            )
        )
        start = end + 1
    return subdivided


def chunk_markdown_file(
    *,
    file_path: str,
    content: str,
    max_section_lines: int = 120,
    whole_file_max_lines: int = 200,
) -> list[FileChunkDraft]:
    """Chunk markdown/reStructuredText by headings, with line-window fallback."""
    lines = content.splitlines(keepends=True)
    total_lines = len(lines)
    if total_lines == 0:
        return []

    heading_sections = _split_markdown_sections(file_path=file_path, lines=lines)
    if heading_sections:
        drafts: list[FileChunkDraft] = []
        for section in heading_sections:
            if _line_count(section.content) > max_section_lines:
                drafts.extend(_subdivide_large_draft(section, max_section_lines=max_section_lines))
            else:
                drafts.append(section)
        return drafts

    return chunk_text_file(
        file_path=file_path,
        content=content,
        max_section_lines=max_section_lines,
        whole_file_max_lines=whole_file_max_lines,
    )
