import re
from dataclasses import dataclass

import httpx

from app.core.config import Settings
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


async def validate_public_repo(owner: str, repo: str, settings: Settings) -> None:
    headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    url = f"https://api.github.com/repos/{owner}/{repo}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, headers=headers)

    if response.status_code == 404:
        raise NotFoundError("Repository not found")
    if response.status_code == 403:
        raise ForbiddenError("Repository is private or access is denied")
    if response.status_code != 200:
        raise ValidationError("Unable to validate GitHub repository")
