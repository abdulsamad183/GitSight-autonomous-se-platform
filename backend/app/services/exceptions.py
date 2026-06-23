class AppError(Exception):
    """Base application error."""


class ConflictError(AppError):
    """Resource conflict (e.g. duplicate email)."""


class AuthenticationError(AppError):
    """Authentication failed."""


class ValidationError(AppError):
    """Invalid input."""


class NotFoundError(AppError):
    """Resource not found."""


class ForbiddenError(AppError):
    """Access denied."""


class AnalysisError(AppError):
    """Repository analysis failed."""
