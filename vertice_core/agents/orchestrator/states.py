"""
State Implementations for the Orchestrator.

Each method implements the behavior for one state in the state machine.
"""

from __future__ import annotations

import asyncio
import time
import traceback
from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, List

from vertice_core.agents.context import DecisionType, ExecutionResult
from vertice_core.agents.router import AgentType, TaskComplexity

from .types import OrchestratorState
from .models import ExecutionPlan, ExecutionStep

if TYPE_CHECKING:
    from .orchestrator import ActiveOrchestrator


async def state_initializing(orch: "ActiveOrchestrator") -> AsyncIterator[str]:
    """Initialize context and prepare for execution."""
    yield "📋 Initializing context...\n"

    orch.context.add_thought(
        agent_id="orchestrator",
        reasoning=f"Processing request: {orch.context.user_request}",
        insights=["Starting orchestration pipeline"],
        next_action="gather_context",
    )

    orch._transition_to(OrchestratorState.GATHERING)


async def state_gathering(orch: "ActiveOrchestrator") -> AsyncIterator[str]:
    """Gather relevant context for the request."""
    yield "🔍 Gathering context...\n"

    orch.context.record_decision(
        decision_type=DecisionType.EXECUTION,
        description="Context gathered for request",
        agent_id="orchestrator",
        reasoning="Initial context collection",
    )

    orch._transition_to(OrchestratorState.ROUTING)


async def state_routing(orch: "ActiveOrchestrator") -> AsyncIterator[str]:
    """Route request to appropriate agent."""
    yield "🔀 Routing request...\n"

    decision = await orch.router.route(
        orch.context.user_request,
        context=orch.context.variables,
    )

    orch.context.record_decision(
        decision_type=DecisionType.ROUTING,
        description=f"Routed to {decision.primary_agent.value}",
        agent_id="orchestrator",
        reasoning=decision.reasoning,
        confidence=decision.confidence,
    )

    yield f"   Agent: {decision.primary_agent.value}\n"
    yield f"   Confidence: {decision.confidence:.2f}\n"
    yield f"   Complexity: {decision.complexity.value}\n"

    orch.context.set("routing_decision", decision.to_dict())
    orch.context.current_agent = decision.primary_agent.value

    if decision.requires_planning:
        orch._transition_to(OrchestratorState.PLANNING, routing=decision.to_dict())
    else:
        orch._transition_to(OrchestratorState.EXECUTING, routing=decision.to_dict())


async def state_planning(orch: "ActiveOrchestrator") -> AsyncIterator[str]:
    """Create execution plan."""
    yield "📝 Creating execution plan...\n"

    routing = orch.context.get("routing_decision", {})

    plan = ExecutionPlan(
        goal=orch.context.user_request,
        created_by="orchestrator",
        complexity=TaskComplexity(routing.get("complexity", "moderate")),
    )

    step = ExecutionStep(
        description=f"Execute: {orch.context.user_request[:100]}",
        agent_type=AgentType(routing.get("agent", "executor")),
        action="execute_task",
        parameters={"request": orch.context.user_request},
    )
    plan.steps.append(step)

    orch.current_plan = plan
    orch.context.current_plan_id = plan.plan_id

    yield f"   Plan ID: {plan.plan_id}\n"
    yield f"   Steps: {len(plan.steps)}\n"

    orch.context.add_thought(
        agent_id="orchestrator",
        reasoning=f"Created plan with {len(plan.steps)} steps",
        insights=[f"Step: {s.description}" for s in plan.steps[:3]],
        next_action="execute_plan",
    )

    orch._transition_to(OrchestratorState.EXECUTING)


async def state_executing(orch: "ActiveOrchestrator") -> AsyncIterator[str]:
    """Execute current plan steps."""
    yield "⚡ Executing...\n"

    if not orch.current_plan:
        orch.current_plan = ExecutionPlan(goal=orch.context.user_request)
        step = ExecutionStep(
            description="Direct execution",
            agent_type=AgentType(orch.context.current_agent or "executor"),
        )
        orch.current_plan.steps.append(step)

    runnable = orch.current_plan.get_runnable_steps()

    if not runnable:
        if orch.current_plan.is_complete():
            orch._transition_to(OrchestratorState.VERIFYING)
        elif orch.current_plan.has_failed():
            orch._transition_to(OrchestratorState.ERROR_RECOVERY)
        else:
            orch._transition_to(OrchestratorState.FAILED, condition="deadlock")
        return

    for step in runnable:
        step.status = "running"
        step.started_at = time.time()

        yield f"   → {step.description}\n"

        try:
            agent = orch.agents.get(step.agent_type)

            if agent:
                async for event in agent.execute(
                    step.parameters.get("request", orch.context.user_request),
                    orch.context,
                ):
                    yield f"     {event}"

            step.status = "completed"
            step.completed_at = time.time()

            result = ExecutionResult(
                step_id=step.step_id,
                success=True,
                duration_ms=(step.completed_at - step.started_at) * 1000,
            )
            step.result = result
            orch.current_plan.completed_steps += 1

            orch.context.add_step_result(result)

            yield f"   ✓ Completed: {step.description}\n"

            if orch._on_step_complete:
                orch._on_step_complete(step, result)

        except Exception as e:
            step.status = "failed"
            step.retry_count += 1

            orch.context.record_error(
                error_type=type(e).__name__,
                error_message=str(e),
                agent_id=step.agent_type.value,
                step_id=step.step_id,
            )

            yield f"   ✗ Failed: {step.description} - {e}\n"

            if step.retry_count < step.max_retries:
                step.status = "pending"
                yield f"   🔄 Retrying ({step.retry_count}/{step.max_retries})\n"
                await asyncio.sleep(orch.RETRY_BACKOFF_BASE ** step.retry_count)
            else:
                orch.current_plan.failed_steps += 1

    if orch.current_plan.get_pending_steps():
        pass  # Stay in EXECUTING
    elif orch.current_plan.is_complete():
        orch._transition_to(OrchestratorState.VERIFYING)
    else:
        orch._transition_to(OrchestratorState.ERROR_RECOVERY)


async def state_verifying(orch: "ActiveOrchestrator") -> AsyncIterator[str]:
    """Verify execution results."""
    yield "✅ Verifying results...\n"

    routing = orch.context.get("routing_decision", {})

    if routing.get("requires_review", False):
        orch._transition_to(OrchestratorState.REVIEWING)
        return

    if orch.context.has_failures():
        yield "   ⚠️ Some steps had failures\n"
        orch._transition_to(OrchestratorState.ERROR_RECOVERY)
    else:
        yield "   All steps completed successfully\n"
        orch._transition_to(OrchestratorState.COMPLETED)


async def state_reviewing(orch: "ActiveOrchestrator") -> AsyncIterator[str]:
    """Review results (agent or human)."""
    yield "🔎 Reviewing results...\n"

    orch.context.record_decision(
        decision_type=DecisionType.APPROVAL,
        description="Results auto-approved",
        agent_id="orchestrator",
    )

    yield "   Results approved\n"
    orch._transition_to(OrchestratorState.COMPLETED)


async def state_handoff(orch: "ActiveOrchestrator") -> AsyncIterator[str]:
    """Handle agent handoff."""
    if not orch.pending_handoffs:
        orch._transition_to(OrchestratorState.EXECUTING)
        return

    handoff = orch.pending_handoffs.pop(0)
    yield f"🔄 Handoff: {handoff.from_agent.value} → {handoff.to_agent.value}\n"
    yield f"   Reason: {handoff.reason}\n"

    orch.context.update(handoff.context_updates)
    orch.context.current_agent = handoff.to_agent.value

    orch.context.record_decision(
        decision_type=DecisionType.HANDOFF,
        description=f"Handoff to {handoff.to_agent.value}",
        agent_id=handoff.from_agent.value,
        reasoning=handoff.reason,
    )

    orch.completed_handoffs.append(handoff)
    orch._transition_to(OrchestratorState.HANDOFF_COMPLETE)
    orch._transition_to(OrchestratorState.EXECUTING)


async def state_error_recovery(orch: "ActiveOrchestrator") -> AsyncIterator[str]:
    """Attempt to recover from errors."""
    yield "🔧 Attempting error recovery...\n"

    errors = orch.context.get_errors()
    if not errors:
        orch._transition_to(OrchestratorState.COMPLETED)
        return

    recent_error = errors[-1]
    yield f"   Last error: {recent_error.error_type}: {recent_error.error_message[:100]}\n"

    if orch.current_plan:
        failed_steps = [s for s in orch.current_plan.steps if s.status == "failed"]
        retryable = [s for s in failed_steps if s.retry_count < s.max_retries]

        if retryable:
            for step in retryable:
                step.status = "pending"
            yield f"   Retrying {len(retryable)} failed steps\n"
            orch._transition_to(OrchestratorState.EXECUTING)
            return

    yield "   ❌ Recovery failed\n"
    orch._transition_to(OrchestratorState.FAILED, condition="unrecoverable_error")
