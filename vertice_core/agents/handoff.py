"""
HandoffManager - Agent Transfer System.

Implements agent handoff patterns from Big 3 (Dec 2025):
- OpenAI Swarm: Handoff via function returns
- Anthropic Claude: Subagent spawning
- LangGraph: Conditional edges

Features:
- Capability-based agent matching
- Escalation chains (A failed → B more capable)
- Parallel handoffs (A + B simultaneously)
- State preservation during transfers
- Handoff protocols and contracts

Phase 10: Sprint 2 - Agent Rewrite

Soli Deo Gloria
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
)

from .context import DecisionType, UnifiedContext
from .router import AgentType

logger = logging.getLogger(__name__)


class HandoffStatus(str, Enum):
    """Status of a handoff."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class HandoffReason(str, Enum):
    """Reason for handoff."""

    TASK_COMPLETION = "task_completion"  # Normal flow
    CAPABILITY_REQUIRED = "capability_required"  # Need different skills
    ESCALATION = "escalation"  # Current agent cannot handle
    SPECIALIZATION = "specialization"  # Delegate to specialist
    PARALLEL_EXECUTION = "parallel_execution"  # Run in parallel
    USER_REQUEST = "user_request"  # User explicitly asked
    ERROR_RECOVERY = "error_recovery"  # Recovering from error


@dataclass
class AgentCapability:
    """Capabilities of an agent."""

    agent_type: AgentType
    capabilities: Set[str] = field(default_factory=set)
    max_complexity: str = "complex"  # simple, moderate, complex
    can_plan: bool = False
    can_execute: bool = True
    can_review: bool = False
    priority: int = 0  # Higher = preferred for escalation
    description: str = ""

    def can_handle(self, required: Set[str]) -> bool:
        """Check if agent can handle required capabilities."""
        return required.issubset(self.capabilities)


# Default agent capabilities
DEFAULT_CAPABILITIES: Dict[AgentType, AgentCapability] = {
    AgentType.PLANNER: AgentCapability(
        agent_type=AgentType.PLANNER,
        capabilities={"planning", "decomposition", "strategy"},
        can_plan=True,
        can_execute=False,
        priority=5,
        description="Creates execution plans and strategies",
    ),
    AgentType.EXECUTOR: AgentCapability(
        agent_type=AgentType.EXECUTOR,
        capabilities={"execution", "coding", "file_ops"},
        can_plan=False,
        can_execute=True,
        priority=3,
        description="Executes code changes and file operations",
    ),
    AgentType.REVIEWER: AgentCapability(
        agent_type=AgentType.REVIEWER,
        capabilities={"review", "quality", "best_practices"},
        can_plan=False,
        can_execute=False,
        can_review=True,
        priority=4,
        description="Reviews code for quality and issues",
    ),
    AgentType.ARCHITECT: AgentCapability(
        agent_type=AgentType.ARCHITECT,
        capabilities={"architecture", "design", "system", "planning"},
        can_plan=True,
        can_execute=False,
        priority=6,
        description="Designs system architecture",
    ),
    AgentType.EXPLORER: AgentCapability(
        agent_type=AgentType.EXPLORER,
        capabilities={"exploration", "search", "understanding"},
        can_plan=False,
        can_execute=False,
        priority=2,
        description="Explores and understands codebase",
    ),
    AgentType.SECURITY: AgentCapability(
        agent_type=AgentType.SECURITY,
        capabilities={"security", "vulnerability", "audit", "review"},
        can_plan=False,
        can_execute=False,
        can_review=True,
        priority=5,
        description="Security analysis and audit",
    ),
    AgentType.TESTING: AgentCapability(
        agent_type=AgentType.TESTING,
        capabilities={"testing", "test_writing", "coverage"},
        can_plan=False,
        can_execute=True,
        priority=3,
        description="Writes and runs tests",
    ),
    AgentType.CHAT: AgentCapability(
        agent_type=AgentType.CHAT,
        capabilities={"conversation", "explanation"},
        can_plan=False,
        can_execute=False,
        priority=1,
        description="General conversation",
    ),
}


@dataclass
class HandoffRequest:
    """A request to hand off to another agent."""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    from_agent: AgentType = AgentType.CHAT
    to_agent: Optional[AgentType] = None  # None = auto-select
    reason: HandoffReason = HandoffReason.TASK_COMPLETION
    required_capabilities: Set[str] = field(default_factory=set)

    # Context to transfer
    message: str = ""  # Message to pass to next agent
    context_updates: Dict[str, Any] = field(default_factory=dict)
    preserve_history: bool = True

    # Constraints
    timeout_seconds: float = 60.0
    allow_escalation: bool = True

    # State
    status: HandoffStatus = HandoffStatus.PENDING
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

    # Result
    actual_to_agent: Optional[AgentType] = None
    error: Optional[str] = None


@dataclass
class HandoffResult:
    """Result of a handoff operation."""

    request_id: str
    success: bool
    from_agent: AgentType
    to_agent: AgentType
    duration_ms: float = 0.0
    message: str = ""
    error: Optional[str] = None


@dataclass
class EscalationChain:
    """Chain of agents for escalation."""

    name: str
    chain: List[AgentType]
    description: str = ""

    def get_next(self, current: AgentType) -> Optional[AgentType]:
        """Get next agent in escalation chain."""
        try:
            idx = self.chain.index(current)
            if idx + 1 < len(self.chain):
                return self.chain[idx + 1]
        except ValueError:
            pass
        return None


# Default escalation chains
DEFAULT_ESCALATION_CHAINS: List[EscalationChain] = [
    EscalationChain(
        name="execution",
        chain=[AgentType.EXECUTOR, AgentType.PLANNER, AgentType.ARCHITECT],
        description="Escalate execution failures to planning",
    ),
    EscalationChain(
        name="review",
        chain=[AgentType.REVIEWER, AgentType.SECURITY, AgentType.ARCHITECT],
        description="Escalate review to security to architect",
    ),
    EscalationChain(
        name="exploration",
        chain=[AgentType.EXPLORER, AgentType.ARCHITECT],
        description="Escalate exploration to architecture",
    ),
]


class HandoffManager:
    """
    Manages agent handoffs and transfers.

    Implements the Swarm pattern where agents return handoffs
    as function results, enabling seamless transfers.

    Usage:
        manager = HandoffManager(context)
        request = manager.create_handoff(
            to_agent=AgentType.REVIEWER,
            reason=HandoffReason.TASK_COMPLETION
        )
        result = await manager.execute_handoff(request)
    """

    def __init__(
        self,
        context: UnifiedContext,
        capabilities: Optional[Dict[AgentType, AgentCapability]] = None,
        escalation_chains: Optional[List[EscalationChain]] = None,
    ):
        """
        Initialize handoff manager.

        Args:
            context: Unified context for state management
            capabilities: Agent capabilities mapping
            escalation_chains: Escalation chain definitions
        """
        self.context = context
        self.capabilities = capabilities or DEFAULT_CAPABILITIES.copy()
        self.escalation_chains = escalation_chains or DEFAULT_ESCALATION_CHAINS.copy()

        # History
        self._handoff_history: List[HandoffResult] = []
        self._pending_handoffs: List[HandoffRequest] = []

        # Callbacks
        self._pre_handoff: Optional[Callable[[HandoffRequest], bool]] = None
        self._post_handoff: Optional[Callable[[HandoffResult], None]] = None

    # =========================================================================
    # Handoff Creation
    # =========================================================================

    def create_handoff(
        self,
        to_agent: Optional[AgentType] = None,
        reason: HandoffReason = HandoffReason.TASK_COMPLETION,
        message: str = "",
        required_capabilities: Optional[Set[str]] = None,
        context_updates: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> HandoffRequest:
        """
        Create a handoff request.

        Args:
            to_agent: Target agent (None for auto-select)
            reason: Reason for handoff
            message: Message to pass to target
            required_capabilities: Capabilities needed
            context_updates: Context variables to update
            **kwargs: Additional request parameters

        Returns:
            HandoffRequest object
        """
        from_agent = AgentType(self.context.current_agent or "chat")

        request = HandoffRequest(
            from_agent=from_agent,
            to_agent=to_agent,
            reason=reason,
            message=message,
            required_capabilities=required_capabilities or set(),
            context_updates=context_updates or {},
            **kwargs,
        )

        logger.debug(f"Created handoff request: {from_agent.value} → {to_agent}")
        return request

    def create_swarm_handoff(
        self,
        agent_type: AgentType,
        context_updates: Optional[Dict[str, Any]] = None,
    ) -> HandoffRequest:
        """
        Create a Swarm-style handoff (simple function return).

        This is the pattern used by OpenAI Swarm where agents
        return a handoff object to transfer control.

        Args:
            agent_type: Agent to transfer to
            context_updates: Variables to update

        Returns:
            HandoffRequest ready for execution
        """
        return self.create_handoff(
            to_agent=agent_type,
            reason=HandoffReason.TASK_COMPLETION,
            context_updates=context_updates,
        )

    # =========================================================================
    # Agent Selection
    # =========================================================================

    def select_agent(
        self,
        required_capabilities: Set[str],
        exclude: Optional[Set[AgentType]] = None,
        prefer_escalation: bool = False,
    ) -> Optional[AgentType]:
        """
        Select best agent for required capabilities.

        Args:
            required_capabilities: Capabilities needed
            exclude: Agents to exclude
            prefer_escalation: Prefer higher-priority agents

        Returns:
            Best matching AgentType or None
        """
        exclude = exclude or set()
        candidates: List[Tuple[AgentType, int]] = []

        for agent_type, capability in self.capabilities.items():
            if agent_type in exclude:
                continue

            if capability.can_handle(required_capabilities):
                score = capability.priority
                if prefer_escalation:
                    score *= 2  # Boost priority
                candidates.append((agent_type, score))

        if not candidates:
            return None

        # Sort by score (highest first)
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def get_escalation_target(
        self,
        current_agent: AgentType,
        chain_name: Optional[str] = None,
    ) -> Optional[AgentType]:
        """
        Get next agent in escalation chain.

        Args:
            current_agent: Current agent that needs escalation
            chain_name: Specific chain to use (None = auto-detect)

        Returns:
            Next agent in chain or None
        """
        # Find applicable chain
        chains = self.escalation_chains

        if chain_name:
            chains = [c for c in chains if c.name == chain_name]

        for chain in chains:
            next_agent = chain.get_next(current_agent)
            if next_agent:
                return next_agent

        return None

    # =========================================================================
    # Handoff Execution
    # =========================================================================

    async def execute_handoff(
        self,
        request: HandoffRequest,
    ) -> HandoffResult:
        """
        Execute a handoff request.

        Args:
            request: The handoff request

        Returns:
            HandoffResult with outcome
        """
        start_time = time.time()
        request.status = HandoffStatus.IN_PROGRESS

        try:
            # Pre-handoff callback
            if self._pre_handoff:
                if not self._pre_handoff(request):
                    request.status = HandoffStatus.REJECTED
                    return HandoffResult(
                        request_id=request.request_id,
                        success=False,
                        from_agent=request.from_agent,
                        to_agent=request.from_agent,
                        error="Handoff rejected by pre-handoff hook",
                    )

            # Select target agent if not specified
            target_agent = request.to_agent

            if target_agent is None:
                if request.required_capabilities:
                    target_agent = self.select_agent(request.required_capabilities)
                elif request.reason == HandoffReason.ESCALATION:
                    target_agent = self.get_escalation_target(request.from_agent)

            if target_agent is None:
                request.status = HandoffStatus.FAILED
                return HandoffResult(
                    request_id=request.request_id,
                    success=False,
                    from_agent=request.from_agent,
                    to_agent=request.from_agent,
                    error="No suitable agent found for handoff",
                )

            request.actual_to_agent = target_agent

            # Update context
            if request.context_updates:
                self.context.update(request.context_updates)

            # Record decision
            self.context.record_decision(
                decision_type=DecisionType.HANDOFF,
                description=f"Handoff: {request.from_agent.value} → {target_agent.value}",
                agent_id=request.from_agent.value,
                reasoning=f"Reason: {request.reason.value}",
            )

            # Update current agent
            self.context.current_agent = target_agent.value

            # Complete
            request.status = HandoffStatus.COMPLETED
            request.completed_at = time.time()

            duration_ms = (time.time() - start_time) * 1000

            result = HandoffResult(
                request_id=request.request_id,
                success=True,
                from_agent=request.from_agent,
                to_agent=target_agent,
                duration_ms=duration_ms,
                message=f"Handoff complete: {request.from_agent.value} → {target_agent.value}",
            )

            # Record history
            self._handoff_history.append(result)

            # Post-handoff callback
            if self._post_handoff:
                self._post_handoff(result)

            logger.info(f"Handoff completed: {request.from_agent.value} → {target_agent.value}")
            return result

        except Exception as e:
            request.status = HandoffStatus.FAILED
            request.error = str(e)

            return HandoffResult(
                request_id=request.request_id,
                success=False,
                from_agent=request.from_agent,
                to_agent=request.to_agent or request.from_agent,
                error=str(e),
            )

    async def execute_parallel_handoffs(
        self,
        requests: List[HandoffRequest],
    ) -> List[HandoffResult]:
        """
        Execute multiple handoffs in parallel.

        Useful for fan-out patterns where multiple agents
        work simultaneously.

        Args:
            requests: List of handoff requests

        Returns:
            List of results
        """
        tasks = [self.execute_handoff(req) for req in requests]
        return await asyncio.gather(*tasks)

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    async def escalate(
        self,
        reason: str = "",
        chain_name: Optional[str] = None,
    ) -> HandoffResult:
        """
        Escalate to next agent in chain.

        Args:
            reason: Reason for escalation
            chain_name: Specific chain to use

        Returns:
            HandoffResult
        """
        current = AgentType(self.context.current_agent or "chat")
        target = self.get_escalation_target(current, chain_name)

        if not target:
            return HandoffResult(
                request_id=str(uuid.uuid4())[:8],
                success=False,
                from_agent=current,
                to_agent=current,
                error="No escalation target available",
            )

        request = self.create_handoff(
            to_agent=target,
            reason=HandoffReason.ESCALATION,
            message=reason,
        )

        return await self.execute_handoff(request)

    async def delegate_to(
        self,
        agent_type: AgentType,
        task: str = "",
        context_updates: Optional[Dict[str, Any]] = None,
    ) -> HandoffResult:
        """
        Delegate task to specific agent.

        Args:
            agent_type: Target agent
            task: Task description
            context_updates: Context to pass

        Returns:
            HandoffResult
        """
        request = self.create_handoff(
            to_agent=agent_type,
            reason=HandoffReason.SPECIALIZATION,
            message=task,
            context_updates=context_updates,
        )

        return await self.execute_handoff(request)

    async def return_to_caller(
        self,
        result: str = "",
    ) -> HandoffResult:
        """
        Return control to the agent that initiated the handoff.

        Swarm pattern for completing delegated work.

        Args:
            result: Result message

        Returns:
            HandoffResult
        """
        # Find previous agent from history
        if self._handoff_history:
            last = self._handoff_history[-1]
            target = last.from_agent
        else:
            target = AgentType.CHAT

        request = self.create_handoff(
            to_agent=target,
            reason=HandoffReason.TASK_COMPLETION,
            message=result,
        )

        return await self.execute_handoff(request)

    # =========================================================================
    # State & History
    # =========================================================================

    def get_history(self) -> List[HandoffResult]:
        """Get handoff history."""
        return self._handoff_history.copy()

    def get_current_agent(self) -> AgentType:
        """Get current active agent."""
        return AgentType(self.context.current_agent or "chat")

    def get_handoff_chain(self) -> List[AgentType]:
        """Get the chain of agents visited via handoffs."""
        chain = []
        for result in self._handoff_history:
            if result.success:
                if not chain:
                    chain.append(result.from_agent)
                chain.append(result.to_agent)
        return chain

    def get_stats(self) -> Dict[str, Any]:
        """Get handoff statistics."""
        total = len(self._handoff_history)
        successful = sum(1 for h in self._handoff_history if h.success)

        return {
            "total_handoffs": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": f"{successful / max(total, 1) * 100:.1f}%",
            "current_agent": self.get_current_agent().value,
            "chain_length": len(self.get_handoff_chain()),
        }

    # =========================================================================
    # Callbacks
    # =========================================================================

    def set_pre_handoff(
        self,
        callback: Callable[[HandoffRequest], bool],
    ) -> None:
        """
        Set pre-handoff callback.

        Return False to reject handoff.
        """
        self._pre_handoff = callback

    def set_post_handoff(
        self,
        callback: Callable[[HandoffResult], None],
    ) -> None:
        """Set post-handoff callback."""
        self._post_handoff = callback


# Swarm-style handoff helper
def handoff(
    agent_type: AgentType,
    **context_updates: Any,
) -> HandoffRequest:
    """
    Create a Swarm-style handoff.

    This function mimics OpenAI Swarm's pattern where
    agents can return a handoff to transfer control.

    Usage in agent:
        def run(context):
            if needs_review:
                return handoff(AgentType.REVIEWER, review_type="security")
            return "Task completed"

    Args:
        agent_type: Agent to transfer to
        **context_updates: Variables to update

    Returns:
        HandoffRequest for execution
    """
    return HandoffRequest(
        to_agent=agent_type,
        reason=HandoffReason.TASK_COMPLETION,
        context_updates=context_updates,
    )


__all__ = [
    "HandoffStatus",
    "HandoffReason",
    "AgentCapability",
    "HandoffRequest",
    "HandoffResult",
    "EscalationChain",
    "HandoffManager",
    "handoff",
    "DEFAULT_CAPABILITIES",
    "DEFAULT_ESCALATION_CHAINS",
]
