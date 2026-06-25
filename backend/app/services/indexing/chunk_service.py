import logging
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models.code_chunk import ChunkType, CodeChunk
from app.models.symbol import Symbol, SymbolType
from app.repositories import (
    code_chunk_repository,
    file_repository,
    snapshot_repository,
    symbol_repository,
)
from app.schemas.chunk import ChunkCreate
from app.utils.file_chunker import chunk_css_file, chunk_markdown_file, chunk_text_file
from app.utils.file_filter import CHUNKABLE_FILE_EXTENSIONS, DOCUMENT_CHUNK_EXTENSIONS
from app.utils.source_extractor import compute_content_hash, extract_lines

logger = logging.getLogger(__name__)

CHUNKABLE_SYMBOL_TYPES = {
    SymbolType.FUNCTION,
    SymbolType.METHOD,
    SymbolType.CLASS,
    SymbolType.INTERFACE,
    SymbolType.ENUM,
}


@dataclass
class ChunkGenerationStats:
    total_chunks: int
    chunk_type_distribution: dict[str, int]
    chunk_generation_time_seconds: float


def _symbol_type_to_chunk_type(symbol_type: SymbolType) -> ChunkType:
    return ChunkType(symbol_type.value)


class ChunkService:
    def __init__(self, db: AsyncSession, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()

    def create_chunk(
        self,
        *,
        symbol: Symbol,
        file_path: str,
        source: bytes,
        branch_name: str,
        repository_id: UUID,
        head_commit_hash: str,
        parent_symbol: str | None = None,
    ) -> ChunkCreate | None:
        if symbol.symbol_type not in CHUNKABLE_SYMBOL_TYPES:
            return None

        content = extract_lines(source, symbol.start_line, symbol.end_line)
        if not content.strip():
            return None

        return ChunkCreate(
            repository_id=repository_id,
            branch_name=branch_name,
            file_path=file_path,
            chunk_type=_symbol_type_to_chunk_type(symbol.symbol_type).value,
            symbol_name=symbol.symbol_name,
            parent_symbol=parent_symbol,
            start_line=symbol.start_line,
            end_line=symbol.end_line,
            content=content,
            content_hash=compute_content_hash(content),
            chunk_source="symbol",
            head_commit_hash=head_commit_hash,
        )

    def _file_chunks_for_path(
        self,
        *,
        file_path: str,
        extension: str | None,
        content: str,
        repository_id: UUID,
        branch_name: str,
        head_commit_hash: str,
    ) -> list[ChunkCreate]:
        if extension in DOCUMENT_CHUNK_EXTENSIONS:
            drafts = chunk_markdown_file(
                file_path=file_path,
                content=content,
                max_section_lines=self.settings.file_chunk_max_lines,
                whole_file_max_lines=self.settings.file_chunk_whole_file_max_lines,
            )
        elif extension == ".css":
            drafts = chunk_css_file(
                file_path=file_path,
                content=content,
                max_section_lines=self.settings.file_chunk_max_lines,
                whole_file_max_lines=self.settings.file_chunk_whole_file_max_lines,
            )
        else:
            drafts = chunk_text_file(
                file_path=file_path,
                content=content,
                max_section_lines=self.settings.file_chunk_max_lines,
                whole_file_max_lines=self.settings.file_chunk_whole_file_max_lines,
            )

        return [
            ChunkCreate(
                repository_id=repository_id,
                branch_name=branch_name,
                file_path=file_path,
                chunk_type=draft.chunk_type,
                symbol_name=draft.symbol_name,
                parent_symbol=None,
                start_line=draft.start_line,
                end_line=draft.end_line,
                content=draft.content,
                content_hash=draft.content_hash,
                chunk_source=draft.chunk_source,
                head_commit_hash=head_commit_hash,
            )
            for draft in drafts
        ]

    async def create_chunks(
        self,
        *,
        repository_id: UUID,
        branch_name: str,
        clone_path: Path,
        head_commit_hash: str,
        only_new_files: bool = False,
    ) -> tuple[ChunkGenerationStats, list[CodeChunk]]:
        start = time.perf_counter()

        snapshot = await snapshot_repository.get_for_branch(self.db, repository_id, branch_name)
        if snapshot is None:
            return ChunkGenerationStats(0, {}, 0.0), []

        existing_files: set[str] = set()
        if only_new_files:
            existing_files = await code_chunk_repository.list_chunked_file_paths(
                self.db,
                repository_id=repository_id,
                branch_name=branch_name,
            )

        symbol_rows = await symbol_repository.list_for_snapshot_with_files(
            self.db, snapshot_id=snapshot.id
        )

        chunks_by_file: dict[str, list[tuple[Symbol, str | None]]] = {}
        for symbol, file in symbol_rows:
            if symbol.symbol_type not in CHUNKABLE_SYMBOL_TYPES:
                continue
            if only_new_files and file.relative_path in existing_files:
                continue
            parent_name = symbol.parent.symbol_name if symbol.parent else None
            chunks_by_file.setdefault(file.relative_path, []).append((symbol, parent_name))

        chunk_creates: list[ChunkCreate] = []
        for file_path, symbols in chunks_by_file.items():
            absolute_path = clone_path / file_path
            try:
                source = absolute_path.read_bytes()
            except OSError:
                logger.warning("Failed to read %s for chunking", file_path)
                continue

            for symbol, parent_name in symbols:
                draft = self.create_chunk(
                    symbol=symbol,
                    file_path=file_path,
                    source=source,
                    branch_name=branch_name,
                    repository_id=repository_id,
                    head_commit_hash=head_commit_hash,
                    parent_symbol=parent_name,
                )
                if draft is not None:
                    chunk_creates.append(draft)

        file_records = await file_repository.list_for_snapshot(self.db, snapshot_id=snapshot.id)
        for file_record in file_records:
            if file_record.is_binary:
                continue
            if only_new_files and file_record.relative_path in existing_files:
                continue
            extension = (file_record.extension or "").lower()
            if extension not in CHUNKABLE_FILE_EXTENSIONS:
                continue

            absolute_path = clone_path / file_record.relative_path
            try:
                text = absolute_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                logger.warning("Failed to read %s for file chunking", file_record.relative_path)
                continue

            chunk_creates.extend(
                self._file_chunks_for_path(
                    file_path=file_record.relative_path,
                    extension=extension,
                    content=text,
                    repository_id=repository_id,
                    branch_name=branch_name,
                    head_commit_hash=head_commit_hash,
                )
            )

        _, needing_embedding = await code_chunk_repository.bulk_upsert(
            self.db, chunks=chunk_creates
        )

        elapsed = time.perf_counter() - start
        distribution = dict(Counter(item.chunk_type for item in chunk_creates))
        stats = ChunkGenerationStats(
            total_chunks=len(chunk_creates),
            chunk_type_distribution=distribution,
            chunk_generation_time_seconds=elapsed,
        )
        logger.info(
            "Created %d chunks for repository %s branch %s "
            "(distribution: %s, only_new_files=%s) in %.2fs",
            stats.total_chunks,
            repository_id,
            branch_name,
            stats.chunk_type_distribution,
            only_new_files,
            stats.chunk_generation_time_seconds,
        )
        return stats, needing_embedding

    async def get_chunk(self, chunk_id: UUID) -> CodeChunk | None:
        return await code_chunk_repository.get_by_id(self.db, chunk_id)

    async def get_chunks_by_repository(
        self,
        repository_id: UUID,
        *,
        branch_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[CodeChunk], int]:
        return await code_chunk_repository.list_by_repository(
            self.db,
            repository_id=repository_id,
            branch_name=branch_name,
            limit=limit,
            offset=offset,
        )

    async def get_chunks_by_file(
        self,
        repository_id: UUID,
        file_path: str,
        *,
        branch_name: str | None = None,
    ) -> list[CodeChunk]:
        return await code_chunk_repository.list_by_file(
            self.db,
            repository_id=repository_id,
            file_path=file_path,
            branch_name=branch_name,
        )

    async def delete_chunks(self, repository_id: UUID) -> None:
        await code_chunk_repository.delete_for_repository(self.db, repository_id)
