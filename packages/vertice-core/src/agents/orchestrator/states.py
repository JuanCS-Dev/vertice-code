"""
State Implementations for the Orchestrator.

Each method implements the behavior for one state in the state machine.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, AsyncIterator

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
        key_insights=["Starting orchestration pipeline"],
        next_action="gather_context",
    )

    orch._transition_to(OrchestratorState.GATHERING)


async def state_gathering(orch: "ActiveOrchestrator") -> AsyncIterator[str]:
    """Gather relevant context for the request."""
    yield "🔍 Gathering context...\n"

    orch.context.record_decision(
        "Context gathered for request",
        DecisionType.EXECUTION,
        1.0,  # confidence
        "Initial context collection",
        agent_id="orchestrator",
    )

    orch._transition_to(OrchestratorState.ROUTING)


async def state_routing(orch: "ActiveOrchestrator") -> AsyncIterator[str]:
    """Route request to appropriate agent."""
    yield "🔀 Routing request...\n"

    decision = await orch.router.route(
        orch.context.user_request,
        context=orch.context.variables(),
    )

    orch.context.record_decision(
        f"Routed to {decision.agent_type.value}",
        DecisionType.ROUTING,
        decision.confidence,
        decision.reasoning,
        agent_id="orchestrator",
    )

    yield f"   Agent: {decision.agent_type.value}\n"
    yield f"   Confidence: {decision.confidence:.2f}\n"
    yield f"   Complexity: {decision.complexity.value}\n"

    # Store routing decision in context
    routing_data = {
        "agent_type": decision.agent_type.value,
        "confidence": decision.confidence,
        "reasoning": decision.reasoning,
        "complexity": decision.complexity.value,
    }
    orch.context.set("routing_decision", routing_data)
    orch.context.current_agent = decision.agent_type.value

    # For now, always go to executing (simplified logic)
    orch._transition_to(OrchestratorState.EXECUTING, routing=routing_data)


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
        reasoning=f"Created plan with {len(plan.steps)} steps",
        agent_id="orchestrator",
        key_insights=[f"Step: {s.description}" for s in plan.steps[:3]],
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
                execution_result = await agent.execute(
                    step.parameters.get("request", orch.context.user_request),
                    orch.context,
                )
                yield f"     {execution_result}"

            step.status = "completed"
            step.completed_at = time.time()

            step_result = ExecutionResult(
                step_id=step.step_id,
                success=True,
                duration_ms=(step.completed_at - step.started_at) * 1000,
            )
            step.result = step_result
            orch.current_plan.completed_steps += 1

            orch.context.add_step_result(step_result)

            yield f"   ✓ Completed: {step.description}\n"

            if orch._on_step_complete:
                orch._on_step_complete(step, step_result)

        except Exception as e:
            step.status = "failed"
            step.retry_count += 1

            orch.context.record_error(
                e,  # error
                agent_id=step.agent_type.value,
                step_id=step.step_id,
            )

            yield f"   ✗ Failed: {step.description} - {e}\n"

            if step.retry_count < step.max_retries:
                step.status = "pending"
                yield f"   🔄 Retrying ({step.retry_count}/{step.max_retries})\n"
                await asyncio.sleep(orch.RETRY_BACKOFF_BASE**step.retry_count)
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
        "Results auto-approved",
        DecisionType.APPROVAL,
        1.0,  # confidence
        "Automatic approval of results",
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
        f"Handoff to {handoff.to_agent.value}",
        DecisionType.HANDOFF,
        1.0,  # confidence
        handoff.reason,
        agent_id=handoff.from_agent.value,
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
