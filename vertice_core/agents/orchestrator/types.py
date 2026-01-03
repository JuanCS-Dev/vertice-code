"""
Orchestrator Types - State machine enums.

Defines the states and transition types for the orchestration state machine.
"""

from enum import Enum, auto


class OrchestratorState(str, Enum):
    """States in the orchestration state machine."""

    # Initial states
    IDLE = "idle"
    INITIALIZING = "initializing"

    # Main loop states
    GATHERING = "gathering"  # Collecting context
    ROUTING = "routing"  # Deciding which agent
    PLANNING = "planning"  # Creating execution plan
    EXECUTING = "executing"  # Running actions
    VERIFYING = "verifying"  # Checking results
    REVIEWING = "reviewing"  # Human/agent review

    # Handoff states
    HANDOFF_PENDING = "handoff_pending"
    HANDOFF_COMPLETE = "handoff_complete"

    # Terminal states
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

    # Error states
    ERROR_RECOVERY = "error_recovery"
    AWAITING_APPROVAL = "awaiting_approval"


class HandoffType(str, Enum):
    """Types of agent handoffs."""

    SEQUENTIAL = "sequential"  # A → B → C
    PARALLEL = "parallel"  # A + B + C simultaneously
    CONDITIONAL = "conditional"  # A → (B if X else C)
    ESCALATION = "escalation"  # A failed → B (more capable)
