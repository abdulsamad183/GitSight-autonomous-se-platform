from uuid import uuid4

from app.schemas.repository import RepositorySummaryResponse


def test_repository_summary_includes_language_breakdown_default():
    summary = RepositorySummaryResponse(
        id=uuid4(),
        owner="octocat",
        repository_name="hello",
        github_url="https://github.com/octocat/hello",
        latest_commit_hash=None,
        status="active",
        analysis_status="COMPLETED",
        files_count=2,
        classes_count=0,
        functions_count=0,
        methods_count=0,
        dependencies_count=0,
        language_breakdown={"python": 2, "json": 1},
    )
    assert summary.language_breakdown == {"python": 2, "json": 1}


def test_repository_summary_language_breakdown_defaults_empty():
    summary = RepositorySummaryResponse(
        id=uuid4(),
        owner="octocat",
        repository_name="hello",
        github_url="https://github.com/octocat/hello",
        latest_commit_hash=None,
        status="active",
        analysis_status="COMPLETED",
        files_count=0,
        classes_count=0,
        functions_count=0,
        methods_count=0,
        dependencies_count=0,
    )
    assert summary.language_breakdown == {}
