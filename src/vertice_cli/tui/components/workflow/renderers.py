"""
Workflow Renderers - Rich terminal rendering for workflow visualization.

Extracted from workflow_visualizer.py for modularity.
Single responsibility: Render workflow state to Rich components.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional, Set

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from .types import StepStatus, WorkflowStep

if TYPE_CHECKING:
    pass


def get_status_style(status: StepStatus) -> str:
    """Get Rich style for status."""
    return {
        StepStatus.PENDING: "dim",
        StepStatus.RUNNING: "yellow bold",
        StepStatus.COMPLETED: "green",
        StepStatus.FAILED: "red bold",
        StepStatus.SKIPPED: "cyan dim",
        StepStatus.BLOCKED: "red dim",
    }[status]


def render_progress_bar(progress: float, width: int = 10) -> str:
    """Render ASCII progress bar."""
    filled = int(progress * width)
    bar = "#" * filled + "-" * (width - filled)
    percentage = int(progress * 100)
    return f"[{bar}] {percentage}%"


def render_dependency_tree(steps: Dict[str, WorkflowStep], start_time: Optional[datetime]) -> Tree:
    """
    Render workflow as dependency tree.

    Returns ASCII tree showing:
    - Step hierarchy
    - Current status
    - Progress indicators
    """
    root = Tree("[Workflow Execution]")

    # Find root steps (no dependencies)
    root_steps = [sid for sid, step in steps.items() if not step.dependencies]

    # Build tree recursively
    visited: Set[str] = set()

    def add_step_to_tree(step_id: str, parent: Tree) -> None:
        if step_id in visited:
            return
        visited.add(step_id)

        step = steps[step_id]

        # Build step label
        duration_str = ""
        if step.duration:
            duration_str = f" ({step.duration:.1f}s)"

        progress_str = ""
        if step.status == StepStatus.RUNNING and step.progress > 0:
            progress_str = f" [{int(step.progress * 100)}%]"

        label = Text()
        label.append(f"{step.status_emoji} ", style="bold")
        label.append(step.name, style=get_status_style(step.status))
        label.append(duration_str, style="dim")
        label.append(progress_str, style="cyan")

        if step.error:
            label.append(f" WARNING: {step.error}", style="red")

        node = parent.add(label)

        # Add dependent steps
        dependents = [sid for sid, s in steps.items() if step_id in s.dependencies]
        for dep_id in dependents:
            add_step_to_tree(dep_id, node)

    for root_id in root_steps:
        add_step_to_tree(root_id, root)

    return root


def render_progress_table(steps: Dict[str, WorkflowStep], execution_order: List[str]) -> Table:
    """Render progress summary table."""
    table = Table(title="Execution Progress", show_header=True)
    table.add_column("Step", style="cyan", width=30)
    table.add_column("Status", width=12)
    table.add_column("Progress", width=15)
    table.add_column("Duration", justify="right", width=10)

    for step_id in execution_order:
        if step_id not in steps:
            continue
        step = steps[step_id]

        # Progress bar
        progress_bar = render_progress_bar(step.progress, width=10)

        # Duration
        duration = f"{step.duration:.1f}s" if step.duration else "-"

        table.add_row(step.name, f"{step.status_emoji} {step.status.value}", progress_bar, duration)

    return table


def render_metrics(steps: Dict[str, WorkflowStep], start_time: Optional[datetime]) -> Panel:
    """Render overall workflow metrics."""
    total_steps = len(steps)
    completed = sum(1 for s in steps.values() if s.status == StepStatus.COMPLETED)
    failed = sum(1 for s in steps.values() if s.status == StepStatus.FAILED)
    running = sum(1 for s in steps.values() if s.status == StepStatus.RUNNING)

    total_duration = 0.0
    if start_time:
        total_duration = (datetime.now() - start_time).total_seconds()

    metrics_text = Text()
    metrics_text.append("Workflow Metrics\n\n", style="bold cyan")
    metrics_text.append(f"Total Steps: {total_steps}\n")
    metrics_text.append(f"[OK] Completed: {completed}\n", style="green")
    metrics_text.append(f"[X] Failed: {failed}\n", style="red")
    metrics_text.append(f">>> Running: {running}\n", style="yellow")
    metrics_text.append(f"Time: {total_duration:.1f}s\n", style="cyan")

    # Calculate avg step duration
    completed_steps = [s for s in steps.values() if s.duration]
    if completed_steps:
        avg_duration = sum(s.duration for s in completed_steps) / len(completed_steps)
        metrics_text.append(f"Avg Step: {avg_duration:.1f}s\n", style="magenta")

    return Panel(metrics_text, border_style="cyan")


def render_minimap(steps: Dict[str, WorkflowStep]) -> Panel:
    """
    Render mini-map overview (Windsurf inspiration).
    Compact view of all steps with status indicators.
    """
    minimap_text = Text()
    minimap_text.append("Workflow Map: ", style="bold cyan")

    for step in steps.values():
        minimap_text.append(f"{step.status_emoji}", style="")

    # Progress bar
    total = len(steps)
    completed = sum(1 for s in steps.values() if s.status == StepStatus.COMPLETED)
    progress_pct = (completed / total * 100) if total > 0 else 0
    minimap_text.append(f"  [{completed}/{total}] {progress_pct:.0f}%", style="dim")

    return Panel(minimap_text, border_style="dim", height=3)


def render_streaming_view(step: Optional[WorkflowStep]) -> Panel:
    """
    Render streaming tokens (Cursor/Claude style).
    Shows live token generation for current step.
    """
    if step is None:
        return Panel("No active streaming", border_style="dim")

    if not step.streaming_tokens:
        return Panel("Waiting for tokens...", border_style="dim")

    # Last 50 tokens
    recent_tokens = list(step.streaming_tokens)[-50:]
    stream_text = Text()

    for _timestamp, token in recent_tokens:
        stream_text.append(token, style="cyan")

    return Panel(stream_text, title=f"Streaming: {step.name}", border_style="yellow")


def render_diff_view(step: Optional[WorkflowStep]) -> Panel:
    """
    Render changes diff-style (GitHub Copilot inspiration).
    Shows before/after for file changes.
    """
    if step is None:
        return Panel("No changes", border_style="dim")

    if not step.changes:
        return Panel("No changes tracked", border_style="dim")

    diff_text = Text()

    for change in step.changes[-5:]:  # Last 5 changes
        diff_text.append(f"\n[{change['type']}]\n", style="bold")
        diff_text.append(f"- {change['before']}\n", style="red")
        diff_text.append(f"+ {change['after']}\n", style="green")

    return Panel(diff_text, title=f"Changes: {step.name}", border_style="blue")


def render_ai_suggestions(step: Optional[WorkflowStep]) -> Optional[Panel]:
    """
    Render AI suggestions (Claude style).
    Shows intelligent recommendations for errors.
    """
    if step is None or not step.ai_suggestion:
        return None

    suggestion_text = Text()
    suggestion_text.append("AI Suggestion:\n\n", style="bold magenta")
    suggestion_text.append(step.ai_suggestion, style="cyan")

    return Panel(suggestion_text, title="Intelligent Recommendation", border_style="magenta")


def render_checkpoint_view(checkpoints: Dict[str, Dict]) -> Panel:
    """
    Render checkpoints (Cursor Composer style).
    Shows save points for undo/rollback.
    """
    if not checkpoints:
        return Panel("No checkpoints", border_style="dim")

    checkpoint_text = Text()
    checkpoint_text.append("Checkpoints:\n\n", style="bold green")

    for cp_id, cp_data in list(checkpoints.items())[-5:]:
        timestamp = cp_data.get("timestamp", "Unknown")
        description = cp_data.get("description", "Checkpoint")
        checkpoint_text.append(f"  {cp_id[:8]}: {description} ({timestamp})\n", style="dim")

    return Panel(checkpoint_text, border_style="green")


def create_main_view(
    steps: Dict[str, WorkflowStep],
    execution_order: List[str],
    start_time: Optional[datetime],
) -> Group:
    """Create main workflow view with metrics, tree, and table."""
    return Group(
        render_metrics(steps, start_time),
        render_dependency_tree(steps, start_time),
        render_progress_table(steps, execution_order),
    )


def create_details_view(steps: Dict[str, WorkflowStep], checkpoints: Dict[str, Dict]) -> Group:
    """Create details view with streaming, diff, and AI suggestions."""
    running_steps = [step for step in steps.values() if step.status == StepStatus.RUNNING]

    if running_steps:
        active_step = running_steps[0]
        details = [render_streaming_view(active_step), render_diff_view(active_step)]

        # Add AI suggestion if error
        if active_step.error and active_step.ai_suggestion:
            ai_panel = render_ai_suggestions(active_step)
            if ai_panel:
                details.append(ai_panel)

        return Group(*details)

    return Group(render_checkpoint_view(checkpoints))


__all__ = [
    "get_status_style",
    "render_progress_bar",
    "render_dependency_tree",
    "render_progress_table",
    "render_metrics",
    "render_minimap",
    "render_streaming_view",
    "render_diff_view",
    "render_ai_suggestions",
    "render_checkpoint_view",
    "create_main_view",
    "create_details_view",
]
