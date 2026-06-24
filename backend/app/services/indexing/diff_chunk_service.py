"""Parse git unified diffs into embeddable chunk drafts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import UUID

from git import Repo

from app.schemas.chunk import ChunkCreate
from app.utils.source_extractor import compute_content_hash

DIFF_FILE_HEADER = re.compile(r"^diff --git a/(.*) b/(.*)$")
HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


@dataclass(frozen=True)
class DiffFileState:
    old_path: str | None
    new_path: str | None
    change_type: str


def _resolve_merge_base(repo: Repo, default_commit: str, branch_commit: str) -> str:
    try:
        merge_base = repo.git.merge_base(default_commit, branch_commit).strip()
        if merge_base:
            return merge_base
    except Exception:
        pass
    return default_commit


def _parse_diff_files(diff_text: str) -> list[tuple[DiffFileState, list[str]]]:
    if not diff_text.strip():
        return []

    sections: list[tuple[DiffFileState, list[str]]] = []
    current_state: DiffFileState | None = None
    current_lines: list[str] = []

    for line in diff_text.splitlines():
        file_match = DIFF_FILE_HEADER.match(line)
        if file_match:
            if current_state is not None:
                sections.append((current_state, current_lines))
            old_path = file_match.group(1)
            new_path = file_match.group(2)
            if old_path == "/dev/null":
                change_type = "add"
                path = new_path
            elif new_path == "/dev/null":
                change_type = "delete"
                path = old_path
            else:
                change_type = "modify"
                path = new_path
            current_state = DiffFileState(old_path=old_path, new_path=path, change_type=change_type)
            current_lines = [line]
            continue

        if current_state is not None:
            current_lines.append(line)

    if current_state is not None:
        sections.append((current_state, current_lines))

    return sections


def _split_file_into_hunks(lines: list[str]) -> list[tuple[int, int, list[str]]]:
    hunks: list[tuple[int, int, list[str]]] = []
    current_hunk: list[str] = []
    new_start = 1
    new_end = 1

    for line in lines:
        hunk_match = HUNK_HEADER.match(line)
        if hunk_match:
            if current_hunk:
                hunks.append((new_start, new_end, current_hunk))
            new_start = int(hunk_match.group(3))
            new_count = int(hunk_match.group(4) or "1")
            new_end = new_start + max(new_count, 1) - 1
            current_hunk = [line]
            continue
        if current_hunk:
            current_hunk.append(line)

    if current_hunk:
        hunks.append((new_start, new_end, current_hunk))

    return hunks


def build_diff_chunks(
    repo: Repo,
    *,
    repository_id: UUID,
    branch_name: str,
    default_commit: str,
    branch_commit: str,
    max_diff_bytes: int = 500_000,
) -> list[ChunkCreate]:
    merge_base = _resolve_merge_base(repo, default_commit, branch_commit)
    if merge_base == branch_commit:
        return []

    diff_text = repo.git.diff(merge_base, branch_commit, unified=3)
    encoded = diff_text.encode("utf-8")
    if len(encoded) > max_diff_bytes:
        diff_text = encoded[:max_diff_bytes].decode("utf-8", errors="ignore")
        diff_text += "\n... [diff truncated]"

    chunks: list[ChunkCreate] = []
    for file_state, file_lines in _parse_diff_files(diff_text):
        file_path = file_state.new_path or file_state.old_path or "unknown"
        for new_start, new_end, hunk_lines in _split_file_into_hunks(file_lines):
            content = "\n".join(hunk_lines)
            if not content.strip():
                continue
            symbol_name = f"diff:{file_path}:@@{new_start}"
            chunks.append(
                ChunkCreate(
                    repository_id=repository_id,
                    branch_name=branch_name,
                    file_path=file_path,
                    chunk_type="diff_hunk",
                    symbol_name=symbol_name,
                    parent_symbol=None,
                    start_line=new_start,
                    end_line=new_end,
                    content=content,
                    content_hash=compute_content_hash(content),
                    chunk_source="diff_hunk",
                    base_commit_hash=merge_base,
                    head_commit_hash=branch_commit,
                    change_type=file_state.change_type,
                )
            )

    return chunks
