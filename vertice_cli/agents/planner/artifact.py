"""
Planner Artifact - Plan.md Generation (v6.0).

This module handles the generation of plan.md artifacts for user tracking.
Inspired by Claude Code's plan mode that generates structured markdown files.

Philosophy:
    "A plan you can see is a plan you can follow."
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING

from .formatting import format_plan_as_markdown

if TYPE_CHECKING:
    from ..base import AgentTask
    from .agent import PlannerAgent


async def generate_plan_artifact(
    agent: "PlannerAgent", plan_data: Dict[str, Any], task: "AgentTask"
) -> Optional[str]:
    """
    Generate a plan.md file for user tracking.

    Inspired by Claude Code's plan mode that generates a structured
    markdown file with checkboxes for each step.

    Args:
        agent: The PlannerAgent instance
        plan_data: The plan data to format
        task: The original task

    Returns:
        Path to the generated artifact, or None on failure
    """
    try:
        # Ensure directory exists
        artifact_dir = Path(agent.plan_artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plan_id = plan_data.get("plan_id", "unknown")[:8]
        filename = f"plan_{timestamp}_{plan_id}.md"
        filepath = artifact_dir / filename

        # Generate markdown content
        content = format_plan_as_markdown(plan_data, task.request)

        # Write file
        filepath.write_text(content, encoding="utf-8")

        agent.logger.info(f"Generated plan artifact: {filepath}")
        return str(filepath)

    except Exception as e:
        agent.logger.warning(f"Failed to generate plan artifact: {e}")
        return None


__all__ = ["generate_plan_artifact"]
