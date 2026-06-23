import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from git import Repo

from app.core.config import Settings
from app.services.exceptions import AnalysisError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CloneResult:
    clone_path: Path
    default_branch: str
    default_commit_hash: str
    branches: list[str]
    total_branches_found: int
    branches_truncated: bool
    analyzed_at: datetime


class RepositoryCloner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def clone(self, *, job_id: UUID, repo_url: str) -> CloneResult:
        base_dir = Path(self.settings.clone_base_dir)
        base_dir.mkdir(parents=True, exist_ok=True)
        clone_path = base_dir / str(job_id)

        if clone_path.exists():
            import shutil

            shutil.rmtree(clone_path, ignore_errors=True)

        try:
            clone_kwargs: dict = {}
            if self.settings.clone_depth > 0:
                clone_kwargs["depth"] = self.settings.clone_depth

            repo = Repo.clone_from(repo_url, clone_path, **clone_kwargs)
            default_branch = self._resolve_default_branch(repo)
            all_branches = self.list_remote_branches(repo)
            if default_branch not in all_branches and all_branches:
                default_branch = all_branches[0]

            total_found = len(all_branches)
            prioritized = self.prioritize_branches(all_branches, default_branch)
            max_branches = self.settings.max_branches_to_analyze
            branches_truncated = total_found > max_branches
            branches_to_analyze = prioritized[:max_branches]

            self.checkout_branch(repo, default_branch)
            default_commit_hash = repo.head.commit.hexsha
        except Exception as exc:
            logger.exception("Failed to clone repository")
            raise AnalysisError(f"Clone failed: {exc}") from exc

        return CloneResult(
            clone_path=clone_path,
            default_branch=default_branch,
            default_commit_hash=default_commit_hash,
            branches=branches_to_analyze,
            total_branches_found=total_found,
            branches_truncated=branches_truncated,
            analyzed_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _resolve_default_branch(repo: Repo) -> str:
        try:
            ref = repo.git.symbolic_ref("refs/remotes/origin/HEAD")
            if ref.startswith("refs/remotes/origin/"):
                return ref.removeprefix("refs/remotes/origin/")
            return ref
        except Exception:
            pass

        try:
            return repo.active_branch.name
        except Exception:
            return "main"

    @staticmethod
    def list_remote_branches(repo: Repo) -> list[str]:
        branches: set[str] = set()
        for ref in repo.remote().refs:
            name = ref.name
            if name.endswith("/HEAD"):
                continue
            if "/" in name:
                name = name.split("/", 1)[1]
            if name == "HEAD":
                continue
            branches.add(name)
        return sorted(branches)

    @staticmethod
    def prioritize_branches(branches: list[str], default_branch: str) -> list[str]:
        ordered: list[str] = []
        if default_branch in branches:
            ordered.append(default_branch)
        for branch in sorted(branches):
            if branch != default_branch:
                ordered.append(branch)
        return ordered

    @staticmethod
    def checkout_branch(repo: Repo, branch: str) -> str:
        repo.git.checkout(branch)
        return repo.head.commit.hexsha
