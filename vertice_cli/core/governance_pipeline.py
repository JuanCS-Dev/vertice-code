"""
Governance pipeline for agent task execution.
"""

from vertice_core.types import AgentTask, AgentResponse


def process_task(task: AgentTask) -> AgentResponse:
    """Process a task through the governance pipeline."""
    return AgentResponse(success=True, reasoning="Task processed", data={"result": "ok"})
