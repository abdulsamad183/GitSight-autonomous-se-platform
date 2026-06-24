from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.pull_request import PullRequestState
from app.models.repository import RepositoryStatus
from app.models.user import User
from app.repositories import pull_request_repository, repository_repository
from app.utils.github import GitHubPullRequestDraft


@pytest.fixture
async def repository_record():
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        connect_args={"statement_cache_size": 0},
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    suffix = uuid4().hex[:8]
    async with session_factory() as db:
        user = User(
            username=f"prsyncuser_{suffix}",
            email=f"prsync_{suffix}@example.com",
            hashed_password=hash_password("securepass123"),
        )
        db.add(user)
        await db.flush()

        repository = await repository_repository.create(
            db,
            user_id=user.id,
            name="octocat/Hello-World",
            repo_url="https://github.com/octocat/Hello-World",
            owner="octocat",
            repository_name="Hello-World",
            status=RepositoryStatus.ACTIVE,
        )
        await db.commit()
        records = (user.id, repository.id, session_factory)

    yield records

    user_id, repository_id, _ = records
    async with session_factory() as db:
        repository = await repository_repository.get_by_id_for_user(db, repository_id, user_id)
        if repository:
            await db.delete(repository)
        user = await db.get(User, user_id)
        if user:
            await db.delete(user)
        await db.commit()

    await engine.dispose()


def _draft(
    *,
    github_pr_id: int = 1001,
    number: int = 12,
    state: PullRequestState = PullRequestState.OPEN,
    title: str = "Initial title",
    is_merged: bool = False,
) -> GitHubPullRequestDraft:
    now = datetime.now(timezone.utc)
    return GitHubPullRequestDraft(
        github_pr_id=github_pr_id,
        number=number,
        title=title,
        description="Description",
        state=state,
        author_username="octocat",
        source_branch="feature/pr",
        target_branch="main",
        github_created_at=now,
        github_updated_at=now,
        github_closed_at=now if state != PullRequestState.OPEN else None,
        github_merged_at=now if is_merged else None,
        is_draft=False,
        is_merged=is_merged,
        html_url=f"https://github.com/octocat/Hello-World/pull/{number}",
    )


@pytest.mark.asyncio
async def test_pull_request_upsert_updates_existing_and_inserts_new(repository_record):
    _, repository_id, session_factory = repository_record

    async with session_factory() as db:
        synced_at = datetime.now(timezone.utc)
        await pull_request_repository.upsert_many(
            db,
            repository_id=repository_id,
            pull_requests=[_draft()],
            synced_at=synced_at,
        )
        await db.commit()

        await pull_request_repository.upsert_many(
            db,
            repository_id=repository_id,
            pull_requests=[
                _draft(
                    state=PullRequestState.MERGED,
                    title="Merged title",
                    is_merged=True,
                ),
                _draft(github_pr_id=1002, number=13, title="New PR"),
            ],
            synced_at=datetime.now(timezone.utc),
        )
        await db.commit()

        records = await pull_request_repository.list_for_repository(db, repository_id)
        assert [record.number for record in records] == [13, 12]

        updated = next(record for record in records if record.number == 12)
        assert updated.title == "Merged title"
        assert updated.state == PullRequestState.MERGED
        assert updated.is_merged is True

        counts = await pull_request_repository.count_by_state(db, repository_id)
        assert counts.total == 2
        assert counts.open == 1
        assert counts.merged == 1


@pytest.mark.asyncio
async def test_pull_request_sync_preserves_missing_historical_records(repository_record):
    _, repository_id, session_factory = repository_record

    async with session_factory() as db:
        await pull_request_repository.upsert_many(
            db,
            repository_id=repository_id,
            pull_requests=[_draft(github_pr_id=1001, number=12)],
            synced_at=datetime.now(timezone.utc),
        )
        await db.commit()

        await pull_request_repository.upsert_many(
            db,
            repository_id=repository_id,
            pull_requests=[],
            synced_at=datetime.now(timezone.utc),
        )
        await db.commit()

        records = await pull_request_repository.list_for_repository(db, repository_id)
        assert len(records) == 1
        assert records[0].number == 12
