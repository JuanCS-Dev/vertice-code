"""
REPL Masterpiece Tools - Tool Processing.

This module provides tool execution handlers for
file operations, bash commands, and git operations.

Features:
- File read/write with syntax highlighting
- Bash command execution
- Git status/diff operations

Philosophy:
    "Tools should do one thing well."
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.syntax import Syntax

if TYPE_CHECKING:
    from .repl import MasterpieceREPL

logger = logging.getLogger(__name__)


async def process_tool(repl: "MasterpieceREPL", tool: str, args: str) -> None:
    """
    Execute tool with rich feedback.

    Args:
        repl: Reference to MasterpieceREPL
        tool: Tool command (e.g., /read, /write)
        args: Tool arguments
    """
    try:
        if tool == "/read":
            await _handle_read(repl, args)
        elif tool == "/write":
            await _handle_write(repl, args)
        elif tool == "/edit":
            await _handle_edit(repl, args)
        elif tool == "/run":
            await _handle_run(repl, args)
        elif tool == "/git":
            await _handle_git(repl, args)

    except Exception as e:
        repl.console.print(f"\n[red]❌ Error: {e}[/red]")
        repl.console.print("[yellow]💡 Check file permissions and path[/yellow]\n")


async def _handle_read(repl: "MasterpieceREPL", args: str) -> None:
    """Handle /read command."""
    if not args:
        repl.console.print("[yellow]Usage: /read <file>[/yellow]\n")
        return

    repl.console.print(f"[dim]📖 Reading {args}...[/dim]")
    result = await repl.file_read.execute(path=args)
    content = str(result.content) if hasattr(result, "content") else str(result)

    # Detect language for syntax highlighting
    ext = Path(args).suffix.lstrip(".")
    lang_map = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "json": "json",
        "yaml": "yaml",
        "yml": "yaml",
        "md": "markdown",
        "sh": "bash",
    }
    language = lang_map.get(ext, "text")

    if language != "text":
        syntax = Syntax(content, language, theme="monokai", line_numbers=True)
        repl.console.print(Panel(syntax, title=f"📖 {args}", border_style="green"))
    else:
        repl.console.print(Panel(content, title=f"📖 {args}", border_style="green"))

    repl.context.remember_file(args, content, "read")
    repl.console.print(f"[dim]✓ Read {len(content)} characters[/dim]\n")


async def _handle_write(repl: "MasterpieceREPL", args: str) -> None:
    """Handle /write command."""
    parts = args.split(maxsplit=1)
    if len(parts) < 2:
        repl.console.print("[yellow]Usage: /write <file> <content>[/yellow]\n")
        return

    path, content = parts
    repl.console.print(f"[dim]✍️  Writing to {path}...[/dim]")
    await repl.file_write.execute(path=path, content=content)
    repl.console.print(f"[green]✓ Written {len(content)} characters to {path}[/green]\n")


async def _handle_edit(repl: "MasterpieceREPL", args: str) -> None:
    """Handle /edit command."""
    repl.console.print("[yellow]💡 Edit mode coming soon! Use /write for now.[/yellow]\n")


async def _handle_run(repl: "MasterpieceREPL", args: str) -> None:
    """Handle /run command."""
    if not args:
        repl.console.print("[yellow]Usage: /run <command>[/yellow]\n")
        return

    repl.console.print(f"[dim]⚡ Running: {args}[/dim]")
    result = await repl.bash_tool.execute(command=args)
    output = result.output if hasattr(result, "output") else str(result)

    repl.console.print(
        Panel(output if output else "[dim]No output[/dim]", title="⚡ Output", border_style="green")
    )
    duration = result.duration if hasattr(result, "duration") else "?"
    repl.console.print(f"[dim]✓ Completed in {duration}s[/dim]\n")


async def _handle_git(repl: "MasterpieceREPL", args: str) -> None:
    """Handle /git command."""
    if not args:
        repl.console.print("[yellow]Usage: /git status | diff[/yellow]\n")
        return

    if "status" in args:
        repl.console.print("[dim]🌿 Git status...[/dim]")
        result = await repl.git_status.execute()
    elif "diff" in args:
        repl.console.print("[dim]🌿 Git diff...[/dim]")
        result = await repl.git_diff.execute()
    else:
        repl.console.print("[yellow]Usage: /git status | diff[/yellow]\n")
        return

    repl.console.print(Panel(str(result), title="🌿 Git", border_style="green"))
    repl.console.print("[dim]✓ Git operation complete[/dim]\n")


__all__ = ["process_tool"]
