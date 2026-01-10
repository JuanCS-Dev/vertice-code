"""
Error Tracking Mixin - Records and manages execution errors.
"""

from typing import Any, Dict, List, Optional

from ..types import ErrorContext


class ErrorTrackingMixin:
    """Mixin for tracking execution errors."""

    def __init__(self) -> None:
        self._errors: List[ErrorContext] = []

    def record_error(
        self,
        error: Exception,
        agent_id: str = "",
        step_id: Optional[str] = None,
        stack_trace: Optional[str] = None,
        recovery_attempted: bool = False,
        recovery_successful: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an execution error."""
        error_ctx = ErrorContext(
            error_type=type(error).__name__,
            error_message=str(error),
            agent_id=agent_id,
            step_id=step_id,
            stack_trace=stack_trace,
            recovery_attempted=recovery_attempted,
            recovery_successful=recovery_successful,
            metadata=metadata or {},
        )
        self._errors.append(error_ctx)

    def get_errors(
        self,
        agent_id: Optional[str] = None,
        step_id: Optional[str] = None,
        limit: int = 0,
    ) -> List[ErrorContext]:
        """Get recorded errors with optional filtering."""
        errors = self._errors

        if agent_id:
            errors = [e for e in errors if e.agent_id == agent_id]

        if step_id:
            errors = [e for e in errors if e.step_id == step_id]

        if limit > 0:
            errors = errors[-limit:]

        return errors.copy()
