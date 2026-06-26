from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pull_request import PullRequest, PullRequestState
from app.utils.github import GitHubPullRequestDraft


@dataclass(frozen=True)
class PullRequestCounts:
    total: int = 0
    open: int = 0
    closed: int = 0
    merged: int = 0


async def upsert_many(
    db: AsyncSession,
    *,
    repository_id: UUID,
    pull_requests: list[GitHubPullRequestDraft],
    synced_at: datetime,
) -> int:
    if not pull_requests:
        return 0

    values = [
        {
            "repository_id": repository_id,
            "github_pr_id": item.github_pr_id,
            "number": item.number,
            "title": item.title,
            "description": item.description,
            "state": item.state,
            "author_username": item.author_username,
            "source_branch": item.source_branch,
            "target_branch": item.target_branch,
            "github_created_at": item.github_created_at,
            "github_updated_at": item.github_updated_at,
            "github_closed_at": item.github_closed_at,
            "github_merged_at": item.github_merged_at,
            "is_draft": item.is_draft,
            "is_merged": item.is_merged,
            "html_url": item.html_url,
            "last_synced_at": synced_at,
        }
        for item in pull_requests
    ]

    statement = insert(PullRequest).values(values)
    excluded = statement.excluded
    statement = statement.on_conflict_do_update(
        index_elements=[PullRequest.repository_id, PullRequest.github_pr_id],
        set_={
            "number": excluded.number,
            "title": excluded.title,
            "description": excluded.description,
            "state": excluded.state,
            "author_username": excluded.author_username,
            "source_branch": excluded.source_branch,
            "target_branch": excluded.target_branch,
            "github_created_at": excluded.github_created_at,
            "github_updated_at": excluded.github_updated_at,
            "github_closed_at": excluded.github_closed_at,
            "github_merged_at": excluded.github_merged_at,
            "is_draft": excluded.is_draft,
            "is_merged": excluded.is_merged,
            "html_url": excluded.html_url,
            "last_synced_at": excluded.last_synced_at,
            "updated_at": func.now(),
        },
    )
    result = await db.execute(statement)
    return result.rowcount or 0


async def list_for_repository(db: AsyncSession, repository_id: UUID) -> list[PullRequest]:
    result = await db.execute(
        select(PullRequest)
        .where(PullRequest.repository_id == repository_id)
        .order_by(PullRequest.number.desc())
    )
    return list(result.scalars().all())


async def get_by_id_for_repository(
    db: AsyncSession,
    *,
    repository_id: UUID,
    pull_request_id: UUID,
) -> PullRequest | None:
    result = await db.execute(
        select(PullRequest).where(
            PullRequest.repository_id == repository_id,
            PullRequest.id == pull_request_id,
        )
    )
    return result.scalar_one_or_none()


async def count_by_state(db: AsyncSession, repository_id: UUID) -> PullRequestCounts:
    result = await db.execute(
        select(PullRequest.state, func.count())
        .where(PullRequest.repository_id == repository_id)
        .group_by(PullRequest.state)
    )
    counts = {state: count for state, count in result.all()}
    return PullRequestCounts(
        total=sum(counts.values()),
        open=counts.get(PullRequestState.OPEN, 0),
        closed=counts.get(PullRequestState.CLOSED, 0),
        merged=counts.get(PullRequestState.MERGED, 0),
    )
