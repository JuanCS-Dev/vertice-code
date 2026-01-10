"""
Core exceptions for Vertice platform.

Provides base exception classes and common error types.
"""

from typing import Optional, Dict, Any


class VerticeError(Exception):
    """
    Base exception for all Vertice-related errors.

    Provides consistent error handling across the platform.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.

        Args:
            message: Human-readable error message.
            details: Optional additional error details.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(VerticeError):
    """Raised when there's a configuration-related error."""

    pass


class ValidationError(VerticeError):
    """Raised when input validation fails."""

    pass


class AuthenticationError(VerticeError):
    """Raised when authentication fails."""

    pass


class AuthorizationError(VerticeError):
    """Raised when authorization fails."""

    pass


class ResourceNotFoundError(VerticeError):
    """Raised when a requested resource is not found."""

    pass


class ExternalServiceError(VerticeError):
    """Raised when an external service call fails."""

    pass
