from app.core.config import get_settings
from app.models.pull_request import PullRequestState
from app.utils.github import fetch_repository_pull_requests, normalize_pull_request


def _github_pr_payload(**overrides):
    payload = {
        "id": 1001,
        "number": 12,
        "title": "Add authentication middleware",
        "body": "PR description",
        "state": "open",
        "user": {"login": "octocat"},
        "head": {"ref": "feature/auth"},
        "base": {"ref": "main"},
        "created_at": "2026-01-01T10:00:00Z",
        "updated_at": "2026-01-02T10:00:00Z",
        "closed_at": None,
        "merged_at": None,
        "draft": False,
        "html_url": "https://github.com/octocat/Hello-World/pull/12",
    }
    payload.update(overrides)
    return payload


def test_normalize_pull_request_open_state():
    draft = normalize_pull_request(_github_pr_payload())

    assert draft.state == PullRequestState.OPEN
    assert draft.is_merged is False
    assert draft.author_username == "octocat"
    assert draft.source_branch == "feature/auth"
    assert draft.target_branch == "main"


def test_normalize_pull_request_merged_state():
    draft = normalize_pull_request(
        _github_pr_payload(
            state="closed",
            merged_at="2026-01-03T10:00:00Z",
            closed_at="2026-01-03T10:00:00Z",
        )
    )

    assert draft.state == PullRequestState.MERGED
    assert draft.is_merged is True


class _FakeResponse:
    def __init__(self, status_code: int, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _FakeAsyncClient:
    requests = []
    pages = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def get(self, url, headers=None, params=None):
        self.requests.append({"url": url, "headers": headers, "params": params})
        return _FakeResponse(200, self.pages.pop(0))


async def test_fetch_repository_pull_requests_paginates(monkeypatch):
    _FakeAsyncClient.requests = []
    _FakeAsyncClient.pages = [
        [_github_pr_payload(id=1001, number=1)],
        [_github_pr_payload(id=1002, number=2, state="closed")],
        [],
    ]
    monkeypatch.setattr("app.utils.github.httpx.AsyncClient", _FakeAsyncClient)

    pull_requests = await fetch_repository_pull_requests(
        "octocat",
        "Hello-World",
        get_settings(),
    )

    assert [item.number for item in pull_requests] == [1, 2]
    assert [request["params"]["page"] for request in _FakeAsyncClient.requests] == [1, 2, 3]
    assert all(request["params"]["state"] == "all" for request in _FakeAsyncClient.requests)
