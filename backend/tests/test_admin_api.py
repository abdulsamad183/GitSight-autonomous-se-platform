import pytest

from app.models.repository import IndexingStatus, Repository, RepositoryStatus
from app.repositories import user_repository

STATS_URL = "/api/v1/admin/stats"
USERS_URL = "/api/v1/admin/users"


@pytest.mark.asyncio
async def test_admin_stats_forbidden_for_regular_user(authenticated_client):
    response = await authenticated_client.get(STATS_URL)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_stats_ok(admin_client):
    response = await admin_client.get(STATS_URL)
    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] >= 1
    assert "repos_by_status" in data
    assert "repos_by_indexing_status" in data
    assert "signups_last_7_days" in data
    assert "repos_added_last_7_days" in data


@pytest.mark.asyncio
async def test_admin_list_users(admin_client):
    response = await admin_client.get(USERS_URL)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert "repository_count" in data["items"][0]


@pytest.mark.asyncio
async def test_admin_user_detail_includes_repo_urls(admin_client):
    session = admin_client.test_session
    users_response = await admin_client.get(USERS_URL)
    admin_user = next(
        item
        for item in users_response.json()["items"]
        if item["email"] == "platform-admin@example.com"
    )

    repo = Repository(
        user_id=admin_user["id"],
        name="demo/repo",
        repo_url="https://github.com/demo/repo",
        owner="demo",
        repository_name="repo",
        status=RepositoryStatus.ACTIVE,
        indexing_status=IndexingStatus.COMPLETED,
    )
    session.add(repo)
    await session.flush()

    detail = await admin_client.get(f"{USERS_URL}/{admin_user['id']}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["email"] == "platform-admin@example.com"
    assert len(body["repositories"]) >= 1
    assert body["repositories"][0]["repo_url"] == "https://github.com/demo/repo"


@pytest.mark.asyncio
async def test_ensure_single_admin(db_client):
    from app.core.config import get_settings
    from app.services.admin_seed import ensure_single_admin

    settings = get_settings()
    session = db_client.test_session
    await ensure_single_admin(session, settings)
    await ensure_single_admin(session, settings)
    admins = await user_repository.list_admins(session)
    assert len(admins) == 1
    assert admins[0].email == settings.admin_email
