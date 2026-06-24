from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.repository import Repository
from app.repositories import pull_request_repository
from app.services.analysis.job_tracker import (
    STAGE_DISCOVERING_PRS,
    STAGE_SYNCING_PRS,
    JobTracker,
)
from app.utils.github import fetch_repository_pull_requests


@dataclass(frozen=True)
class PullRequestSyncResult:
    discovered: int
    upserted: int


async def sync_pull_requests(
    db: AsyncSession,
    *,
    repository: Repository,
    settings: Settings,
    tracker: JobTracker,
) -> PullRequestSyncResult:
    await tracker.set_stage(STAGE_DISCOVERING_PRS)
    pull_requests = await fetch_repository_pull_requests(
        repository.owner,
        repository.repository_name,
        settings,
    )

    await tracker.set_stage(STAGE_SYNCING_PRS)
    synced_at = datetime.now(timezone.utc)
    upserted = await pull_request_repository.upsert_many(
        db,
        repository_id=repository.id,
        pull_requests=pull_requests,
        synced_at=synced_at,
    )
    await db.commit()

    await tracker.set_message(
        f"Synchronized {len(pull_requests)} pull requests",
        progress=93,
    )
    return PullRequestSyncResult(discovered=len(pull_requests), upserted=upserted)
