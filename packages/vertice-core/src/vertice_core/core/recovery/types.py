"""
Recovery Types - Enums and Data Classes.

Contains error categories, recovery strategies, and context/result dataclasses.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class ErrorCategory(Enum):
    """Error categories for recovery strategies."""

    SYNTAX = "syntax"
    PERMISSION = "permission"
    NOT_FOUND = "not_found"
    COMMAND_NOT_FOUND = "command_not_found"
    TIMEOUT = "timeout"
    TYPE_ERROR = "type_error"
    VALUE_ERROR = "value_error"
    NETWORK = "network"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""

    RETRY_MODIFIED = "retry_modified"
    RETRY_ALTERNATIVE = "retry_alternative"
    SUGGEST_INSTALL = "suggest_install"
    SUGGEST_PERMISSION = "suggest_permission"
    ESCALATE = "escalate"
    ABORT = "abort"


@dataclass
class RecoveryContext:
    """Context for error recovery attempt."""

    attempt_number: int
    max_attempts: int
    error: str
    error_category: ErrorCategory
    failed_tool: str
    failed_args: Dict[str, Any]
    previous_result: Any

    # Conversation context
    user_intent: str
    previous_commands: List[Dict[str, Any]]

    # Diagnosis
    diagnosis: Optional[str] = None
    suggested_fix: Optional[str] = None
    recovery_strategy: Optional[RecoveryStrategy] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "attempt": f"{self.attempt_number}/{self.max_attempts}",
            "error": self.error,
            "category": self.error_category.value,
            "tool": self.failed_tool,
            "args": self.failed_args,
            "diagnosis": self.diagnosis,
            "suggested_fix": self.suggested_fix,
            "strategy": self.recovery_strategy.value if self.recovery_strategy else None,
        }


@dataclass
class RecoveryResult:
    """Result of recovery attempt."""

    success: bool
    recovered: bool
    attempts_used: int

    # If recovered
    corrected_tool: Optional[str] = None
    corrected_args: Optional[Dict[str, Any]] = None
    result: Any = None

    # If failed
    final_error: Optional[str] = None
    escalation_reason: Optional[str] = None

    # Learning
    what_worked: Optional[str] = None
    what_failed: Optional[str] = None
