"""Agent handoff system for multi-agent coordination."""

from typing import Any

from .types import (
    HandoffStatus,
    HandoffReason,
    AgentCapability,
    HandoffRequest,
    HandoffResult,
    EscalationChain,
)
from .config import DEFAULT_CAPABILITIES, DEFAULT_ESCALATION_CHAINS
from .selection import AgentSelector
from .manager import HandoffManager
from ..router import AgentType

__all__ = [
    "HandoffStatus",
    "HandoffReason",
    "AgentCapability",
    "HandoffRequest",
    "HandoffResult",
    "EscalationChain",
    "DEFAULT_CAPABILITIES",
    "DEFAULT_ESCALATION_CHAINS",
    "AgentSelector",
    "HandoffManager",
    "handoff",
]


def handoff(
    agent_type: AgentType,
    **context_updates: Any,
) -> HandoffRequest:
    """
    Create a Swarm-style handoff.
    """
    return HandoffRequest(
        to_agent=agent_type,
        reason=HandoffReason.TASK_COMPLETION,
        context_updates=context_updates,
    )
