import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository import IndexingStatus
from app.repositories import (
    chunk_embedding_repository,
    code_chunk_repository,
    repository_repository,
)
from app.services.analysis.job_tracker import STAGE_INDEXING_CHUNKS, STAGE_INDEXING_EMBEDDINGS
from app.services.indexing.chunk_service import ChunkService
from app.services.indexing.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class RepositoryIndexingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.chunk_service = ChunkService(db)
        self.embedding_service = EmbeddingService(db)

    async def index_repository(
        self,
        *,
        repository_id: UUID,
        clone_path: Path,
        branches: list[str],
        tracker=None,
    ) -> None:
        repository = await repository_repository.get_by_id(self.db, repository_id)
        if repository is None:
            logger.error("Repository %s not found for indexing", repository_id)
            return

        started_at = datetime.now(timezone.utc)
        start_perf = time.perf_counter()

        await repository_repository.update_indexing_status(
            self.db,
            repository,
            indexing_status=IndexingStatus.PROCESSING,
            indexing_started_at=started_at,
            indexing_completed_at=None,
            indexing_duration_seconds=None,
        )
        await self.db.commit()

        try:
            all_needing_embedding = []

            for branch in branches:
                if tracker is not None:
                    await tracker.set_stage(STAGE_INDEXING_CHUNKS)

                await code_chunk_repository.delete_for_branch(
                    self.db,
                    repository_id=repository_id,
                    branch_name=branch,
                )

                _, needing_embedding = await self.chunk_service.create_chunks(
                    repository_id=repository_id,
                    branch_name=branch,
                    clone_path=clone_path,
                )
                all_needing_embedding.extend(needing_embedding)
                await self.db.commit()

            if tracker is not None:
                await tracker.set_stage(STAGE_INDEXING_EMBEDDINGS)

            if all_needing_embedding:
                await self.embedding_service.embed_chunks(all_needing_embedding)
            else:
                missing = await code_chunk_repository.list_chunks_needing_embedding(
                    self.db, repository_id=repository_id
                )
                if missing:
                    await self.embedding_service.embed_chunks(missing)

            await self.db.commit()

            total_chunks = await code_chunk_repository.count_by_repository(self.db, repository_id)
            embedded_chunks = await chunk_embedding_repository.count_for_repository(
                self.db, repository_id
            )
            duration = time.perf_counter() - start_perf
            completed_at = datetime.now(timezone.utc)

            await repository_repository.update_indexing_status(
                self.db,
                repository,
                indexing_status=IndexingStatus.COMPLETED,
                total_chunks=total_chunks,
                embedded_chunks=embedded_chunks,
                indexing_completed_at=completed_at,
                indexing_duration_seconds=duration,
            )
            await self.db.commit()

            logger.info(
                "Indexing completed for repository %s: %d chunks, %d embedded in %.1fs",
                repository_id,
                total_chunks,
                embedded_chunks,
                duration,
            )
        except Exception as exc:
            logger.exception("Indexing failed for repository %s: %s", repository_id, exc)
            await self.db.rollback()
            repository = await repository_repository.get_by_id(self.db, repository_id)
            if repository is not None:
                await repository_repository.update_indexing_status(
                    self.db,
                    repository,
                    indexing_status=IndexingStatus.FAILED,
                    indexing_duration_seconds=time.perf_counter() - start_perf,
                )
                await self.db.commit()
