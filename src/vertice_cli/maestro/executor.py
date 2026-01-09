"""
Maestro Executor - Agent task execution engine.

Handles execution of agent tasks with governance integration.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from rich.progress import Progress, SpinnerColumn, TextColumn

from .formatters import console, render_error, render_success
from .state import state

logger = logging.getLogger(__name__)


async def execute_agent_task(
    agent_name: str,
    prompt: str,
    context: Optional[Dict[str, Any]] = None,
    stream: bool = True,
    with_governance: bool = True,
) -> Dict[str, Any]:
    """
    Delegates execution to the specific v6.0 Agent.

    Args:
        agent_name: Name of agent (planner, reviewer, explorer)
        prompt: User prompt/request
        context: Additional context
        stream: Enable streaming output
        with_governance: Enable governance checks

    Returns:
        Agent response data (ExecutionPlan, ReviewReport, etc.)
    """
    from vertice_cli.agents.base import AgentTask

    start_time = datetime.now()
    agent_name = agent_name.lower()

    # Validate agent exists
    if agent_name not in state.agents:
        raise ValueError(
            f"Agent '{agent_name}' not found in swarm. Available: {list(state.agents.keys())}"
        )

    target_agent = state.agents[agent_name]

    console.print(
        f"\n[bold blue]{target_agent.role.value.upper()}[/bold blue] [dim]activated[/dim]"
    )

    try:
        # Create the standardized Task object
        task = AgentTask(
            request=prompt,
            context=context or {},
            metadata={"interface": "maestro_v7", "timestamp": datetime.now().isoformat()},
        )

        # Execute with governance if available
        if with_governance and state.governance:
            with Progress(
                SpinnerColumn("dots12"),
                TextColumn("[bold blue]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task("Reasoning with governance...", total=None)

                response = await state.governance.execute_with_governance(
                    agent=target_agent, task=task
                )
        else:
            # Execute without governance
            with Progress(
                SpinnerColumn("dots12"),
                TextColumn("[bold blue]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task("Reasoning...", total=None)

                response = await target_agent.execute(task)

        duration = (datetime.now() - start_time).total_seconds()

        # Check success
        if not response.success:
            render_error(
                f"{agent_name.title()} reported failure", response.error or "Unknown error"
            )
            return {"status": "failed", "error": response.error, "reasoning": response.reasoning}

        render_success("Task Complete", duration)

        # Log reasoning for debugging
        logger.info(f"{agent_name} reasoning: {response.reasoning}")

        return response.data

    except Exception as e:
        render_error(f"Crash in {agent_name}", str(e))
        logger.exception(f"Agent {agent_name} crash details")
        raise
