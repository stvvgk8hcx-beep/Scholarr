"""Custom exceptions for Scholarr."""


class ScholarrException(Exception):
    """Base exception for all Scholarr errors."""

    pass


class ValidationException(ScholarrException):
    """Raised when validation fails."""

    pass


# Alias used in tests and some endpoint code
ValidationError = ValidationException


class NotFoundError(ScholarrException):
    """Raised when a resource is not found."""

    pass


class UnauthorizedError(ScholarrException):
    """Raised when authentication fails."""

    pass


class ForbiddenError(ScholarrException):
    """Raised when authorization fails."""

    pass


class ConflictError(ScholarrException):
    """Raised when there's a conflict (e.g., duplicate)."""

    pass


class FileOperationError(ScholarrException):
    """Raised when a file operation fails."""

    pass


class ImportError(ScholarrException):
    """Raised when import fails."""

    pass


class BackupError(ScholarrException):
    """Raised when backup/restore fails."""

    pass
