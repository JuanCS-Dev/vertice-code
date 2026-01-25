"""
Parallel Execution Tracker - Track and visualize parallel workflow execution.

Extracted from workflow_visualizer.py for modularity.
Single responsibility: Track concurrent step execution and generate timeline views.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Tuple

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .types import StepStatus, WorkflowStep


class ParallelExecutionTracker:
    """
    Track and visualize parallel workflow execution.

    Shows:
    - Concurrent steps
    - Resource utilization
    - Bottlenecks
    - Timeline visualization
    """

    def __init__(self, max_parallel: int = 4):
        """
        Initialize parallel execution tracker.

        Args:
            max_parallel: Maximum number of concurrent steps allowed
        """
        self.max_parallel = max_parallel
        self.active_steps: List[Tuple[str, datetime]] = []
        self.timeline: List[Tuple[datetime, str, str]] = []
        self.steps: Dict[str, WorkflowStep] = {}

    def register_steps(self, steps: Dict[str, WorkflowStep]) -> None:
        """Register workflow steps for status tracking."""
        self.steps = steps

    def start_step(self, step_id: str) -> None:
        """Mark step as started."""
        now = datetime.now()
        self.active_steps.append((step_id, now))
        self.timeline.append((now, step_id, "start"))

    def end_step(self, step_id: str) -> None:
        """Mark step as ended."""
        now = datetime.now()
        self.active_steps = [(sid, start) for sid, start in self.active_steps if sid != step_id]
        self.timeline.append((now, step_id, "end"))

    def get_parallelism_metrics(self) -> Dict[str, float]:
        """Calculate parallelism metrics."""
        if not self.timeline:
            return {
                "avg_concurrent": 0.0,
                "max_concurrent": 0,
                "parallelism_ratio": 0.0,
            }

        # Calculate concurrent steps over time
        concurrent_counts = []
        active = set()

        for _timestamp, step_id, event in sorted(self.timeline):
            if event == "start":
                active.add(step_id)
            elif event == "end":
                active.discard(step_id)
            concurrent_counts.append(len(active))

        max_concurrent = max(concurrent_counts) if concurrent_counts else 0

        return {
            "avg_concurrent": (
                sum(concurrent_counts) / len(concurrent_counts) if concurrent_counts else 0
            ),
            "max_concurrent": max_concurrent,
            "parallelism_ratio": max_concurrent / self.max_parallel,
        }

    def render_timeline(self, style: str = "table") -> Panel:
        """
        Render execution timeline.

        Args:
            style: "table" (event list) or "gantt" (visual timeline)

        Returns:
            Rich Panel with timeline visualization
        """
        if style == "gantt":
            return self._render_gantt_timeline()
        return self._render_table_timeline()

    def _render_table_timeline(self) -> Panel:
        """Render timeline as event table."""
        table = Table(show_header=True, box=None)
        table.add_column("Time", style="cyan", width=12)
        table.add_column("Event", width=10)
        table.add_column("Step", width=30)
        table.add_column("Concurrent", justify="right", width=10)

        active = set()
        for timestamp, step_id, event in self.timeline[-20:]:
            if event == "start":
                active.add(step_id)
                indicator = "[>]"
            else:
                active.discard(step_id)
                indicator = "[.]"

            time_str = timestamp.strftime("%H:%M:%S.%f")[:-3]
            table.add_row(time_str, f"{indicator} {event}", step_id, str(len(active)))

        return Panel(table, title="[bold cyan]Execution Timeline[/bold cyan]", border_style="cyan")

    def _render_gantt_timeline(self) -> Panel:
        """
        Render Gantt-style timeline.

        Visual timeline showing step durations:
        step1 ########------- 0.5s [OK]
        step2   --########--- 0.3s [OK]
        step3   ----########- 0.4s [X]
        """
        # Calculate timeline bounds
        if not self.timeline:
            return Panel(
                Text("No timeline data yet", style="dim"),
                title="[bold cyan]Visual Timeline[/bold cyan]",
                border_style="cyan",
            )

        start_time = min(t for t, _, _ in self.timeline)
        end_time = max(t for t, _, _ in self.timeline)
        total_duration = (end_time - start_time).total_seconds()

        if total_duration == 0:
            total_duration = 1  # Avoid division by zero

        # Build step intervals
        step_intervals: Dict[str, Dict] = {}
        for timestamp, step_id, event in self.timeline:
            if step_id not in step_intervals:
                step_intervals[step_id] = {"start": None, "end": None}

            if event == "start":
                step_intervals[step_id]["start"] = timestamp
            elif event == "end":
                step_intervals[step_id]["end"] = timestamp

        # Render Gantt bars
        gantt_text = Text()
        bar_width = 40

        for step_id, interval in step_intervals.items():
            if interval["start"] is None:
                continue

            # Calculate bar position and width
            start_offset = (interval["start"] - start_time).total_seconds()
            start_pos = int((start_offset / total_duration) * bar_width)

            if interval["end"]:
                duration = (interval["end"] - interval["start"]).total_seconds()
                bar_len = max(1, int((duration / total_duration) * bar_width))
            else:
                bar_len = bar_width - start_pos
                duration = 0

            # Build bar
            bar = "-" * start_pos

            # Get step status
            step = self.steps.get(step_id)
            if step:
                if step.status == StepStatus.COMPLETED:
                    bar += "#" * bar_len
                    status_indicator = "[OK]"
                    bar_color = "green"
                elif step.status == StepStatus.FAILED:
                    bar += "X" * bar_len
                    status_indicator = "[X]"
                    bar_color = "red"
                elif step.status == StepStatus.RUNNING:
                    bar += ">" * bar_len
                    status_indicator = ">>>"
                    bar_color = "yellow"
                else:
                    bar += "." * bar_len
                    status_indicator = "..."
                    bar_color = "dim"

                bar += "-" * (bar_width - len(bar))

                # Duration
                dur_str = f"{duration:.2f}s" if interval["end"] else "..."

                # Build line
                gantt_text.append(f"{step_id:15s} ", style="bold")
                gantt_text.append(bar[:bar_width], style=bar_color)
                gantt_text.append(f" {dur_str:6s} {status_indicator}\n", style=bar_color)

        return Panel(
            gantt_text,
            title="[bold cyan]Visual Timeline (Gantt)[/bold cyan]",
            border_style="cyan",
        )


__all__ = ["ParallelExecutionTracker"]
