"""
Maestro Root Commands - Top-level CLI commands.

Commands for version, info, and main callback.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.panel import Panel

from ..formatters import console
from ..state import state


def version() -> None:
    """Show version information."""
    console.print(
        Panel.fit(
            "[bold cyan]Maestro Shell v7.0[/bold cyan]\n"
            "[dim]The Ultimate AI-Powered CLI (2025)[/dim]\n\n"
            "Built with:\n"
            "  - Typer (CLI framework)\n"
            "  - Rich (Terminal UI)\n"
            "  - async-typer (Async support)",
            border_style="cyan",
        )
    )


def info() -> None:
    """System information."""
    console.print(
        Panel(
            f"""[bold]System Information[/bold]

Python: {sys.version.split()[0]}
Working Directory: {Path.cwd()}
Log File: maestro.log
Agents: {len(state.agents)} initialized
Context Size: {len(state.context)} items""",
            border_style="blue",
        )
    )


def main(
    ctx: typer.Context,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose mode")] = False,
) -> None:
    """
    Maestro - AI-Powered Development CLI v7.0

    The supersonic, reliable, minimal shell for AI-assisted development.
    """
    if ctx.invoked_subcommand is None:
        # Show welcome if no command
        console.print(
            Panel.fit(
                "[bold cyan]Maestro Shell v7.0[/bold cyan]\n\n"
                "Quick Start:\n"
                '  [cyan]maestro agent plan[/cyan] "your goal"\n'
                "  [cyan]maestro agent review[/cyan] src/\n"
                "  [cyan]maestro agent explore[/cyan] map\n\n"
                "Type [cyan]maestro --help[/cyan] for all commands",
                border_style="cyan",
            )
        )

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        console.print("[dim]Verbose mode enabled[/dim]")
