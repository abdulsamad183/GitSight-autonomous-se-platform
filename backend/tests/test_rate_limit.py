import httpx
from groq import APIStatusError, AuthenticationError, RateLimitError

from app.services.ai.providers.rate_limit import is_rate_limit_error


def _mock_response(status_code: int) -> httpx.Response:
    return httpx.Response(
        status_code=status_code, request=httpx.Request("POST", "https://api.groq.com")
    )


def test_is_rate_limit_error_groq_rate_limit():
    exc = RateLimitError("rate limit exceeded", response=_mock_response(429), body=None)
    assert is_rate_limit_error(exc) is True


def test_is_rate_limit_error_api_status_429():
    exc = APIStatusError("too many requests", response=_mock_response(429), body=None)
    assert is_rate_limit_error(exc) is True


def test_is_rate_limit_error_message_fallback():
    assert is_rate_limit_error(Exception("HTTP 429 Too Many Requests")) is True
    assert is_rate_limit_error(Exception("Rate limit exceeded")) is True


def test_is_rate_limit_error_auth_error():
    exc = AuthenticationError("invalid api key", response=_mock_response(401), body=None)
    assert is_rate_limit_error(exc) is False


def test_is_rate_limit_error_other_status():
    exc = APIStatusError("server error", response=_mock_response(500), body=None)
    assert is_rate_limit_error(exc) is False


def test_is_rate_limit_error_generic_exception():
    assert is_rate_limit_error(ValueError("something went wrong")) is False
