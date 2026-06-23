from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.repository import RepositoryStatus
from app.services.analysis_service import start_analysis


@pytest.mark.asyncio
async def test_start_analysis_returns_cached_for_active_repo():
    user_id = uuid4()
    repo_id = uuid4()
    job_id = uuid4()

    existing = MagicMock()
    existing.id = repo_id
    existing.status = RepositoryStatus.ACTIVE

    latest_job = MagicMock()
    latest_job.id = job_id

    db = AsyncMock()
    background_tasks = MagicMock()
    settings = MagicMock()

    with (
        patch(
            "app.services.analysis_service.parse_github_url",
            return_value=MagicMock(
                normalized_url="https://github.com/octocat/Cached-Repo",
                owner="octocat",
                repository_name="Cached-Repo",
            ),
        ),
        patch(
            "app.services.analysis_service.repository_repository.get_by_url_for_user",
            new_callable=AsyncMock,
            return_value=existing,
        ),
        patch(
            "app.services.analysis_service.job_repository.get_latest_for_repository",
            new_callable=AsyncMock,
            return_value=latest_job,
        ),
    ):
        result = await start_analysis(
            db,
            user_id=user_id,
            github_url="https://github.com/octocat/Cached-Repo",
            settings=settings,
            background_tasks=background_tasks,
        )

    assert result.cached is True
    assert result.status == "CACHED"
    assert result.repository_id == repo_id
    assert result.job_id == job_id
    background_tasks.add_task.assert_not_called()


@pytest.mark.asyncio
async def test_start_refresh_creates_job_for_active_repo():
    user_id = uuid4()
    repo_id = uuid4()
    job_id = uuid4()

    repository = MagicMock()
    repository.id = repo_id
    repository.status = RepositoryStatus.ACTIVE

    new_job = MagicMock()
    new_job.id = job_id

    db = AsyncMock()
    background_tasks = MagicMock()

    with (
        patch(
            "app.services.analysis_service.repository_repository.get_by_id_for_user",
            new_callable=AsyncMock,
            return_value=repository,
        ),
        patch(
            "app.services.analysis_service.job_repository.get_active_for_repository",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.services.analysis_service.job_repository.create",
            new_callable=AsyncMock,
            return_value=new_job,
        ),
    ):
        from app.services.analysis_service import start_refresh

        result = await start_refresh(
            db,
            user_id=user_id,
            repository_id=repo_id,
            background_tasks=background_tasks,
        )

    assert result.cached is False
    assert result.status == "PENDING"
    assert result.repository_id == repo_id
    assert result.job_id == job_id
    background_tasks.add_task.assert_called_once()
