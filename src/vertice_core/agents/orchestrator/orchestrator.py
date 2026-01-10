"""
ActiveOrchestrator - State Machine for Multi-Agent Orchestration.

Implements the execution loop pattern from Big 3 (Dec 2025):
- LangGraph: Explicit state machine with transitions
- Claude SDK: Gather → Act → Verify → Repeat
- OpenAI Swarm: Handoffs via function returns
"""

from __future__ import annotations

import asyncio
import logging
import time
import traceback
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from vertice_core.agents.context import ExecutionResult, UnifiedContext
from vertice_core.agents.router import AgentType, SemanticRouter

from .types import OrchestratorState, HandoffType
from .models import StateTransition, ExecutionStep, ExecutionPlan, Handoff
from .protocol import AgentProtocol
from . import states

logger = logging.getLogger(__name__)


class ActiveOrchestrator:
    """
    State machine orchestrator for multi-agent execution.

    Implements the pattern: Gather → Route → Act → Verify → Repeat

    State Machine:
        IDLE → GATHERING → ROUTING → PLANNING/EXECUTING → VERIFYING → COMPLETED
    """

    MAX_ITERATIONS = 20
    DEFAULT_TIMEOUT = 300.0
    RETRY_BACKOFF_BASE = 2.0

    def __init__(
        self,
        context: UnifiedContext,
        router: Optional[SemanticRouter] = None,
        agents: Optional[Dict[AgentType, AgentProtocol]] = None,
        timeout: Optional[float] = None,
        max_iterations: Optional[int] = None,
    ):
        if context is None:
            raise AttributeError("Context cannot be None")

        self.context = context
        self.router = router or SemanticRouter()
        self.agents = agents or {}
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_iterations = max_iterations or self.MAX_ITERATIONS

        self.state = OrchestratorState.IDLE
        self._state_history: List[StateTransition] = []

        self.current_plan: Optional[ExecutionPlan] = None
        self.pending_handoffs: List[Handoff] = []
        self.completed_handoffs: List[Handoff] = []

        self._cancelled = False
        self._iteration_count = 0
        self._start_time: Optional[float] = None

        self._on_state_change: Optional[Callable[[OrchestratorState, OrchestratorState], None]] = (
            None
        )
        self._on_step_complete: Optional[Callable[[ExecutionStep, ExecutionResult], None]] = None

    def _transition_to(
        self,
        new_state: OrchestratorState,
        condition: Optional[str] = None,
        **metadata: Any,
    ) -> None:
        """Transition to a new state."""
        old_state = self.state

        transition = StateTransition(
            from_state=old_state,
            to_state=new_state,
            condition=condition,
            metadata=metadata,
        )
        self._state_history.append(transition)

        self.state = new_state
        logger.debug(f"State: {old_state.value} → {new_state.value}")

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
        return elapsed > self.timeout

    def _check_iteration_limit(self) -> bool:
        """Check if iteration limit reached."""
        return self._iteration_count >= self.max_iterations

    async def execute(
        self,
        request: str,
        timeout: Optional[float] = None,
    ) -> AsyncIterator[str]:
        """Execute a user request through the orchestration pipeline."""
        self._start_time = time.time()
        self._cancelled = False
        self._iteration_count = 0

        if timeout:
            self.DEFAULT_TIMEOUT = timeout

        self._transition_to(OrchestratorState.INITIALIZING)
        self.context.user_request = request
        self.context.current_agent = None

        await self.router.initialize()

        yield f"🎯 AI Processing: {request[:100]}...\n"

        try:
            while not self._is_terminal_state():
                self._iteration_count += 1

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

                async for event in self._execute_state():
                    yield event

            async for event in self._generate_summary():
                yield event

        except Exception as e:
            self._transition_to(OrchestratorState.FAILED, error=str(e))
            self.context.record_error(
                e,  # error
                stack_trace=traceback.format_exc(),
            )
            yield f"❌ Error: {e}\n"

    async def _execute_state(self) -> AsyncIterator[str]:
        """Execute actions for current state and transition."""
        state = self.state

        state_handlers = {
            OrchestratorState.INITIALIZING: states.state_initializing,
            OrchestratorState.GATHERING: states.state_gathering,
            OrchestratorState.ROUTING: states.state_routing,
            OrchestratorState.PLANNING: states.state_planning,
            OrchestratorState.EXECUTING: states.state_executing,
            OrchestratorState.VERIFYING: states.state_verifying,
            OrchestratorState.REVIEWING: states.state_reviewing,
            OrchestratorState.HANDOFF_PENDING: states.state_handoff,
            OrchestratorState.ERROR_RECOVERY: states.state_error_recovery,
        }

        handler = state_handlers.get(state)
        if handler:
            async for event in handler(self):
                yield event
        elif state == OrchestratorState.AWAITING_APPROVAL:
            await asyncio.sleep(0.1)
        else:
            self._transition_to(OrchestratorState.FAILED, condition="unknown_state")

    def request_handoff(
        self,
        to_agent: AgentType,
        reason: str = "",
        context_updates: Optional[Dict[str, Any]] = None,
        handoff_type: HandoffType = HandoffType.SEQUENTIAL,
    ) -> Handoff:
        """Request a handoff to another agent."""
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

    async def _generate_summary(self) -> AsyncIterator[str]:
        """Generate execution summary."""
        yield "\n" + "=" * 40 + "\n"
        yield "📊 AI Execution Summary\n"
        yield "=" * 40 + "\n"

        state_emoji = {
            OrchestratorState.COMPLETED: "✅",
            OrchestratorState.FAILED: "❌",
            OrchestratorState.CANCELLED: "🚫",
            OrchestratorState.TIMEOUT: "⏰",
        }.get(self.state, "❓")

        yield f"Status: {state_emoji} {self.state.value.upper()}\n"

        if self._start_time:
            duration = time.time() - self._start_time
            yield f"Duration: {duration:.2f}s\n"

        yield f"Iterations: {self._iteration_count}\n"

        if self.current_plan:
            yield f"Plan Steps: {len(self.current_plan.steps)}\n"
            yield f"   Completed: {self.current_plan.completed_steps}\n"
            yield f"   Failed: {self.current_plan.failed_steps}\n"

        if self.completed_handoffs:
            yield f"Handoffs: {len(self.completed_handoffs)}\n"

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

    def cancel(self) -> None:
        """Cancel execution."""
        self._cancelled = True
        self._transition_to(OrchestratorState.CANCELLED)

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
