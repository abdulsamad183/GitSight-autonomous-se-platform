from pathlib import Path
from uuid import uuid4

from git import Repo

from app.services.indexing.diff_chunk_service import build_diff_chunks
from tests.git_fixtures import create_two_branch_fixture


def test_build_diff_chunks_for_feature_branch(tmp_path: Path):
    repo_path = tmp_path / "repo"
    create_two_branch_fixture(repo_path)
    git_repo = Repo(repo_path)

    main_commit = git_repo.git.rev_parse("main").strip()
    gh_pages_commit = git_repo.git.rev_parse("gh-pages").strip()

    chunks = build_diff_chunks(
        git_repo,
        repository_id=uuid4(),
        branch_name="gh-pages",
        default_commit=main_commit,
        branch_commit=gh_pages_commit,
    )

    assert chunks
    assert any(chunk.file_path == "index.html" for chunk in chunks)
    assert all(chunk.chunk_type == "diff_hunk" for chunk in chunks)
    assert all(chunk.base_commit_hash for chunk in chunks)
    assert all(chunk.head_commit_hash == gh_pages_commit for chunk in chunks)

    git_repo.close()


def test_build_diff_chunks_empty_when_same_commit(tmp_path: Path):
    repo_path = tmp_path / "repo"
    create_two_branch_fixture(repo_path)
    git_repo = Repo(repo_path)
    main_commit = git_repo.git.rev_parse("main").strip()

    chunks = build_diff_chunks(
        git_repo,
        repository_id=uuid4(),
        branch_name="main",
        default_commit=main_commit,
        branch_commit=main_commit,
    )
    assert chunks == []
    git_repo.close()
