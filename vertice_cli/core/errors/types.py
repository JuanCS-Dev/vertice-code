"""
Error Types - Shared types for error handling.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import time
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
    """Error that cannot be recovered from."""

    pass


class CircuitOpenError(Exception):
    """Raised when attempting to call through an open circuit."""

    pass


# Type aliases for callbacks
DecomposeCallback = Callable[[str], List[str]]
HumanCallback = Callable[[str, Exception], str]
