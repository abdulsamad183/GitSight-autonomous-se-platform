import subprocess
from pathlib import Path


def _run_git(args: list[str], *, cwd: Path) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def init_git_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _run_git(["init"], cwd=path)
    _run_git(["config", "user.email", "test@example.com"], cwd=path)
    _run_git(["config", "user.name", "Test User"], cwd=path)


def commit_file(path: Path, filename: str, content: str, message: str) -> None:
    (path / filename).write_text(content, encoding="utf-8")
    _run_git(["add", filename], cwd=path)
    _run_git(["commit", "-m", message], cwd=path)


def create_two_branch_fixture(path: Path) -> None:
    init_git_repo(path)
    commit_file(path, "main.py", "def hello():\n    pass\n", "main commit")
    _run_git(["branch", "-M", "main"], cwd=path)
    _run_git(["checkout", "-b", "gh-pages"], cwd=path)
    commit_file(path, "index.html", "<html></html>\n", "gh-pages commit")
    _run_git(["checkout", "main"], cwd=path)


def create_many_branch_fixture(path: Path, count: int) -> None:
    init_git_repo(path)
    commit_file(path, "README.md", "# repo\n", "initial")
    _run_git(["branch", "-M", "main"], cwd=path)
    for index in range(1, count):
        branch = f"branch-{index:02d}"
        _run_git(["checkout", "-b", branch], cwd=path)
        commit_file(path, f"{branch}.txt", f"content {index}\n", f"commit on {branch}")
    _run_git(["checkout", "main"], cwd=path)
