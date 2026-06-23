import pytest

from app.services.exceptions import ValidationError
from app.utils.github import parse_github_url


def test_parse_github_url_normalizes():
    parsed = parse_github_url("https://github.com/octocat/Hello-World.git/")
    assert parsed.owner == "octocat"
    assert parsed.repository_name == "Hello-World"
    assert parsed.normalized_url == "https://github.com/octocat/Hello-World"


def test_parse_github_url_http():
    parsed = parse_github_url("http://github.com/foo/bar")
    assert parsed.normalized_url == "https://github.com/foo/bar"


def test_parse_github_url_invalid():
    with pytest.raises(ValidationError):
        parse_github_url("https://gitlab.com/foo/bar")


def test_parse_github_url_empty():
    with pytest.raises(ValidationError):
        parse_github_url("   ")
