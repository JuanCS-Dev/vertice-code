"""Handoff Manager implementation."""

from __future__ import annotations
import logging
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from ..context import UnifiedContext
from ..router import AgentType
from .types import (
    HandoffReason,
    HandoffRequest,
    HandoffResult,
    AgentCapability,
    EscalationChain,
)
from .config import DEFAULT_CAPABILITIES, DEFAULT_ESCALATION_CHAINS
from .selection import AgentSelector

logger = logging.getLogger(__name__)


class HandoffManager:
    """Manages agent handoffs and transfers."""

    def __init__(
        self,
        context: UnifiedContext,
        capabilities: Optional[Dict[AgentType, AgentCapability]] = None,
        escalation_chains: Optional[List[EscalationChain]] = None,
    ):
        if context is None:
            raise AttributeError("Context cannot be None")

        self.context = context
        self.capabilities = capabilities or DEFAULT_CAPABILITIES.copy()
        self.escalation_chains = escalation_chains or DEFAULT_ESCALATION_CHAINS.copy()
        self.selector = AgentSelector(self.capabilities, self.escalation_chains)
        self._handoff_history: List[HandoffResult] = []
        self._pending_handoffs: List[HandoffRequest] = []
        self._pre_handoff: Optional[Callable[[HandoffRequest], bool]] = None
        self._post_handoff: Optional[Callable[[HandoffResult], None]] = None

    def create_handoff(
        self,
        from_agent: AgentType,
        to_agent: AgentType,
        reason: HandoffReason,
        context_updates: Optional[Dict[str, Any]] = None,
        message: str = "",
    ) -> HandoffResult:
        """Create a new handoff request."""
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # Create handoff request
        request = HandoffRequest(
            request_id=request_id,
            from_agent=from_agent,
            to_agent=to_agent,
            reason=reason,
            message=message,
            context_updates=context_updates or {},
        )

        # Execute the handoff (simplified for now)
        duration = (time.time() - start_time) * 1000

        result = HandoffResult(
            request_id=request_id,
            success=True,
            from_agent=from_agent,
            to_agent=to_agent,
            duration_ms=duration,
            message=f"Handoff completed from {from_agent.value.upper()} to {to_agent.value.upper()}",
            request=request,
        )

        self._handoff_history.append(result)
        return result

    def return_to_caller(self, result: str = "") -> HandoffResult:
        if self._handoff_history:
            last = self._handoff_history[-1]
            target = last.from_agent
        else:
            target = AgentType.CHAT

        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # Create handoff request
        request = HandoffRequest(
            request_id=request_id,
            from_agent=AgentType.CHAT,
            to_agent=target,
            reason=HandoffReason.TASK_COMPLETION,
            message=result,
            context_updates={},
        )

        # Execute the handoff (simplified for now)
        duration = (time.time() - start_time) * 1000

        handoff_result = HandoffResult(
            request_id=request_id,
            success=True,
            from_agent=AgentType.CHAT,
            to_agent=target,
            duration_ms=duration,
            message=result or "Task completed",
            request=request,
        )

        self._handoff_history.append(handoff_result)
        return handoff_result

    def get_history(self) -> List[HandoffResult]:
        """Get handoff history."""
        return self._handoff_history.copy()

    def get_current_agent(self) -> AgentType:
        """Get currently active agent from handoff history."""
        if self._handoff_history:
            return self._handoff_history[-1].to_agent
        return AgentType.CHAT

    def get_handoff_chain(self) -> List[AgentType]:
        """Get the chain of agents involved in successful handoffs."""
        chain: List[AgentType] = []
        for result in self._handoff_history:
            if result.success:
                if not chain:
                    chain.append(result.from_agent)
                chain.append(result.to_agent)
        return chain

    def get_stats(self) -> Dict[str, Any]:
        """Get handoff statistics and metrics."""
        total = len(self._handoff_history)
        successful = sum(1 for h in self._handoff_history if h.success)
        failed = total - successful
        durations = [h.duration_ms for h in self._handoff_history if h.success]
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        return {
            "total_handoffs": total,
            "successful_handoffs": successful,
            "failed_handoffs": failed,
            "success_rate": f"{successful / max(total, 1) * 100:.1f}%",
            "avg_duration_ms": avg_duration,
            "current_agent": self.get_current_agent().value,
            "chain_length": len(self.get_handoff_chain()),
        }

    def set_pre_handoff(self, callback: Callable[[HandoffRequest], bool]) -> None:
        """Set callback to run before handoff execution."""
        self._pre_handoff = callback

    def set_post_handoff(self, callback: Callable[[HandoffResult], None]) -> None:
        """Set callback to run after handoff completion."""
        self._post_handoff = callback
