from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import numpy as np
import pytest
from git import Repo
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.repository import RepositoryStatus
from app.models.user import User
from app.repositories import (
    code_chunk_repository,
    repository_repository,
    snapshot_repository,
    symbol_repository,
)
from app.schemas.analysis import FileCreate, SnapshotCreate, SymbolCreate
from app.services.indexing.repository_indexing_service import RepositoryIndexingService
from tests.git_fixtures import _run_git, commit_file, create_two_branch_fixture, init_git_repo


@pytest.fixture
async def indexing_records(tmp_path):
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        connect_args={"statement_cache_size": 0},
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    suffix = uuid4().hex[:8]
    repo_path = tmp_path / f"repo-{suffix}"
    init_git_repo(repo_path)
    commit_file(repo_path, "main.py", "def hello():\n    return 1\n", "initial")
    _run_git(["branch", "-M", "main"], cwd=repo_path)
    git_repo = Repo(repo_path)
    main_commit = git_repo.head.commit.hexsha
    git_repo.close()

    async with session_factory() as db:
        user = User(
            username=f"indexuser_{suffix}",
            email=f"index_{suffix}@example.com",
            hashed_password=hash_password("securepass123"),
        )
        db.add(user)
        await db.flush()

        repository = await repository_repository.create(
            db,
            user_id=user.id,
            name=f"local/repo-{suffix}",
            repo_url=str(repo_path),
            owner="local",
            repository_name=f"repo-{suffix}",
            status=RepositoryStatus.ACTIVE,
        )
        await repository_repository.update_after_clone(
            db,
            repository,
            default_branch="main",
            latest_commit_hash=main_commit,
        )
        snapshot = await snapshot_repository.create(
            db,
            repository_id=repository.id,
            data=SnapshotCreate(
                commit_hash=main_commit,
                branch="main",
                analyzed_at=datetime.now(timezone.utc),
            ),
        )
        from app.repositories import file_repository

        file_records = await file_repository.bulk_create(
            db,
            repository_id=repository.id,
            snapshot_id=snapshot.id,
            files=[
                FileCreate(
                    relative_path="main.py",
                    file_name="main.py",
                    extension=".py",
                    language="python",
                    size_bytes=32,
                    is_binary=False,
                )
            ],
        )
        await symbol_repository.bulk_create(
            db,
            repository_id=repository.id,
            snapshot_id=snapshot.id,
            symbols=[
                SymbolCreate(
                    file_id=file_records[0].id,
                    symbol_name="hello",
                    symbol_type="function",
                    start_line=1,
                    end_line=2,
                    signature="def hello():",
                )
            ],
        )
        await db.commit()
        records = (repository.id, user.id, repo_path)

    yield records

    repo_id, user_id, _ = records
    async with session_factory() as db:
        repo = await repository_repository.get_by_id_for_user(db, repo_id, user_id)
        if repo:
            await db.delete(repo)
        user = await db.get(User, user_id)
        if user:
            await db.delete(user)
        await db.commit()

    await engine.dispose()


@pytest.fixture
async def multi_branch_indexing_records(tmp_path):
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        connect_args={"statement_cache_size": 0},
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    suffix = uuid4().hex[:8]
    repo_path = tmp_path / f"multi-{suffix}"
    create_two_branch_fixture(repo_path)
    git_repo = Repo(repo_path)
    main_commit = git_repo.git.rev_parse("main").strip()
    gh_pages_commit = git_repo.git.rev_parse("gh-pages").strip()
    git_repo.close()

    async with session_factory() as db:
        user = User(
            username=f"multiuser_{suffix}",
            email=f"multi_{suffix}@example.com",
            hashed_password=hash_password("securepass123"),
        )
        db.add(user)
        await db.flush()

        repository = await repository_repository.create(
            db,
            user_id=user.id,
            name=f"local/multi-{suffix}",
            repo_url=str(repo_path),
            owner="local",
            repository_name=f"multi-{suffix}",
            status=RepositoryStatus.ACTIVE,
        )
        await repository_repository.update_after_clone(
            db,
            repository,
            default_branch="main",
            latest_commit_hash=main_commit,
        )

        main_snapshot = await snapshot_repository.create(
            db,
            repository_id=repository.id,
            data=SnapshotCreate(
                commit_hash=main_commit,
                branch="main",
                analyzed_at=datetime.now(timezone.utc),
            ),
        )
        gh_snapshot = await snapshot_repository.create(
            db,
            repository_id=repository.id,
            data=SnapshotCreate(
                commit_hash=gh_pages_commit,
                branch="gh-pages",
                analyzed_at=datetime.now(timezone.utc),
            ),
        )

        from app.repositories import file_repository

        main_file = await file_repository.bulk_create(
            db,
            repository_id=repository.id,
            snapshot_id=main_snapshot.id,
            files=[
                FileCreate(
                    relative_path="main.py",
                    file_name="main.py",
                    extension=".py",
                    language="python",
                    size_bytes=32,
                    is_binary=False,
                )
            ],
        )
        await file_repository.bulk_create(
            db,
            repository_id=repository.id,
            snapshot_id=gh_snapshot.id,
            files=[
                FileCreate(
                    relative_path="index.html",
                    file_name="index.html",
                    extension=".html",
                    language="html",
                    size_bytes=32,
                    is_binary=False,
                )
            ],
        )
        await symbol_repository.bulk_create(
            db,
            repository_id=repository.id,
            snapshot_id=main_snapshot.id,
            symbols=[
                SymbolCreate(
                    file_id=main_file[0].id,
                    symbol_name="hello",
                    symbol_type="function",
                    start_line=1,
                    end_line=2,
                    signature="def hello():",
                )
            ],
        )
        await db.commit()
        records = (repository.id, user.id, repo_path)

    yield records

    repo_id, user_id, _ = records
    async with session_factory() as db:
        repo = await repository_repository.get_by_id_for_user(db, repo_id, user_id)
        if repo:
            await db.delete(repo)
        user = await db.get(User, user_id)
        if user:
            await db.delete(user)
        await db.commit()

    await engine.dispose()


@pytest.mark.asyncio
async def test_repository_indexing_creates_chunks_and_embeddings(indexing_records):
    repository_id, _, repo_path = indexing_records
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        connect_args={"statement_cache_size": 0},
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    mock_model = MagicMock()

    def mock_encode(texts, batch_size=None, show_progress_bar=False):
        if isinstance(texts, str):
            return np.array([0.1] * 384)
        return np.array([[0.1] * 384 for _ in texts])

    mock_model.encode.side_effect = mock_encode

    git_repo = Repo(repo_path)
    try:
        async with session_factory() as db:
            with patch(
                "app.services.indexing.embedding_service.get_embedding_model",
                return_value=mock_model,
            ):
                service = RepositoryIndexingService(db)
                await service.index_repository(
                    repository_id=repository_id,
                    clone_path=Path(repo_path),
                    git_repo=git_repo,
                    default_branch="main",
                    branches=["main"],
                )

            total_chunks = await code_chunk_repository.count_by_repository(db, repository_id)
            assert total_chunks == 1

            repository = await repository_repository.get_by_id(db, repository_id)
            assert repository is not None
            assert repository.indexing_status.value == "completed"
            assert repository.total_chunks == 1
            assert repository.embedded_chunks == 1
    finally:
        git_repo.close()

    await engine.dispose()


@pytest.mark.asyncio
async def test_multi_branch_indexing_full_default_and_diff_secondary(multi_branch_indexing_records):
    repository_id, _, repo_path = multi_branch_indexing_records
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        connect_args={"statement_cache_size": 0},
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    mock_model = MagicMock()

    def mock_encode(texts, batch_size=None, show_progress_bar=False):
        if isinstance(texts, str):
            return np.array([0.1] * 384)
        return np.array([[0.1] * 384 for _ in texts])

    mock_model.encode.side_effect = mock_encode

    git_repo = Repo(repo_path)
    try:
        async with session_factory() as db:
            with patch(
                "app.services.indexing.embedding_service.get_embedding_model",
                return_value=mock_model,
            ):
                service = RepositoryIndexingService(db)
                await service.index_repository(
                    repository_id=repository_id,
                    clone_path=Path(repo_path),
                    git_repo=git_repo,
                    default_branch="main",
                    branches=["main", "gh-pages"],
                )

            main_chunks, _ = await code_chunk_repository.list_by_repository(
                db, repository_id=repository_id, branch_name="main"
            )
            gh_chunks, _ = await code_chunk_repository.list_by_repository(
                db, repository_id=repository_id, branch_name="gh-pages"
            )

            assert len(main_chunks) >= 1
            assert any(chunk.chunk_type.value == "function" for chunk in main_chunks)
            assert len(gh_chunks) >= 1
            assert all(chunk.chunk_type.value == "diff_hunk" for chunk in gh_chunks)
    finally:
        git_repo.close()

    await engine.dispose()
