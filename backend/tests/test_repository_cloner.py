import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest
from git import Repo

from app.core.config import Settings
from app.services.analysis.repository_cloner import RepositoryCloner
from tests.git_fixtures import create_two_branch_fixture


@pytest.fixture
def clone_settings(tmp_path: Path) -> Settings:
    return Settings(
        clone_base_dir=str(tmp_path / "clones"),
        max_branches_to_analyze=10,
        clone_depth=0,
    )


@pytest.fixture
def source_repo(tmp_path: Path) -> Path:
    repo_path = tmp_path / "source"
    create_two_branch_fixture(repo_path)
    return repo_path


def test_list_remote_branches_from_local_clone(source_repo: Path):
    clone_dest = source_repo.parent / "clone"
    Repo.clone_from(str(source_repo), clone_dest)
    repo = Repo(clone_dest)
    try:
        branches = RepositoryCloner.list_remote_branches(repo)
        assert branches == ["gh-pages", "main"]
    finally:
        repo.close()
        shutil.rmtree(clone_dest, ignore_errors=True)


def test_prioritize_branches_puts_default_first():
    branches = ["gh-pages", "main", "develop"]
    ordered = RepositoryCloner.prioritize_branches(branches, "main")
    assert ordered[0] == "main"
    assert ordered[1:] == ["develop", "gh-pages"]


def test_clone_local_repo_discovers_branches(
    source_repo: Path,
    clone_settings: Settings,
    tmp_path: Path,
):
    bare_path = tmp_path / "bare.git"
    subprocess.run(
        ["git", "clone", "--bare", str(source_repo), str(bare_path)],
        check=True,
        capture_output=True,
    )

    cloner = RepositoryCloner(clone_settings)
    result = cloner.clone(job_id=uuid4(), repo_url=str(bare_path))

    try:
        assert result.default_branch == "main"
        assert result.branches == ["main", "gh-pages"]
        assert result.total_branches_found == 2
        assert result.branches_truncated is False
        assert (result.clone_path / "main.py").exists()
    finally:
        shutil.rmtree(result.clone_path, ignore_errors=True)
        shutil.rmtree(bare_path, ignore_errors=True)
