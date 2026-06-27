from unittest.mock import MagicMock

import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.database import engine, get_db
from app.main import app


@pytest.fixture(autouse=True)
async def dispose_global_engine_after_test():
    yield
    await engine.dispose()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_client():
    settings = get_settings()
    test_engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        connect_args={"statement_cache_size": 0},
    )

    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac
        finally:
            app.dependency_overrides.clear()
            await session.close()
            await transaction.rollback()

    await test_engine.dispose()


@pytest.fixture
def register_payload():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepass123",
    }


def mock_fastembed_model(*, dim: int = 384) -> MagicMock:
    mock_model = MagicMock()

    def passage_embed(texts, batch_size=None, **kwargs):
        texts_list = [texts] if isinstance(texts, str) else list(texts)
        for _ in texts_list:
            yield np.array([0.1] * dim)

    def query_embed(queries, **kwargs):
        queries_list = [queries] if isinstance(queries, str) else list(queries)
        for _ in queries_list:
            yield np.array([0.1] * dim)

    mock_model.passage_embed.side_effect = passage_embed
    mock_model.query_embed.side_effect = query_embed
    return mock_model


@pytest.fixture
async def authenticated_client(db_client, register_payload):
    response = await db_client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == 201
    return db_client
