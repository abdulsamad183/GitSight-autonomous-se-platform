from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import numpy as np
import pytest
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
from tests.git_fixtures import commit_file, init_git_repo


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
        snapshot = await snapshot_repository.create(
            db,
            repository_id=repository.id,
            data=SnapshotCreate(
                commit_hash="abc123",
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
    mock_model.encode.return_value = np.array([[0.1] * 384])

    async with session_factory() as db:
        with patch(
            "app.services.indexing.embedding_service.get_embedding_model",
            return_value=mock_model,
        ):
            service = RepositoryIndexingService(db)
            await service.index_repository(
                repository_id=repository_id,
                clone_path=Path(repo_path),
                branches=["main"],
            )

        total_chunks = await code_chunk_repository.count_by_repository(db, repository_id)
        assert total_chunks == 1

        repository = await repository_repository.get_by_id(db, repository_id)
        assert repository is not None
        assert repository.indexing_status.value == "completed"
        assert repository.total_chunks == 1
        assert repository.embedded_chunks == 1

    await engine.dispose()
