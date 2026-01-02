"""
Error Handling Package - Modular error recovery system.

Exports:
- ErrorEscalationHandler: Tiered error recovery
- EnhancedCircuitBreaker: Gradual recovery pattern
- Types: EscalationLevel, CircuitState, ExecutionContext, Recovery

Reference: HEROIC_IMPLEMENTATION_PLAN.md Sprint 3
Follows CODE_CONSTITUTION: Modular, <500 lines per file
"""

from .types import (
    CircuitOpenError,
    CircuitState,
    DecomposeCallback,
    EscalationLevel,
    ExecutionContext,
    HumanCallback,
    Recovery,
    UnrecoverableError,
)

from .escalation import (
    ErrorEscalationHandler,
    get_escalation_handler,
)

from .circuit_breaker import (
    EnhancedCircuitBreaker,
    get_circuit_breaker,
    reset_all_circuits,
)

__all__ = [
    # Types
    "EscalationLevel",
    "CircuitState",
    "ExecutionContext",
    "Recovery",
    "UnrecoverableError",
    "CircuitOpenError",
    "DecomposeCallback",
    "HumanCallback",
    # Escalation
    "ErrorEscalationHandler",
    "get_escalation_handler",
    # Circuit Breaker
    "EnhancedCircuitBreaker",
    "get_circuit_breaker",
    "reset_all_circuits",
]
