"""
Maestro Shell v7.0: The Ultimate AI-Powered CLI

Supersonic. Reliable. Minimal. Production-Ready.

Architecture:
- Typer (FastAPI of CLIs) + async-typer for async support
- Rich for gorgeous terminal UI
- Structured logging (no noise)
- Graceful error handling
"""

from __future__ import annotations

import logging
import os
import sys

# Silence the noise FIRST
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "3"

from async_typer import AsyncTyper

from .commands import agent_app, config_app, info, main, version
from .executor import execute_agent_task
from .formatters import OutputFormat, console
from .state import GlobalState, state

# Structured logging (file-only, no terminal pollution)
logging.basicConfig(
    filename="maestro.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Main app (Typer instance)
app = AsyncTyper(
    name="maestro",
    help="Vertice Maestro - Sovereign Intelligence CLI",
    add_completion=True,
    rich_markup_mode="rich",
)

# Register sub-apps
app.add_typer(agent_app, name="agent")
app.add_typer(config_app, name="config")

# Register root commands
app.command()(version)
app.command()(info)
app.callback(invoke_without_command=True)(main)


def run() -> None:
    """Entry point for maestro CLI."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[bold red]Fatal error:[/bold red] {e}")
        logging.exception("Fatal error")
        sys.exit(1)


__all__ = [
    "app",
    "run",
    "state",
    "GlobalState",
    "OutputFormat",
    "execute_agent_task",
    "console",
]
