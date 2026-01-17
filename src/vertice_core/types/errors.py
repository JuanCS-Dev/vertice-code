# Error and recovery types - Domain level

from __future__ import annotations

from typing import Optional, TypedDict
from enum import Enum

from .files import FilePath


class ErrorCategory(str, Enum):
    """Category of error for recovery strategies."""

    SYNTAX = "syntax"
    IMPORT = "import"
    TYPE = "type"
    RUNTIME = "runtime"
    PERMISSION = "permission"
    NETWORK = "network"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


class ErrorInfo(TypedDict):
    """Structured error information."""

    category: ErrorCategory
    message: str
    traceback: Optional[str]
    file: Optional[FilePath]
    line: Optional[int]
    recoverable: bool


class RecoveryStrategy(TypedDict):
    """Strategy for recovering from an error."""

    category: ErrorCategory
    max_attempts: int
    backoff_factor: float
    timeout_seconds: float
    fallback: Optional[str]
