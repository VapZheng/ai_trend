class DashboardError(Exception):
    """Base error for dashboard operations."""


class ConflictError(DashboardError):
    """Raised when a refresh is already running."""


class ValidationError(DashboardError):
    """Raised when request parameters are invalid."""
