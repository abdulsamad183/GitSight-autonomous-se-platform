import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from app.core.config import Settings
from app.models.pull_request import PullRequestState
from app.services.exceptions import ForbiddenError, NotFoundError, ValidationError

GITHUB_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?github\.com/(?P<owner>[\w.\-]+)/(?P<repo>[\w.\-]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedGitHubUrl:
    owner: str
    repository_name: str
    normalized_url: str


@dataclass(frozen=True)
class GitHubPullRequestDraft:
    github_pr_id: int
    number: int
    title: str
    description: str | None
    state: PullRequestState
    author_username: str
    source_branch: str | None
    target_branch: str | None
    github_created_at: datetime
    github_updated_at: datetime
    github_closed_at: datetime | None
    github_merged_at: datetime | None
    is_draft: bool
    is_merged: bool
    html_url: str


def parse_github_url(url: str) -> ParsedGitHubUrl:
    trimmed = url.strip()
    if not trimmed:
        raise ValidationError("GitHub URL is required")

    match = GITHUB_URL_PATTERN.match(trimmed)
    if not match:
        raise ValidationError("Invalid GitHub repository URL")

    owner = match.group("owner")
    repo = match.group("repo")
    normalized = f"https://github.com/{owner}/{repo}"
    return ParsedGitHubUrl(owner=owner, repository_name=repo, normalized_url=normalized)


def _github_headers(settings: Settings) -> dict[str, str]:
    headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


def _parse_github_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def normalize_pull_request(item: dict[str, Any]) -> GitHubPullRequestDraft:
    merged_at = _parse_github_datetime(item.get("merged_at"))
    is_merged = bool(merged_at or item.get("merged"))
    raw_state = str(item.get("state") or "").lower()
    if is_merged:
        state = PullRequestState.MERGED
    elif raw_state == "open":
        state = PullRequestState.OPEN
    else:
        state = PullRequestState.CLOSED

    user = item.get("user") or {}
    head = item.get("head") or {}
    base = item.get("base") or {}

    created_at = _parse_github_datetime(item.get("created_at"))
    updated_at = _parse_github_datetime(item.get("updated_at"))
    if created_at is None or updated_at is None:
        raise ValidationError("GitHub pull request response is missing timestamps")

    return GitHubPullRequestDraft(
        github_pr_id=int(item["id"]),
        number=int(item["number"]),
        title=str(item.get("title") or ""),
        description=item.get("body"),
        state=state,
        author_username=str(user.get("login") or "unknown"),
        source_branch=head.get("ref"),
        target_branch=base.get("ref"),
        github_created_at=created_at,
        github_updated_at=updated_at,
        github_closed_at=_parse_github_datetime(item.get("closed_at")),
        github_merged_at=merged_at,
        is_draft=bool(item.get("draft")),
        is_merged=is_merged,
        html_url=str(item.get("html_url") or ""),
    )


async def validate_public_repo(owner: str, repo: str, settings: Settings) -> None:
    headers = _github_headers(settings)

    url = f"https://api.github.com/repos/{owner}/{repo}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, headers=headers)

    if response.status_code == 404:
        raise NotFoundError("Repository not found")
    if response.status_code == 403:
        raise ForbiddenError("Repository is private or access is denied")
    if response.status_code != 200:
        raise ValidationError("Unable to validate GitHub repository")


async def fetch_repository_pull_requests(
    owner: str,
    repo: str,
    settings: Settings,
) -> list[GitHubPullRequestDraft]:
    headers = _github_headers(settings)
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    pull_requests: list[GitHubPullRequestDraft] = []
    page = 1

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            response = await client.get(
                url,
                headers=headers,
                params={"state": "all", "per_page": 100, "page": page},
            )
            if response.status_code == 404:
                raise NotFoundError("Repository not found")
            if response.status_code == 403:
                raise ForbiddenError("Unable to fetch pull requests from GitHub")
            if response.status_code != 200:
                raise ValidationError("Unable to fetch pull requests from GitHub")

            items = response.json()
            if not items:
                break

            pull_requests.extend(normalize_pull_request(item) for item in items)
            page += 1

    return pull_requests
