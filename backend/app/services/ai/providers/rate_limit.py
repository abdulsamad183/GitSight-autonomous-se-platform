from groq import APIStatusError, RateLimitError


def is_rate_limit_error(exc: Exception) -> bool:
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, APIStatusError) and exc.status_code == 429:
        return True
    message = str(exc).lower()
    return "rate limit" in message or "429" in message
