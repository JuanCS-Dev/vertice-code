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

Usage:
    from vertice_core.agents.orchestrator import ActiveOrchestrator, orchestrate

    orchestrator = ActiveOrchestrator(context)
    async for event in orchestrator.execute("implement login"):
        print(event)
"""

from typing import Any, AsyncIterator, Optional

from vertice_core.agents.context import UnifiedContext

from .types import OrchestratorState, HandoffType
from .models import StateTransition, ExecutionStep, ExecutionPlan, Handoff
from .protocol import AgentProtocol
from .orchestrator import ActiveOrchestrator


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
    from vertice_core.agents.context import new_context

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
