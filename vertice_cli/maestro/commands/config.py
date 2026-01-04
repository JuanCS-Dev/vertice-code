"""
Maestro Config Commands - Configuration CLI commands.

Commands for showing and resetting configuration.
"""

from __future__ import annotations

import sys
from typing import Annotated

import typer
from async_typer import AsyncTyper
from rich.prompt import Confirm
from rich.table import Table

from ..formatters import console, render_success
from ..state import state

# Sub-app for config commands
config_app = AsyncTyper(help="Configuration commands")


@config_app.command("show")
def config_show() -> None:
    """Show current configuration."""
    table = Table(title="Configuration", border_style="blue")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")

    config = {
        "log_file": "maestro.log",
        "agents_initialized": str(state.initialized),
        "python_version": sys.version.split()[0],
        "context_size": len(state.context),
    }

    for key, value in config.items():
        table.add_row(key, value)

    console.print(table)


@config_app.command("reset")
def config_reset(
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
) -> None:
    """Reset configuration to defaults."""
    if not force:
        confirmed = Confirm.ask("Reset all configuration?")
        if not confirmed:
            console.print("[yellow]Cancelled[/yellow]")
            raise typer.Exit(0)

    state.context.clear()
    state.initialized = False
    render_success("Configuration reset")
