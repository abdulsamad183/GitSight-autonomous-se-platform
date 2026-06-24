from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.job import JobStatus, JobType
from app.models.repository import Repository, RepositoryStatus
from app.models.user import User
from app.repositories import (
    job_event_repository,
    job_repository,
    repository_repository,
    snapshot_repository,
)
from app.services.analysis.repository_analyzer import RepositoryAnalyzer
from app.services.analysis.repository_cloner import CloneResult
from app.services.exceptions import AnalysisError


@pytest.fixture
async def analysis_records():
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
            username=f"analyzeruser_{suffix}",
            email=f"analyzer_{suffix}@example.com",
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
            status=RepositoryStatus.PENDING,
        )
        job = await job_repository.create(db, repository_id=repository.id, job_type=JobType.INGEST)
        await db.commit()
        records = (job.id, user.id, repository.id)

    yield records

    job_id, user_id, repository_id = records
    async with session_factory() as db:
        repo = await repository_repository.get_by_id_for_user(db, repository_id, user_id)
        if repo:
            await db.delete(repo)
        user = await db.get(User, user_id)
        if user:
            await db.delete(user)
        await db.commit()

    await engine.dispose()


def _make_clone_result(job_id, branches: list[str], *, truncated: bool = False) -> CloneResult:
    clone_path = Path("/tmp/gitsight-test") / str(job_id)
    clone_path.mkdir(parents=True, exist_ok=True)
    (clone_path / "main.py").write_text("def hello():\n    pass\n", encoding="utf-8")
    return CloneResult(
        clone_path=clone_path,
        default_branch=branches[0],
        default_commit_hash="abc123",
        branches=branches,
        total_branches_found=len(branches) if not truncated else len(branches) + 5,
        branches_truncated=truncated,
        analyzed_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_repository_analyzer_marks_completed(analysis_records):
    job_id, _, repository_id = analysis_records
    clone_result = _make_clone_result(job_id, ["main"])

    try:
        with (
            patch("app.services.analysis.repository_analyzer.RepositoryCloner") as mock_cloner_cls,
            patch("app.services.analysis.repository_analyzer.Repo") as mock_repo_cls,
            patch("app.services.analysis.repository_analyzer.shutil.rmtree") as mock_rmtree,
            patch(
                "app.services.analysis.repository_analyzer.sync_pull_requests",
                new_callable=AsyncMock,
            ),
            patch(
                "app.services.analysis.repository_analyzer.RepositoryIndexingService",
            ) as mock_indexing_cls,
        ):
            mock_cloner_cls.return_value.clone.return_value = clone_result
            mock_cloner_cls.return_value.checkout_branch.return_value = "abc123"
            mock_repo_cls.return_value = MagicMock()
            mock_indexing_cls.return_value.index_repository = AsyncMock()
            analyzer = RepositoryAnalyzer()
            await analyzer.run(job_id)

        mock_rmtree.assert_called()

        settings = get_settings()
        engine = create_async_engine(
            settings.database_url,
            poolclass=NullPool,
            connect_args={"statement_cache_size": 0},
        )
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as db:
            job = await job_repository.get_by_id(db, job_id)
            assert job is not None
            assert job.status == JobStatus.COMPLETED
            assert job.progress == 100.0

            snapshots = await snapshot_repository.list_for_repository(db, repository_id)
            assert len(snapshots) == 1
            assert snapshots[0].branch == "main"

            repository = await db.get(Repository, repository_id)
            assert repository is not None
            assert repository.branches_analyzed_count == 1
            assert repository.branches_truncated is False
        await engine.dispose()
    finally:
        import shutil

        shutil.rmtree(clone_result.clone_path, ignore_errors=True)


@pytest.mark.asyncio
async def test_repository_analyzer_creates_snapshot_per_branch(analysis_records):
    job_id, _, repository_id = analysis_records
    clone_result = _make_clone_result(job_id, ["main", "gh-pages"])

    try:
        with (
            patch("app.services.analysis.repository_analyzer.RepositoryCloner") as mock_cloner_cls,
            patch("app.services.analysis.repository_analyzer.Repo") as mock_repo_cls,
            patch("app.services.analysis.repository_analyzer.shutil.rmtree"),
            patch(
                "app.services.analysis.repository_analyzer.sync_pull_requests",
                new_callable=AsyncMock,
            ),
            patch(
                "app.services.analysis.repository_analyzer.RepositoryIndexingService",
            ) as mock_indexing_cls,
        ):
            mock_cloner_cls.return_value.clone.return_value = clone_result
            mock_cloner_cls.return_value.checkout_branch.side_effect = ["abc123", "def456"]
            mock_repo_cls.return_value = MagicMock()
            mock_indexing_cls.return_value.index_repository = AsyncMock()
            analyzer = RepositoryAnalyzer()
            await analyzer.run(job_id)

        settings = get_settings()
        engine = create_async_engine(
            settings.database_url,
            poolclass=NullPool,
            connect_args={"statement_cache_size": 0},
        )
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as db:
            snapshots = await snapshot_repository.list_for_repository(db, repository_id)
            branches = {snap.branch for snap in snapshots}
            assert branches == {"main", "gh-pages"}

            repository = await db.get(Repository, repository_id)
            assert repository is not None
            assert repository.branches_analyzed_count == 2
        await engine.dispose()
    finally:
        import shutil

        shutil.rmtree(clone_result.clone_path, ignore_errors=True)


@pytest.mark.asyncio
async def test_repository_analyzer_marks_failed_on_clone_error(analysis_records):
    job_id, _, _ = analysis_records

    with (
        patch("app.services.analysis.repository_analyzer.RepositoryCloner") as mock_cloner_cls,
        patch("app.services.analysis.repository_analyzer.shutil.rmtree"),
    ):
        mock_cloner_cls.return_value.clone.side_effect = AnalysisError("Clone failed")
        analyzer = RepositoryAnalyzer()
        await analyzer.run(job_id)

    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        connect_args={"statement_cache_size": 0},
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        job = await job_repository.get_by_id(db, job_id)
        assert job is not None
        assert job.status == JobStatus.FAILED
        assert job.error_message == "Clone failed"
    await engine.dispose()


async def _run_analyzer(job_id, clone_result, checkout_hashes: list[str], skip_unchanged: bool):
    with (
        patch("app.services.analysis.repository_analyzer.RepositoryCloner") as mock_cloner_cls,
        patch("app.services.analysis.repository_analyzer.Repo") as mock_repo_cls,
        patch("app.services.analysis.repository_analyzer.shutil.rmtree"),
        patch(
            "app.services.analysis.repository_analyzer.sync_pull_requests",
            new_callable=AsyncMock,
        ),
        patch(
            "app.services.analysis.repository_analyzer.RepositoryIndexingService",
        ) as mock_indexing_cls,
    ):
        mock_cloner_cls.return_value.clone.return_value = clone_result
        mock_cloner_cls.return_value.checkout_branch.side_effect = checkout_hashes
        mock_repo_cls.return_value = MagicMock()
        mock_indexing_cls.return_value.index_repository = AsyncMock()
        analyzer = RepositoryAnalyzer()
        await analyzer.run(job_id, skip_unchanged=skip_unchanged)


@pytest.mark.asyncio
async def test_repository_analyzer_skips_unchanged_branches_on_refresh(analysis_records):
    job_id, _, repository_id = analysis_records
    clone_result = _make_clone_result(job_id, ["main"])

    try:
        await _run_analyzer(job_id, clone_result, ["abc123"], skip_unchanged=False)

        settings = get_settings()
        engine = create_async_engine(
            settings.database_url,
            poolclass=NullPool,
            connect_args={"statement_cache_size": 0},
        )
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        refresh_job_id = None
        async with session_factory() as db:
            snapshots_before = await snapshot_repository.list_for_repository(db, repository_id)
            assert len(snapshots_before) == 1
            snapshot_id_before = snapshots_before[0].id

            refresh_job = await job_repository.create(
                db,
                repository_id=repository_id,
                job_type=JobType.INGEST,
            )
            refresh_job_id = refresh_job.id
            await db.commit()

        refresh_clone = _make_clone_result(refresh_job_id, ["main"])
        await _run_analyzer(refresh_job_id, refresh_clone, ["abc123"], skip_unchanged=True)

        async with session_factory() as db:
            job = await job_repository.get_by_id(db, refresh_job_id)
            assert job is not None
            assert job.status == JobStatus.COMPLETED
            assert job.current_stage == "No changes detected"

            snapshots_after = await snapshot_repository.list_for_repository(db, repository_id)
            assert len(snapshots_after) == 1
            assert snapshots_after[0].id == snapshot_id_before
            assert snapshots_after[0].commit_hash == "abc123"
        await engine.dispose()
    finally:
        import shutil

        shutil.rmtree(clone_result.clone_path, ignore_errors=True)
        if refresh_job_id:
            shutil.rmtree(
                Path("/tmp/gitsight-test") / str(refresh_job_id),
                ignore_errors=True,
            )


@pytest.mark.asyncio
async def test_repository_analyzer_replaces_changed_branch_on_refresh(analysis_records):
    job_id, _, repository_id = analysis_records
    clone_result = _make_clone_result(job_id, ["main"])

    try:
        await _run_analyzer(job_id, clone_result, ["abc123"], skip_unchanged=False)

        settings = get_settings()
        engine = create_async_engine(
            settings.database_url,
            poolclass=NullPool,
            connect_args={"statement_cache_size": 0},
        )
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        refresh_job_id = None
        async with session_factory() as db:
            refresh_job = await job_repository.create(
                db,
                repository_id=repository_id,
                job_type=JobType.INGEST,
            )
            refresh_job_id = refresh_job.id
            await db.commit()

        refresh_clone = _make_clone_result(refresh_job_id, ["main"])
        await _run_analyzer(refresh_job_id, refresh_clone, ["def456"], skip_unchanged=True)

        async with session_factory() as db:
            snapshots = await snapshot_repository.list_for_repository(db, repository_id)
            assert len(snapshots) == 1
            assert snapshots[0].commit_hash == "def456"
        await engine.dispose()
    finally:
        import shutil

        shutil.rmtree(clone_result.clone_path, ignore_errors=True)
        if refresh_job_id:
            shutil.rmtree(
                Path("/tmp/gitsight-test") / str(refresh_job_id),
                ignore_errors=True,
            )


@pytest.mark.asyncio
async def test_repository_analyzer_completes_when_pull_request_sync_fails(analysis_records):
    job_id, _, repository_id = analysis_records
    clone_result = _make_clone_result(job_id, ["main"])

    try:
        with (
            patch("app.services.analysis.repository_analyzer.RepositoryCloner") as mock_cloner_cls,
            patch("app.services.analysis.repository_analyzer.Repo") as mock_repo_cls,
            patch("app.services.analysis.repository_analyzer.shutil.rmtree"),
            patch(
                "app.services.analysis.repository_analyzer.sync_pull_requests",
                new_callable=AsyncMock,
            ) as mock_sync_pull_requests,
            patch(
                "app.services.analysis.repository_analyzer.RepositoryIndexingService",
            ) as mock_indexing_cls,
        ):
            mock_cloner_cls.return_value.clone.return_value = clone_result
            mock_cloner_cls.return_value.checkout_branch.return_value = "abc123"
            mock_repo_cls.return_value = MagicMock()
            mock_sync_pull_requests.side_effect = RuntimeError("GitHub unavailable")
            mock_indexing_cls.return_value.index_repository = AsyncMock()

            analyzer = RepositoryAnalyzer()
            await analyzer.run(job_id)

        settings = get_settings()
        engine = create_async_engine(
            settings.database_url,
            poolclass=NullPool,
            connect_args={"statement_cache_size": 0},
        )
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as db:
            job = await job_repository.get_by_id(db, job_id)
            assert job is not None
            assert job.status == JobStatus.COMPLETED

            repository = await db.get(Repository, repository_id)
            assert repository is not None
            assert repository.status == RepositoryStatus.ACTIVE

            events = await job_event_repository.list_for_job(db, job_id)
            assert any(
                "Warning: PR sync failed: GitHub unavailable" in event.message for event in events
            )
        await engine.dispose()
    finally:
        import shutil

        shutil.rmtree(clone_result.clone_path, ignore_errors=True)
