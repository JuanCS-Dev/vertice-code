"""
Auto-Recovery Loop System

Implements Constitutional Layer 4 (Execution): Verify-Fix-Execute loop
- Detects errors automatically
- Sends error + context to LLM for analysis
- LLM suggests correction
- Re-executes with corrected command
- Max 2 iterations with mandatory diagnosis (Constitutional P6)

Inspired by:
- Claude Code: Self-healing code execution
- GitHub Copilot: Error correction suggestions
- Cursor AI: Context-aware debugging

DAY 7 ENHANCEMENTS:
- Exponential backoff with jitter
- Circuit breaker pattern
- Sophisticated retry policies

Usage:
    from vertice_core.core.recovery import (
        ErrorRecoveryEngine,
        RecoveryContext,
        RecoveryResult,
        ErrorCategory,
        RecoveryStrategy,
    )

    engine = ErrorRecoveryEngine(llm_client)
    result = await engine.attempt_recovery(context)
"""

from .types import (
    ErrorCategory,
    RecoveryStrategy,
    RecoveryContext,
    RecoveryResult,
)
from .retry_policy import RetryPolicy
from .circuit_breaker import RecoveryCircuitBreaker
from .engine import ErrorRecoveryEngine
from .helpers import create_recovery_context

__all__ = [
    # Types
    "ErrorCategory",
    "RecoveryStrategy",
    "RecoveryContext",
    "RecoveryResult",
    # Components
    "RetryPolicy",
    "RecoveryCircuitBreaker",
    "ErrorRecoveryEngine",
    # Helpers
    "create_recovery_context",
]
