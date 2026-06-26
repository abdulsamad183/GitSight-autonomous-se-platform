from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pr_review import PrReview


async def get_by_pull_request(
    db: AsyncSession,
    *,
    repository_id: UUID,
    pull_request_id: UUID,
) -> PrReview | None:
    result = await db.execute(
        select(PrReview).where(
            PrReview.repository_id == repository_id,
            PrReview.pull_request_id == pull_request_id,
        )
    )
    return result.scalar_one_or_none()


async def upsert(
    db: AsyncSession,
    *,
    repository_id: UUID,
    pull_request_id: UUID,
    title: str,
    content: str,
) -> PrReview:
    now = datetime.now(timezone.utc)
    stmt = (
        insert(PrReview)
        .values(
            repository_id=repository_id,
            pull_request_id=pull_request_id,
            title=title,
            content=content,
            generated_at=now,
        )
        .on_conflict_do_update(
            constraint="uq_pr_reviews_repo_pr",
            set_={
                "title": title,
                "content": content,
                "generated_at": now,
            },
        )
        .returning(PrReview)
    )
    result = await db.execute(stmt)
    review = result.scalar_one()
    await db.flush()
    return review


async def delete_by_pull_request(
    db: AsyncSession,
    *,
    repository_id: UUID,
    pull_request_id: UUID,
) -> None:
    await db.execute(
        delete(PrReview).where(
            PrReview.repository_id == repository_id,
            PrReview.pull_request_id == pull_request_id,
        )
    )
    await db.flush()
