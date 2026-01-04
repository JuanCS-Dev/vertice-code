"""
Context Rendering - Render context awareness panels.

Rich-based panels for context visualization.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .types import ContextWindow, FileRelevance


def render_context_panel(
    window: ContextWindow,
    max_tokens: int,
) -> Panel:
    """Render context awareness panel.

    Args:
        window: Current context window.
        max_tokens: Maximum tokens allowed.

    Returns:
        Rich Panel with context information.
    """
    table = Table(title="Context Window", show_header=True)
    table.add_column("File", style="cyan", width=40)
    table.add_column("Relevance", width=10)
    table.add_column("Tokens", justify="right", width=10)
    table.add_column("Status", width=10)

    for path, relevance in window.files.items():
        # Status icons
        status = []
        if path in window.user_pinned:
            status.append("P")
        if path in window.auto_added:
            status.append("A")

        # Relevance indicator
        if relevance.priority == "HIGH":
            rel_icon = "[green]H[/green]"
        elif relevance.priority == "MEDIUM":
            rel_icon = "[yellow]M[/yellow]"
        else:
            rel_icon = "[red]L[/red]"

        table.add_row(
            Path(path).name,
            f"{rel_icon} {relevance.score:.2f}",
            f"{relevance.token_count:,}",
            " ".join(status),
        )

    # Summary
    summary = Text()
    summary.append("\nUtilization: ", style="bold")
    summary.append(
        f"{window.utilization*100:.1f}%",
        style="red" if window.is_critical else "green",
    )
    summary.append(
        f" ({window.total_tokens:,}/{max_tokens:,} tokens)\n",
        style="dim",
    )

    return Panel(table, subtitle=summary, border_style="cyan")


def render_token_usage_realtime(window: ContextWindow) -> Panel:
    """Render real-time token usage panel.

    Shows:
    - Current input/output tokens
    - Streaming token counter
    - Usage trend (last 10 interactions)
    - Cost estimate

    Args:
        window: Current context window.

    Returns:
        Rich Panel with token usage.
    """
    content = Text()

    # Current session stats
    content.append("Current Session\n", style="bold cyan")
    content.append(f"  Input:  {window.current_input_tokens:,} tokens\n", style="green")
    content.append(f"  Output: {window.current_output_tokens:,} tokens\n", style="yellow")

    if window.streaming_tokens > 0:
        content.append(
            f"  Streaming: {window.streaming_tokens:,} tokens\n",
            style="magenta bold",
        )

    total_session = window.current_input_tokens + window.current_output_tokens
    content.append(f"  Total:  {total_session:,} tokens\n\n", style="bold")

    # Usage trend (last 10 snapshots)
    if window.usage_history:
        content.append("Recent Trend\n", style="bold cyan")

        recent = list(window.usage_history)[-10:]
        for snapshot in recent:
            time_str = snapshot.timestamp.strftime("%H:%M:%S")
            content.append(f"  {time_str} | ", style="dim")
            content.append(f"in:{snapshot.input_tokens:,} ", style="green")
            content.append(f"out:{snapshot.output_tokens:,}", style="yellow")

            if snapshot.cost_estimate_usd > 0:
                content.append(f" | ${snapshot.cost_estimate_usd:.4f}", style="magenta")

            content.append("\n")

        # Calculate cumulative cost
        total_cost = sum(s.cost_estimate_usd for s in window.usage_history)
        if total_cost > 0:
            content.append(f"\nCumulative Cost: ${total_cost:.4f}\n", style="bold magenta")

    # Warning if approaching limit
    if window.is_critical:
        content.append("\nCRITICAL: Context >90% full!\n", style="bold red")
        content.append("    Consider optimizing context.\n", style="red")
    elif window.is_warning:
        content.append("\nWARNING: Context >80% full\n", style="bold yellow")

    return Panel(content, title="Token Usage (Real-Time)", border_style="magenta")


__all__ = ["render_context_panel", "render_token_usage_realtime"]
