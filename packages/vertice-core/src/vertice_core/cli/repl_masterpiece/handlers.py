"""
REPL Masterpiece Handlers - Command Handler Functions.

This module provides handler functions for shell commands.

Features:
- System command handlers (help, exit, clear, status)
- Output mode management
- DREAM mode toggle

Philosophy:
    "Handlers should be focused and predictable."
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from rich.panel import Panel

if TYPE_CHECKING:
    from .repl import MasterpieceREPL


def cmd_help(repl: "MasterpieceREPL", _: str) -> None:
    """Show MINIMAL help (Nov 2025 style)."""
    repl.console.print("\n[bold cyan]Commands[/bold cyan]")

    # Group by category
    categories = {"system": [], "agent": []}

    for cmd, meta in repl.commands.items():
        cat = meta["category"].value
        if cat in categories:
            categories[cat].append((cmd, meta))

    # Render compact
    for cat_name, cat_key in [("System", "system"), ("Agents", "agent")]:
        if cat_key in categories and categories[cat_key]:
            repl.console.print(f"\n[dim]{cat_name}:[/dim]")
            items = sorted(categories[cat_key])

            for cmd, meta in items:
                repl.console.print(
                    f"  {meta['icon']} [cyan]{cmd:14}[/cyan] " f"[dim]{meta['description']}[/dim]"
                )

    repl.console.print(
        "\n[dim]💡 Ctrl+P palette • Ctrl+O expand • Tab autocomplete • " "Natural chat[/dim]\n"
    )


def cmd_exit(repl: "MasterpieceREPL", _: str) -> None:
    """Exit with style."""
    duration = int(time.time() - repl.session_start)
    minutes = duration // 60
    seconds = duration % 60

    repl.console.print("\n[bold cyan]Session Summary:[/bold cyan]")
    repl.console.print(f"  • Commands executed: [green]{repl.command_count}[/green]")
    repl.console.print(f"  • Duration: [green]{minutes}m {seconds}s[/green]")
    repl.console.print("\n[bold yellow]👋 Goodbye! Keep coding! ✨[/bold yellow]")
    repl.console.print("[dim]Soli Deo Gloria 🙏[/dim]\n")

    # Cleanup
    repl.cleanup()
    repl.running = False


def cmd_clear(repl: "MasterpieceREPL", _: str) -> None:
    """Clear with feedback."""
    repl.console.clear()
    repl.console.print("[dim]✨ Screen cleared[/dim]\n")


def cmd_status(repl: "MasterpieceREPL", _: str) -> None:
    """Show session status."""
    duration = int(time.time() - repl.session_start)

    panel = Panel.fit(
        f"""[bold]Session Status[/bold]

⏱️  Duration: [cyan]{duration}s[/cyan]
🎯 Commands: [green]{repl.command_count}[/green]
💭 DREAM mode: [yellow]{'ON' if repl.dream_mode else 'OFF'}[/yellow]
🤖 Current agent: [magenta]{repl.current_agent or 'None'}[/magenta]
📁 Context: [blue]{len(repl.context.file_history)} files[/blue]

[dim]Shortcuts: Ctrl+P (palette) • Ctrl+O (expand) • Ctrl+D (dream) • Ctrl+L (clear)[/dim]
        """,
        border_style="cyan",
        title="📊 Status",
    )
    repl.console.print("\n")
    repl.console.print(panel)
    repl.console.print()


def cmd_expand(repl: "MasterpieceREPL", _: str) -> None:
    """Show full last response."""
    if not repl.last_response:
        repl.console.print("[yellow]No previous response to expand[/yellow]\n")
        return

    repl.console.print("\n[bold cyan]📖 Full Response[/bold cyan]")
    repl.console.print("─" * 60)
    repl.console.print(repl.last_response, style="white")
    repl.console.print("─" * 60)
    repl.console.print(
        f"[dim]{len(repl.last_response.split())} words • "
        f"{len(repl.last_response)} chars[/dim]\n"
    )


def cmd_mode(repl: "MasterpieceREPL", args: str) -> None:
    """Change output mode."""
    modes = ["auto", "full", "minimal", "summary"]

    if not args or args not in modes:
        repl.console.print(f"[yellow]Current mode: {repl.output_mode}[/yellow]")
        repl.console.print(f"[dim]Available: {', '.join(modes)}[/dim]")
        repl.console.print("[dim]Usage: /mode <mode>[/dim]\n")
        return

    repl.output_mode = args
    repl.console.print(f"[green]✓ Output mode: {args}[/green]\n")


def cmd_dream(repl: "MasterpieceREPL", message: str) -> None:
    """Toggle DREAM mode."""
    if not message.strip():
        repl.dream_mode = not repl.dream_mode
        status = "🟢 ENABLED" if repl.dream_mode else "⚫ DISABLED"
        repl.console.print(f"\n💭 [bold]DREAM mode {status}[/bold]\n")
    else:
        asyncio.run(repl.invoke_agent("reviewer", f"[CRITICAL ANALYSIS] {message}"))


__all__ = [
    "cmd_help",
    "cmd_exit",
    "cmd_clear",
    "cmd_status",
    "cmd_expand",
    "cmd_mode",
    "cmd_dream",
]
