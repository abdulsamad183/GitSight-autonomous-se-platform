from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.models.pull_request import PullRequestState
from app.repositories import pull_request_repository
from app.services.analysis.repository_analyzer import RepositoryAnalyzer
from app.services.analysis.repository_cloner import CloneResult
from app.utils.github import GitHubPullRequestDraft

ANALYZE_URL = "/api/v1/repositories/analyze"
LIST_URL = "/api/v1/repositories"


def _make_clone_result(job_id: UUID, branches: list[str]) -> CloneResult:
    clone_path = Path("/tmp/gitsight-api-test") / str(job_id)
    clone_path.mkdir(parents=True, exist_ok=True)
    (clone_path / "main.py").write_text("def hello():\n    pass\n", encoding="utf-8")
    return CloneResult(
        clone_path=clone_path,
        default_branch=branches[0],
        default_commit_hash="abc123",
        branches=branches,
        total_branches_found=len(branches),
        branches_truncated=False,
        analyzed_at=datetime.now(timezone.utc),
    )


def _make_pull_request_draft() -> GitHubPullRequestDraft:
    now = datetime.now(timezone.utc)
    return GitHubPullRequestDraft(
        github_pr_id=1001,
        number=15,
        title="Add authentication middleware",
        description="PR description",
        state=PullRequestState.OPEN,
        author_username="octocat",
        source_branch="feature/auth",
        target_branch="main",
        github_created_at=now,
        github_updated_at=now,
        github_closed_at=None,
        github_merged_at=None,
        is_draft=False,
        is_merged=False,
        html_url="https://github.com/octocat/Hello-World/pull/15",
    )


@pytest.mark.asyncio
async def test_analyze_requires_auth(client):
    response = await client.post(
        ANALYZE_URL,
        json={"github_url": "https://github.com/octocat/Hello-World"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_analyze_invalid_url(authenticated_client):
    response = await authenticated_client.post(
        ANALYZE_URL,
        json={"github_url": "https://example.com/not-github"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_analyze_success(authenticated_client):
    with (
        patch(
            "app.services.analysis_service.validate_public_repo",
            new_callable=AsyncMock,
        ),
        patch("app.services.analysis_service.run_analysis_job", new_callable=AsyncMock),
    ):
        response = await authenticated_client.post(
            ANALYZE_URL,
            json={"github_url": "https://github.com/octocat/Hello-World"},
        )

    assert response.status_code == 202
    data = response.json()
    assert "repository_id" in data
    assert "job_id" in data
    assert data["status"] == "PENDING"
    assert data["cached"] is False


@pytest.mark.asyncio
async def test_list_repositories(authenticated_client):
    with (
        patch(
            "app.services.analysis_service.validate_public_repo",
            new_callable=AsyncMock,
        ),
        patch("app.services.analysis_service.run_analysis_job", new_callable=AsyncMock),
    ):
        await authenticated_client.post(
            ANALYZE_URL,
            json={"github_url": "https://github.com/octocat/List-Repo"},
        )

    response = await authenticated_client.get(LIST_URL)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_repository_pull_requests_endpoint_and_summary_counts(client):
    from uuid import uuid4

    suffix = uuid4().hex[:8]
    register_payload = {
        "username": f"prapiuser_{suffix}",
        "email": f"prapi_{suffix}@example.com",
        "password": "securepass123",
    }
    register_response = await client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201

    with (
        patch(
            "app.services.analysis_service.validate_public_repo",
            new_callable=AsyncMock,
        ),
        patch("app.services.analysis_service.run_analysis_job", new_callable=AsyncMock),
    ):
        analyze_response = await client.post(
            ANALYZE_URL,
            json={"github_url": "https://github.com/octocat/PR-Repo"},
        )

    assert analyze_response.status_code == 202
    repository_id = UUID(analyze_response.json()["repository_id"])

    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        connect_args={"statement_cache_size": 0},
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        await pull_request_repository.upsert_many(
            db,
            repository_id=repository_id,
            pull_requests=[_make_pull_request_draft()],
            synced_at=datetime.now(timezone.utc),
        )
        await db.commit()
    await engine.dispose()

    pull_requests_response = await client.get(f"/api/v1/repositories/{repository_id}/pull-requests")
    assert pull_requests_response.status_code == 200
    pull_requests = pull_requests_response.json()
    assert len(pull_requests) == 1
    pull_request = pull_requests[0]
    assert pull_request["number"] == 15
    assert pull_request["title"] == "Add authentication middleware"
    assert pull_request["state"] == "OPEN"
    assert pull_request["author"] == "octocat"
    assert pull_request["is_merged"] is False
    assert pull_request["source_branch"] == "feature/auth"
    assert pull_request["target_branch"] == "main"

    list_response = await client.get(LIST_URL)
    assert list_response.status_code == 200
    repository_item = next(
        item for item in list_response.json() if item["id"] == str(repository_id)
    )
    assert repository_item["total_pull_requests"] == 1
    assert repository_item["open_pull_requests"] == 1
    assert repository_item["merged_pull_requests"] == 0

    delete_response = await client.delete(f"/api/v1/repositories/{repository_id}")
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_get_repository_requires_ownership(authenticated_client, register_payload):
    with (
        patch(
            "app.services.analysis_service.validate_public_repo",
            new_callable=AsyncMock,
        ),
        patch("app.services.analysis_service.run_analysis_job", new_callable=AsyncMock),
    ):
        analyze_response = await authenticated_client.post(
            ANALYZE_URL,
            json={"github_url": "https://github.com/octocat/Owned-Repo"},
        )

    assert analyze_response.status_code == 202
    repository_id = analyze_response.json()["repository_id"]

    other_payload = {
        "username": "otheruser",
        "email": "other@example.com",
        "password": "securepass123",
    }
    other_client_response = await authenticated_client.post(
        "/api/v1/auth/register",
        json=other_payload,
    )
    assert other_client_response.status_code == 201

    await authenticated_client.post("/api/v1/auth/logout")
    login_response = await authenticated_client.post(
        "/api/v1/auth/login",
        json={"email": other_payload["email"], "password": other_payload["password"]},
    )
    assert login_response.status_code == 200

    response = await authenticated_client.get(f"/api/v1/repositories/{repository_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_repository(authenticated_client):
    with (
        patch(
            "app.services.analysis_service.validate_public_repo",
            new_callable=AsyncMock,
        ),
        patch("app.services.analysis_service.run_analysis_job", new_callable=AsyncMock),
    ):
        analyze_response = await authenticated_client.post(
            ANALYZE_URL,
            json={"github_url": "https://github.com/octocat/Delete-Me"},
        )

    repository_id = analyze_response.json()["repository_id"]
    delete_response = await authenticated_client.delete(f"/api/v1/repositories/{repository_id}")
    assert delete_response.status_code == 204

    get_response = await authenticated_client.get(f"/api/v1/repositories/{repository_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_clear_all_repositories(authenticated_client):
    with (
        patch(
            "app.services.analysis_service.validate_public_repo",
            new_callable=AsyncMock,
        ),
        patch("app.services.analysis_service.run_analysis_job", new_callable=AsyncMock),
    ):
        await authenticated_client.post(
            ANALYZE_URL,
            json={"github_url": "https://github.com/octocat/Clear-All-1"},
        )
        await authenticated_client.post(
            ANALYZE_URL,
            json={"github_url": "https://github.com/octocat/Clear-All-2"},
        )

    clear_response = await authenticated_client.delete(LIST_URL)
    assert clear_response.status_code == 200
    assert clear_response.json()["deleted_count"] >= 2

    list_response = await authenticated_client.get(LIST_URL)
    assert list_response.status_code == 200
    assert list_response.json() == []


@pytest.mark.asyncio
async def test_list_branches_and_details_by_branch(client):
    from uuid import uuid4

    suffix = uuid4().hex[:8]
    register_payload = {
        "username": f"branchapiuser_{suffix}",
        "email": f"branchapi_{suffix}@example.com",
        "password": "securepass123",
    }
    register_response = await client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201

    with (
        patch(
            "app.services.analysis_service.validate_public_repo",
            new_callable=AsyncMock,
        ),
        patch("app.services.analysis_service.run_analysis_job", new_callable=AsyncMock),
        patch(
            "app.services.analysis.repository_analyzer.RepositoryCloner",
        ) as mock_cloner_cls,
        patch("app.services.analysis.repository_analyzer.Repo") as mock_repo_cls,
        patch("app.services.analysis.repository_analyzer.shutil.rmtree"),
        patch(
            "app.services.analysis.repository_analyzer.sync_pull_requests",
            new_callable=AsyncMock,
        ),
    ):
        analyze_response = await client.post(
            ANALYZE_URL,
            json={"github_url": "https://github.com/octocat/Branch-Repo"},
        )
        assert analyze_response.status_code == 202
        payload = analyze_response.json()
        repository_id = payload["repository_id"]
        job_id = UUID(payload["job_id"])

        clone_result = _make_clone_result(job_id, ["main", "gh-pages"])
        mock_cloner_cls.return_value.clone.return_value = clone_result
        mock_cloner_cls.return_value.checkout_branch.side_effect = ["abc123", "def456"]
        mock_repo_cls.return_value = MagicMock()

        await RepositoryAnalyzer().run(job_id)

    branches_response = await client.get(
        f"/api/v1/repositories/{repository_id}/branches",
    )
    assert branches_response.status_code == 200
    branches = branches_response.json()
    assert len(branches) == 2
    branch_names = {item["branch"] for item in branches}
    assert branch_names == {"main", "gh-pages"}

    details_response = await client.get(
        f"/api/v1/repositories/{repository_id}/details?branch=gh-pages",
    )
    assert details_response.status_code == 200
    details = details_response.json()
    assert details["selected_branch"] == "gh-pages"
    assert details["files_count"] >= 1

    delete_response = await client.delete(f"/api/v1/repositories/{repository_id}")
    assert delete_response.status_code == 204

    import shutil

    shutil.rmtree(clone_result.clone_path, ignore_errors=True)


@pytest.mark.asyncio
async def test_refresh_repository(client):
    from uuid import uuid4

    suffix = uuid4().hex[:8]
    register_payload = {
        "username": f"refreshuser_{suffix}",
        "email": f"refresh_{suffix}@example.com",
        "password": "securepass123",
    }
    register_response = await client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201

    with (
        patch(
            "app.services.analysis_service.validate_public_repo",
            new_callable=AsyncMock,
        ),
        patch("app.services.analysis_service.run_analysis_job", new_callable=AsyncMock),
        patch(
            "app.services.analysis.repository_analyzer.RepositoryCloner",
        ) as mock_cloner_cls,
        patch("app.services.analysis.repository_analyzer.Repo") as mock_repo_cls,
        patch("app.services.analysis.repository_analyzer.shutil.rmtree"),
        patch(
            "app.services.analysis.repository_analyzer.sync_pull_requests",
            new_callable=AsyncMock,
        ),
    ):
        analyze_response = await client.post(
            ANALYZE_URL,
            json={"github_url": "https://github.com/octocat/Refresh-Repo"},
        )
        assert analyze_response.status_code == 202
        payload = analyze_response.json()
        repository_id = payload["repository_id"]
        job_id = UUID(payload["job_id"])

        clone_result = _make_clone_result(job_id, ["main"])
        mock_cloner_cls.return_value.clone.return_value = clone_result
        mock_cloner_cls.return_value.checkout_branch.return_value = "abc123"
        mock_repo_cls.return_value = MagicMock()

        await RepositoryAnalyzer().run(job_id)

    with patch("app.services.analysis_service.run_analysis_job", new_callable=AsyncMock):
        refresh_response = await client.post(f"/api/v1/repositories/{repository_id}/refresh")
        assert refresh_response.status_code == 202
        data = refresh_response.json()
        assert data["repository_id"] == repository_id
        assert data["cached"] is False
        assert data["job_id"] is not None

    delete_response = await client.delete(f"/api/v1/repositories/{repository_id}")
    assert delete_response.status_code == 204

    import shutil

    shutil.rmtree(clone_result.clone_path, ignore_errors=True)


@pytest.mark.asyncio
async def test_graph_endpoint_requires_auth(client):
    from uuid import uuid4

    response = await client.get(f"/api/v1/repositories/{uuid4()}/graph")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_graph_endpoint_requires_ownership(authenticated_client):
    with (
        patch(
            "app.services.analysis_service.validate_public_repo",
            new_callable=AsyncMock,
        ),
        patch("app.services.analysis_service.run_analysis_job", new_callable=AsyncMock),
    ):
        analyze_response = await authenticated_client.post(
            ANALYZE_URL,
            json={"github_url": "https://github.com/octocat/Graph-Owned"},
        )

    repository_id = analyze_response.json()["repository_id"]

    other_payload = {
        "username": "graphother",
        "email": "graphother@example.com",
        "password": "securepass123",
    }
    await authenticated_client.post("/api/v1/auth/register", json=other_payload)
    await authenticated_client.post("/api/v1/auth/logout")
    await authenticated_client.post(
        "/api/v1/auth/login",
        json={"email": other_payload["email"], "password": other_payload["password"]},
    )

    response = await authenticated_client.get(f"/api/v1/repositories/{repository_id}/graph")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_graph_endpoint_success(client):
    from uuid import uuid4

    suffix = uuid4().hex[:8]
    register_payload = {
        "username": f"graphuser_{suffix}",
        "email": f"graph_{suffix}@example.com",
        "password": "securepass123",
    }
    register_response = await client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201

    with (
        patch(
            "app.services.analysis_service.validate_public_repo",
            new_callable=AsyncMock,
        ),
        patch("app.services.analysis_service.run_analysis_job", new_callable=AsyncMock),
        patch(
            "app.services.analysis.repository_analyzer.RepositoryCloner",
        ) as mock_cloner_cls,
        patch("app.services.analysis.repository_analyzer.Repo") as mock_repo_cls,
        patch("app.services.analysis.repository_analyzer.shutil.rmtree"),
        patch(
            "app.services.analysis.repository_analyzer.sync_pull_requests",
            new_callable=AsyncMock,
        ),
    ):
        analyze_response = await client.post(
            ANALYZE_URL,
            json={"github_url": "https://github.com/octocat/Graph-Repo"},
        )
        assert analyze_response.status_code == 202
        payload = analyze_response.json()
        repository_id = payload["repository_id"]
        job_id = UUID(payload["job_id"])

        clone_result = _make_clone_result(job_id, ["main"])
        mock_cloner_cls.return_value.clone.return_value = clone_result
        mock_cloner_cls.return_value.checkout_branch.return_value = "abc123"
        mock_repo_cls.return_value = MagicMock()

        await RepositoryAnalyzer().run(job_id)

    graph_response = await client.get(f"/api/v1/repositories/{repository_id}/graph")
    assert graph_response.status_code == 200
    graph = graph_response.json()
    assert graph["graph_type"] == "structure"
    assert "nodes" in graph
    assert "edges" in graph
    assert "stats" in graph
    assert any(node["type"] == "repository" for node in graph["nodes"])
    assert any(node["type"] == "file" for node in graph["nodes"])

    branch_response = await client.get(
        f"/api/v1/repositories/{repository_id}/graph?branch=main",
    )
    assert branch_response.status_code == 200
    assert branch_response.json()["branch"] == "main"

    unknown_type_response = await client.get(
        f"/api/v1/repositories/{repository_id}/graph?type=dependency",
    )
    assert unknown_type_response.status_code == 400

    delete_response = await client.delete(f"/api/v1/repositories/{repository_id}")
    assert delete_response.status_code == 204

    import shutil

    shutil.rmtree(clone_result.clone_path, ignore_errors=True)
