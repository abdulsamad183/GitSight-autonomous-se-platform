import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

from app.core.config import Settings
from app.services.analysis.repository_cloner import RepositoryCloner
from tests.git_fixtures import create_many_branch_fixture


def test_branch_cap_truncates_analysis(tmp_path: Path):
    source_repo = tmp_path / "source"
    create_many_branch_fixture(source_repo, count=15)

    bare_path = tmp_path / "bare.git"
    subprocess.run(
        ["git", "clone", "--bare", str(source_repo), str(bare_path)],
        check=True,
        capture_output=True,
    )

    settings = Settings(
        clone_base_dir=str(tmp_path / "clones"),
        max_branches_to_analyze=10,
        clone_depth=0,
    )
    cloner = RepositoryCloner(settings)
    result = cloner.clone(job_id=uuid4(), repo_url=str(bare_path))

    try:
        assert result.total_branches_found == 15
        assert len(result.branches) == 10
        assert result.branches_truncated is True
        assert result.branches[0] == "main"
    finally:
        shutil.rmtree(result.clone_path, ignore_errors=True)
        shutil.rmtree(bare_path, ignore_errors=True)
