from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.code_chunk import ChunkType, CodeChunk
from app.models.repository import RepositoryStatus
from app.models.user import User
from app.repositories import chunk_embedding_repository, repository_repository
from app.services.search_service import SearchService
from tests.conftest import mock_fastembed_model
from tests.git_fixtures import commit_file, init_git_repo


@pytest.fixture
async def search_fixture(tmp_path):
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        connect_args={"statement_cache_size": 0},
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    suffix = uuid4().hex[:8]
    repo_path = tmp_path / f"search-repo-{suffix}"
    init_git_repo(repo_path)
    commit_file(
        repo_path,
        "jwt.py",
        "def validate_jwt_token(token):\n    return decode(token)\n",
        "add jwt",
    )

    async with session_factory() as db:
        user = User(
            username=f"searchuser_{suffix}",
            email=f"search_{suffix}@example.com",
            hashed_password=hash_password("securepass123"),
        )
        db.add(user)
        await db.flush()

        repository = await repository_repository.create(
            db,
            user_id=user.id,
            name=f"local/search-{suffix}",
            repo_url=str(repo_path),
            owner="local",
            repository_name=f"search-{suffix}",
            status=RepositoryStatus.ACTIVE,
        )

        chunk = CodeChunk(
            repository_id=repository.id,
            branch_name="main",
            file_path="jwt.py",
            chunk_type=ChunkType.FUNCTION,
            symbol_name="validate_jwt_token",
            parent_symbol=None,
            start_line=1,
            end_line=2,
            content="def validate_jwt_token(token):\n    return decode(token)\n",
            content_hash="jwtchunkhash123",
        )
        db.add(chunk)
        await db.flush()

        mock_model = mock_fastembed_model()
        with patch(
            "app.services.indexing.embedding_service.get_embedding_model",
            return_value=mock_model,
        ):
            await chunk_embedding_repository.bulk_upsert(
                db,
                chunk_ids=[chunk.id],
                embeddings=[[0.1] * 384],
                model_name="BAAI/bge-small-en-v1.5",
            )

        await db.commit()
        records = (repository.id, user.id, chunk.id)

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
async def test_keyword_search_finds_exact_symbol(search_fixture):
    repository_id, _, _ = search_fixture
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        connect_args={"statement_cache_size": 0},
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        service = SearchService(db)
        results = await service.keyword_search(repository_id, "jwt")
        assert len(results) >= 1
        assert any("jwt" in r.symbol_name.lower() or "jwt" in r.file_path.lower() for r in results)

    await engine.dispose()


@pytest.mark.asyncio
async def test_semantic_search_returns_results(search_fixture):
    repository_id, _, _ = search_fixture
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        connect_args={"statement_cache_size": 0},
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    mock_model = mock_fastembed_model()

    async with session_factory() as db:
        with patch(
            "app.services.indexing.embedding_service.get_embedding_model",
            return_value=mock_model,
        ):
            service = SearchService(db)
            results = await service.semantic_search(
                repository_id, "token validation", threshold=0.0
            )
            assert len(results) >= 1

    await engine.dispose()


@pytest.mark.asyncio
async def test_hybrid_search_combines_scores(search_fixture):
    repository_id, _, _ = search_fixture
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        connect_args={"statement_cache_size": 0},
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    mock_model = mock_fastembed_model()

    async with session_factory() as db:
        with patch(
            "app.services.indexing.embedding_service.get_embedding_model",
            return_value=mock_model,
        ):
            service = SearchService(db)
            results = await service.hybrid_search(repository_id, "jwt")
            assert len(results) >= 1
            assert results[0].final_score is not None

    await engine.dispose()


@pytest.mark.asyncio
async def test_retrieve_context_returns_full_content(search_fixture):
    repository_id, _, chunk_id = search_fixture
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        connect_args={"statement_cache_size": 0},
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    mock_model = mock_fastembed_model()

    async with session_factory() as db:
        with patch(
            "app.services.indexing.embedding_service.get_embedding_model",
            return_value=mock_model,
        ):
            service = SearchService(db)
            context = await service.retrieve_context(repository_id, "jwt", top_k=1)
            assert len(context) >= 1
            assert "validate_jwt_token" in context[0].content

    await engine.dispose()
