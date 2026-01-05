"""
Error Types - Shared types for error handling.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class EscalationLevel(str, Enum):
    """Escalation levels in order of severity."""

    RETRY = "retry"
    ADJUST = "adjust"
    FALLBACK = "fallback"
    DECOMPOSE = "decompose"
    HUMAN = "human"


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class ExecutionContext:
    """Context for error recovery."""

    operation: str
    args: Dict[str, Any] = field(default_factory=dict)
    attempt: int = 0
    max_retries: int = 3
    provider: Optional[str] = None
    tool: Optional[str] = None
    original_error: Optional[Exception] = None
    history: List[str] = field(default_factory=list)


@dataclass
class Recovery:
    """Result of a recovery attempt."""

    success: bool
    result: Any = None
    strategy_used: EscalationLevel = EscalationLevel.RETRY
    attempts: int = 0
    message: str = ""


class UnrecoverableError(Exception):
    """
    Raised when an operation fails with a non-transient error.

    This exception signals that further retry attempts for the same operation
    are futile, as the underlying cause is not expected to resolve on its own
    (e.g., invalid API key, malformed request, authentication failure).

    When to raise:
      - After exhausting all retry and fallback strategies.
      - When a validation error makes the request permanently invalid.

    How to handle:
      - Log the error for debugging.
      - Terminate the current workflow gracefully.
      - Escalate to a human for manual intervention.
    """

    pass


class ToolExecutionError(Exception):
    """
    Raised when one or more tools fail during parallel execution.

    This exception aggregates multiple underlying errors into a single report,
    providing a comprehensive summary of all failures. It is specifically used
    in contexts where tools are run concurrently, and `return_exceptions=True`
    might otherwise hide individual errors.

    When to raise:
      - When `asyncio.gather` collects multiple exceptions from tool executions.

    How to handle:
      - Log the full error message, which contains details for each failed tool.
      - Use the aggregated information to inform recovery or rollback strategies.
      - Present a consolidated error report to the user.
    """

    pass


class CircuitOpenError(Exception):
    """
    Raised when an operation is blocked by an open circuit breaker.

    This indicates that the associated service has been deemed unavailable due
    to a high rate of recent failures. The circuit breaker is intentionally
    preventing new requests to allow the downstream service time to recover.

    When to raise:
      - By a circuit breaker implementation before executing a guarded call.

    How to handle:
      - Immediately route the request to a fallback provider, if available.
      - If no fallback exists, fail fast and inform the user.
      - Do not retry the same operation against the same provider until the
        circuit transitions to half-open or closed.
    """

    pass


# Type aliases for callbacks
DecomposeCallback = Callable[[str], List[str]]
HumanCallback = Callable[[str, Exception], str]
