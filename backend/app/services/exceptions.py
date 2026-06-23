class AppError(Exception):
    """Base application error."""


class ConflictError(AppError):
    """Resource conflict (e.g. duplicate email)."""


class AuthenticationError(AppError):
    """Authentication failed."""
