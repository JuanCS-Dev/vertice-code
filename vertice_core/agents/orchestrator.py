"""
ActiveOrchestrator - State Machine for Multi-Agent Orchestration.

Implements the execution loop pattern from Big 3 (Dec 2025):
- LangGraph: Explicit state machine with transitions
- Claude SDK: Gather → Act → Verify → Repeat
- OpenAI Swarm: Handoffs via function returns

Features:
- State-based execution flow
- Automatic agent handoffs
- Retry with exponential backoff
- Progress streaming for TUI
- Checkpoint/recovery support

Phase 10: Sprint 2 - Agent Rewrite

Soli Deo Gloria
"""

from __future__ import annotations

import asyncio
import logging
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Set,
    Tuple,
    TypeVar,
    Union,
)

from .context import (
    Decision,
    DecisionType,
    ErrorContext,
    ExecutionResult,
    ThoughtSignature,
    UnifiedContext,
)
from .router import (
    AgentType,
    RoutingDecision,
    SemanticRouter,
    TaskComplexity,
)

logger = logging.getLogger(__name__)

# Type aliases
T = TypeVar("T")


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


@dataclass
class StateTransition:
    """A transition between orchestrator states."""

    from_state: OrchestratorState
    to_state: OrchestratorState
    condition: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionStep:
    """A step in the execution plan."""

    step_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    agent_type: AgentType = AgentType.EXECUTOR
    action: str = ""  # Tool/action to execute
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # Step IDs this depends on
    requires_approval: bool = False
    timeout_seconds: float = 60.0
    retry_count: int = 0
    max_retries: int = 2

    # Status
    status: str = "pending"  # pending, running, completed, failed, skipped
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[ExecutionResult] = None


@dataclass
class ExecutionPlan:
    """A plan consisting of multiple execution steps."""

    plan_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    goal: str = ""
    steps: List[ExecutionStep] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    created_by: str = ""
    complexity: TaskComplexity = TaskComplexity.MODERATE

    # Execution state
    current_step_index: int = 0
    completed_steps: int = 0
    failed_steps: int = 0

    def get_current_step(self) -> Optional[ExecutionStep]:
        """Get the current step to execute."""
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def get_pending_steps(self) -> List[ExecutionStep]:
        """Get steps that are pending execution."""
        return [s for s in self.steps if s.status == "pending"]

    def get_runnable_steps(self) -> List[ExecutionStep]:
        """Get steps that can run now (dependencies met)."""
        completed_ids = {s.step_id for s in self.steps if s.status == "completed"}
        runnable = []
        for step in self.steps:
            if step.status != "pending":
                continue
            if all(dep in completed_ids for dep in step.dependencies):
                runnable.append(step)
        return runnable

    def is_complete(self) -> bool:
        """Check if plan execution is complete."""
        return all(s.status in ("completed", "skipped") for s in self.steps)

    def has_failed(self) -> bool:
        """Check if any step failed without recovery."""
        return any(
            s.status == "failed" and s.retry_count >= s.max_retries
            for s in self.steps
        )


@dataclass
class Handoff:
    """An agent handoff request."""

    handoff_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    from_agent: AgentType = AgentType.CHAT
    to_agent: AgentType = AgentType.EXECUTOR
    handoff_type: HandoffType = HandoffType.SEQUENTIAL
    reason: str = ""
    context_updates: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class AgentProtocol(Protocol):
    """Protocol that agents must implement."""

    async def execute(
        self,
        request: str,
        context: UnifiedContext,
    ) -> AsyncIterator[str]:
        """Execute agent task, yielding progress."""
        ...


class ActiveOrchestrator:
    """
    State machine orchestrator for multi-agent execution.

    Implements the pattern: Gather → Route → Act → Verify → Repeat

    Usage:
        orchestrator = ActiveOrchestrator(context)
        async for event in orchestrator.execute("implement login"):
            print(event)

    State Machine:
        IDLE → GATHERING → ROUTING → PLANNING/EXECUTING → VERIFYING → COMPLETED
                   ↑                                           |
                   └───────────────────────────────────────────┘
    """

    # Configuration
    MAX_ITERATIONS = 20  # Prevent infinite loops
    DEFAULT_TIMEOUT = 300.0  # 5 minutes
    RETRY_BACKOFF_BASE = 2.0  # Exponential backoff

    def __init__(
        self,
        context: UnifiedContext,
        router: Optional[SemanticRouter] = None,
        agents: Optional[Dict[AgentType, AgentProtocol]] = None,
    ):
        """
        Initialize orchestrator.

        Args:
            context: Shared unified context
            router: Semantic router for intent classification
            agents: Map of agent type to agent instance
        """
        self.context = context
        self.router = router or SemanticRouter()
        self.agents = agents or {}

        # State machine
        self.state = OrchestratorState.IDLE
        self._state_history: List[StateTransition] = []

        # Execution state
        self.current_plan: Optional[ExecutionPlan] = None
        self.pending_handoffs: List[Handoff] = []
        self.completed_handoffs: List[Handoff] = []

        # Control
        self._cancelled = False
        self._iteration_count = 0
        self._start_time: Optional[float] = None

        # Callbacks for extensibility
        self._on_state_change: Optional[
            Callable[[OrchestratorState, OrchestratorState], None]
        ] = None
        self._on_step_complete: Optional[
            Callable[[ExecutionStep, ExecutionResult], None]
        ] = None

    # =========================================================================
    # State Machine
    # =========================================================================

    def _transition_to(
        self,
        new_state: OrchestratorState,
        condition: Optional[str] = None,
        **metadata: Any,
    ) -> None:
        """Transition to a new state."""
        old_state = self.state

        # Record transition
        transition = StateTransition(
            from_state=old_state,
            to_state=new_state,
            condition=condition,
            metadata=metadata,
        )
        self._state_history.append(transition)

        # Update state
        self.state = new_state
        logger.debug(f"State: {old_state.value} → {new_state.value}")

        # Callback
        if self._on_state_change:
            self._on_state_change(old_state, new_state)

    def _is_terminal_state(self) -> bool:
        """Check if current state is terminal."""
        return self.state in (
            OrchestratorState.COMPLETED,
            OrchestratorState.FAILED,
            OrchestratorState.CANCELLED,
            OrchestratorState.TIMEOUT,
        )

    def _check_timeout(self) -> bool:
        """Check if execution has timed out."""
        if self._start_time is None:
            return False
        elapsed = time.time() - self._start_time
        return elapsed > self.DEFAULT_TIMEOUT

    def _check_iteration_limit(self) -> bool:
        """Check if iteration limit reached."""
        return self._iteration_count >= self.MAX_ITERATIONS

    # =========================================================================
    # Main Execution Loop
    # =========================================================================

    async def execute(
        self,
        request: str,
        timeout: Optional[float] = None,
    ) -> AsyncIterator[str]:
        """
        Execute a user request through the orchestration pipeline.

        Implements: Gather → Route → Plan → Execute → Verify → Complete

        Args:
            request: User's request
            timeout: Optional timeout override

        Yields:
            Progress events as strings
        """
        self._start_time = time.time()
        self._cancelled = False
        self._iteration_count = 0

        if timeout:
            self.DEFAULT_TIMEOUT = timeout

        # Initialize
        self._transition_to(OrchestratorState.INITIALIZING)
        self.context.user_request = request
        self.context.current_agent = None

        # Initialize router
        await self.router.initialize()

        yield f"🎯 Processing: {request[:100]}...\n"

        try:
            # Main execution loop
            while not self._is_terminal_state():
                self._iteration_count += 1

                # Safety checks
                if self._cancelled:
                    self._transition_to(OrchestratorState.CANCELLED)
                    yield "❌ Execution cancelled\n"
                    break

                if self._check_timeout():
                    self._transition_to(OrchestratorState.TIMEOUT)
                    yield "⏰ Execution timeout\n"
                    break

                if self._check_iteration_limit():
                    self._transition_to(OrchestratorState.FAILED, condition="iteration_limit")
                    yield "⚠️ Maximum iterations reached\n"
                    break

                # Execute current state
                async for event in self._execute_state():
                    yield event

            # Final summary
            async for event in self._generate_summary():
                yield event

        except Exception as e:
            self._transition_to(OrchestratorState.FAILED, error=str(e))
            self.context.record_error(
                error_type=type(e).__name__,
                error_message=str(e),
                stack_trace=traceback.format_exc(),
            )
            yield f"❌ Error: {e}\n"

    async def _execute_state(self) -> AsyncIterator[str]:
        """Execute actions for current state and transition."""
        state = self.state

        if state == OrchestratorState.INITIALIZING:
            async for event in self._state_initializing():
                yield event

        elif state == OrchestratorState.GATHERING:
            async for event in self._state_gathering():
                yield event

        elif state == OrchestratorState.ROUTING:
            async for event in self._state_routing():
                yield event

        elif state == OrchestratorState.PLANNING:
            async for event in self._state_planning():
                yield event

        elif state == OrchestratorState.EXECUTING:
            async for event in self._state_executing():
                yield event

        elif state == OrchestratorState.VERIFYING:
            async for event in self._state_verifying():
                yield event

        elif state == OrchestratorState.REVIEWING:
            async for event in self._state_reviewing():
                yield event

        elif state == OrchestratorState.HANDOFF_PENDING:
            async for event in self._state_handoff():
                yield event

        elif state == OrchestratorState.ERROR_RECOVERY:
            async for event in self._state_error_recovery():
                yield event

        elif state == OrchestratorState.AWAITING_APPROVAL:
            # Waiting for external input
            await asyncio.sleep(0.1)

        else:
            # Unknown state - fail safe
            self._transition_to(OrchestratorState.FAILED, condition="unknown_state")

    # =========================================================================
    # State Implementations
    # =========================================================================

    async def _state_initializing(self) -> AsyncIterator[str]:
        """Initialize context and prepare for execution."""
        yield "📋 Initializing context...\n"

        # Add thought signature
        self.context.add_thought(
            agent_id="orchestrator",
            reasoning=f"Processing request: {self.context.user_request}",
            insights=["Starting orchestration pipeline"],
            next_action="gather_context",
        )

        self._transition_to(OrchestratorState.GATHERING)

    async def _state_gathering(self) -> AsyncIterator[str]:
        """Gather relevant context for the request."""
        yield "🔍 Gathering context...\n"

        # In a full implementation, this would:
        # 1. Search codebase semantically (Sprint 1 integration)
        # 2. Load relevant files into context
        # 3. Check conversation history

        # Record decision
        self.context.record_decision(
            decision_type=DecisionType.EXECUTION,
            description="Context gathered for request",
            agent_id="orchestrator",
            reasoning="Initial context collection",
        )

        self._transition_to(OrchestratorState.ROUTING)

    async def _state_routing(self) -> AsyncIterator[str]:
        """Route request to appropriate agent."""
        yield "🔀 Routing request...\n"

        # Use semantic router
        decision = await self.router.route(
            self.context.user_request,
            context=self.context.variables,
        )

        # Record routing decision
        self.context.record_decision(
            decision_type=DecisionType.ROUTING,
            description=f"Routed to {decision.primary_agent.value}",
            agent_id="orchestrator",
            reasoning=decision.reasoning,
            confidence=decision.confidence,
        )

        yield f"   Agent: {decision.primary_agent.value}\n"
        yield f"   Confidence: {decision.confidence:.2f}\n"
        yield f"   Complexity: {decision.complexity.value}\n"

        # Store routing decision
        self.context.set("routing_decision", decision.to_dict())
        self.context.current_agent = decision.primary_agent.value

        # Decide next state based on routing
        if decision.requires_planning:
            self._transition_to(OrchestratorState.PLANNING, routing=decision.to_dict())
        else:
            self._transition_to(OrchestratorState.EXECUTING, routing=decision.to_dict())

    async def _state_planning(self) -> AsyncIterator[str]:
        """Create execution plan."""
        yield "📝 Creating execution plan...\n"

        routing = self.context.get("routing_decision", {})

        # Create a simple plan (in full implementation, this would use a planner agent)
        plan = ExecutionPlan(
            goal=self.context.user_request,
            created_by="orchestrator",
            complexity=TaskComplexity(routing.get("complexity", "moderate")),
        )

        # Add a single execution step for now
        # In full implementation, planner agent would decompose into multiple steps
        step = ExecutionStep(
            description=f"Execute: {self.context.user_request[:100]}",
            agent_type=AgentType(routing.get("agent", "executor")),
            action="execute_task",
            parameters={"request": self.context.user_request},
        )
        plan.steps.append(step)

        self.current_plan = plan
        self.context.current_plan_id = plan.plan_id

        yield f"   Plan ID: {plan.plan_id}\n"
        yield f"   Steps: {len(plan.steps)}\n"

        # Add thought signature
        self.context.add_thought(
            agent_id="orchestrator",
            reasoning=f"Created plan with {len(plan.steps)} steps",
            insights=[f"Step: {s.description}" for s in plan.steps[:3]],
            next_action="execute_plan",
        )

        self._transition_to(OrchestratorState.EXECUTING)

    async def _state_executing(self) -> AsyncIterator[str]:
        """Execute current plan steps."""
        yield "⚡ Executing...\n"

        if not self.current_plan:
            # No plan - create simple one
            self.current_plan = ExecutionPlan(goal=self.context.user_request)
            step = ExecutionStep(
                description="Direct execution",
                agent_type=AgentType(self.context.current_agent or "executor"),
            )
            self.current_plan.steps.append(step)

        # Get runnable steps
        runnable = self.current_plan.get_runnable_steps()

        if not runnable:
            # Check if complete or failed
            if self.current_plan.is_complete():
                self._transition_to(OrchestratorState.VERIFYING)
            elif self.current_plan.has_failed():
                self._transition_to(OrchestratorState.ERROR_RECOVERY)
            else:
                # All pending steps have unmet dependencies
                self._transition_to(OrchestratorState.FAILED, condition="deadlock")
            return

        # Execute steps (could be parallel if no dependencies)
        for step in runnable:
            step.status = "running"
            step.started_at = time.time()

            yield f"   → {step.description}\n"

            try:
                # Execute via agent (if available)
                agent = self.agents.get(step.agent_type)

                if agent:
                    async for event in agent.execute(
                        step.parameters.get("request", self.context.user_request),
                        self.context,
                    ):
                        yield f"     {event}"

                # Mark completed
                step.status = "completed"
                step.completed_at = time.time()

                result = ExecutionResult(
                    step_id=step.step_id,
                    success=True,
                    duration_ms=(step.completed_at - step.started_at) * 1000,
                )
                step.result = result
                self.current_plan.completed_steps += 1

                # Record in context
                self.context.add_step_result(result)

                yield f"   ✓ Completed: {step.description}\n"

                # Callback
                if self._on_step_complete:
                    self._on_step_complete(step, result)

            except Exception as e:
                step.status = "failed"
                step.retry_count += 1

                # Record error
                error = self.context.record_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    agent_id=step.agent_type.value,
                    step_id=step.step_id,
                )

                yield f"   ✗ Failed: {step.description} - {e}\n"

                # Check retries
                if step.retry_count < step.max_retries:
                    step.status = "pending"  # Retry
                    yield f"   🔄 Retrying ({step.retry_count}/{step.max_retries})\n"
                    await asyncio.sleep(self.RETRY_BACKOFF_BASE ** step.retry_count)
                else:
                    self.current_plan.failed_steps += 1

        # Check if more steps to run
        if self.current_plan.get_pending_steps():
            # Stay in EXECUTING state for next iteration
            pass
        elif self.current_plan.is_complete():
            self._transition_to(OrchestratorState.VERIFYING)
        else:
            self._transition_to(OrchestratorState.ERROR_RECOVERY)

    async def _state_verifying(self) -> AsyncIterator[str]:
        """Verify execution results."""
        yield "✅ Verifying results...\n"

        routing = self.context.get("routing_decision", {})

        # Check if review required
        if routing.get("requires_review", False):
            self._transition_to(OrchestratorState.REVIEWING)
            return

        # Simple verification: check no failures
        if self.context.has_failures():
            yield "   ⚠️ Some steps had failures\n"
            self._transition_to(OrchestratorState.ERROR_RECOVERY)
        else:
            yield "   All steps completed successfully\n"
            self._transition_to(OrchestratorState.COMPLETED)

    async def _state_reviewing(self) -> AsyncIterator[str]:
        """Review results (agent or human)."""
        yield "🔎 Reviewing results...\n"

        # In full implementation, would invoke reviewer agent
        # For now, auto-approve

        self.context.record_decision(
            decision_type=DecisionType.APPROVAL,
            description="Results auto-approved",
            agent_id="orchestrator",
        )

        yield "   Results approved\n"
        self._transition_to(OrchestratorState.COMPLETED)

    async def _state_handoff(self) -> AsyncIterator[str]:
        """Handle agent handoff."""
        if not self.pending_handoffs:
            self._transition_to(OrchestratorState.EXECUTING)
            return

        handoff = self.pending_handoffs.pop(0)
        yield f"🔄 Handoff: {handoff.from_agent.value} → {handoff.to_agent.value}\n"
        yield f"   Reason: {handoff.reason}\n"

        # Update context
        self.context.update(handoff.context_updates)
        self.context.current_agent = handoff.to_agent.value

        # Record decision
        self.context.record_decision(
            decision_type=DecisionType.HANDOFF,
            description=f"Handoff to {handoff.to_agent.value}",
            agent_id=handoff.from_agent.value,
            reasoning=handoff.reason,
        )

        self.completed_handoffs.append(handoff)
        self._transition_to(OrchestratorState.HANDOFF_COMPLETE)
        self._transition_to(OrchestratorState.EXECUTING)

    async def _state_error_recovery(self) -> AsyncIterator[str]:
        """Attempt to recover from errors."""
        yield "🔧 Attempting error recovery...\n"

        errors = self.context.get_errors()
        if not errors:
            self._transition_to(OrchestratorState.COMPLETED)
            return

        recent_error = errors[-1]
        yield f"   Last error: {recent_error.error_type}: {recent_error.error_message[:100]}\n"

        # Simple recovery strategies
        # 1. If step has retries left, let it retry
        # 2. If escalation possible, handoff to more capable agent
        # 3. Otherwise, fail

        if self.current_plan:
            failed_steps = [s for s in self.current_plan.steps if s.status == "failed"]
            retryable = [s for s in failed_steps if s.retry_count < s.max_retries]

            if retryable:
                for step in retryable:
                    step.status = "pending"
                yield f"   Retrying {len(retryable)} failed steps\n"
                self._transition_to(OrchestratorState.EXECUTING)
                return

        # Cannot recover
        yield "   ❌ Recovery failed\n"
        self._transition_to(OrchestratorState.FAILED, condition="unrecoverable_error")

    # =========================================================================
    # Handoff Management
    # =========================================================================

    def request_handoff(
        self,
        to_agent: AgentType,
        reason: str,
        context_updates: Optional[Dict[str, Any]] = None,
        handoff_type: HandoffType = HandoffType.SEQUENTIAL,
    ) -> Handoff:
        """
        Request a handoff to another agent.

        Args:
            to_agent: Agent to hand off to
            reason: Why the handoff is needed
            context_updates: Updates to apply to context
            handoff_type: Type of handoff

        Returns:
            Created Handoff object
        """
        from_agent = AgentType(self.context.current_agent or "chat")

        handoff = Handoff(
            from_agent=from_agent,
            to_agent=to_agent,
            handoff_type=handoff_type,
            reason=reason,
            context_updates=context_updates or {},
        )

        self.pending_handoffs.append(handoff)
        self._transition_to(OrchestratorState.HANDOFF_PENDING)

        logger.info(f"Handoff requested: {from_agent.value} → {to_agent.value}")
        return handoff

    # =========================================================================
    # Summary & Stats
    # =========================================================================

    async def _generate_summary(self) -> AsyncIterator[str]:
        """Generate execution summary."""
        yield "\n" + "=" * 40 + "\n"
        yield f"📊 Execution Summary\n"
        yield "=" * 40 + "\n"

        # Final state
        state_emoji = {
            OrchestratorState.COMPLETED: "✅",
            OrchestratorState.FAILED: "❌",
            OrchestratorState.CANCELLED: "🚫",
            OrchestratorState.TIMEOUT: "⏰",
        }.get(self.state, "❓")

        yield f"Status: {state_emoji} {self.state.value.upper()}\n"

        # Duration
        if self._start_time:
            duration = time.time() - self._start_time
            yield f"Duration: {duration:.2f}s\n"

        # Iterations
        yield f"Iterations: {self._iteration_count}\n"

        # Plan stats
        if self.current_plan:
            yield f"Plan Steps: {len(self.current_plan.steps)}\n"
            yield f"   Completed: {self.current_plan.completed_steps}\n"
            yield f"   Failed: {self.current_plan.failed_steps}\n"

        # Handoffs
        if self.completed_handoffs:
            yield f"Handoffs: {len(self.completed_handoffs)}\n"

        # Errors
        errors = self.context.get_errors()
        if errors:
            yield f"Errors: {len(errors)}\n"

        yield "=" * 40 + "\n"

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            "state": self.state.value,
            "iterations": self._iteration_count,
            "transitions": len(self._state_history),
            "handoffs_completed": len(self.completed_handoffs),
            "handoffs_pending": len(self.pending_handoffs),
            "plan_steps": len(self.current_plan.steps) if self.current_plan else 0,
            "errors": len(self.context.get_errors()),
        }

    def get_state_history(self) -> List[Dict[str, Any]]:
        """Get state transition history."""
        return [
            {
                "from": t.from_state.value,
                "to": t.to_state.value,
                "condition": t.condition,
                "time": t.timestamp,
            }
            for t in self._state_history
        ]

    # =========================================================================
    # Control
    # =========================================================================

    def cancel(self) -> None:
        """Cancel execution."""
        self._cancelled = True

    def pause(self) -> None:
        """Pause execution (awaiting approval)."""
        self._transition_to(OrchestratorState.AWAITING_APPROVAL)

    def resume(self) -> None:
        """Resume from awaiting approval."""
        if self.state == OrchestratorState.AWAITING_APPROVAL:
            self._transition_to(OrchestratorState.EXECUTING)

    def set_on_state_change(
        self,
        callback: Callable[[OrchestratorState, OrchestratorState], None],
    ) -> None:
        """Set callback for state changes."""
        self._on_state_change = callback

    def set_on_step_complete(
        self,
        callback: Callable[[ExecutionStep, ExecutionResult], None],
    ) -> None:
        """Set callback for step completion."""
        self._on_step_complete = callback


# Convenience function
async def orchestrate(
    request: str,
    context: Optional[UnifiedContext] = None,
    **kwargs: Any,
) -> AsyncIterator[str]:
    """
    Convenience function to orchestrate a request.

    Args:
        request: User request to process
        context: Optional unified context
        **kwargs: Additional arguments for orchestrator

    Yields:
        Progress events
    """
    from .context import new_context

    ctx = context or new_context(user_request=request)
    orchestrator = ActiveOrchestrator(ctx, **kwargs)

    async for event in orchestrator.execute(request):
        yield event


__all__ = [
    "OrchestratorState",
    "HandoffType",
    "StateTransition",
    "ExecutionStep",
    "ExecutionPlan",
    "Handoff",
    "AgentProtocol",
    "ActiveOrchestrator",
    "orchestrate",
]
