"""
GitHandler - Git Operations Command Handler.

SCALE & SUSTAIN Phase 1.3 - Semantic Modularization.

Handles: /git status, /git diff, /git log, /git branch
         Plus palette git actions.

Principles:
- Single Responsibility: Only git-related operations
- Semantic Clarity: Clear naming and documentation
- Scalability: Easy to add new git commands

Author: Vertice Team
Date: 2026-01-02
"""

from typing import TYPE_CHECKING, Optional

from rich.panel import Panel
from rich.syntax import Syntax

from .dispatcher import CommandResult

if TYPE_CHECKING:
    from vertice_cli.shell_main import InteractiveShell


class GitHandler:
    """
    Handler for git-related commands.

    Encapsulates all git operations following the Command Pattern.
    Each method corresponds to a specific git action.
    """

    def __init__(self, shell: 'InteractiveShell'):
        """
        Initialize with shell reference.

        Args:
            shell: The InteractiveShell instance providing access to
                   registry, console, and other shell components.
        """
        self.shell = shell
        self.console = shell.console
        self.registry = shell.registry

    # =========================================================================
    # Slash Commands (/git ...)
    # =========================================================================

    async def handle_status(self, cmd: str) -> CommandResult:
        """
        Handle /git status command.

        Shows current git repository status including:
        - Current branch
        - Modified files
        - Staged changes
        - Untracked files
        """
        tool = self.registry.get("git_status")
        if not tool:
            return CommandResult.error("[red]Git status tool not available[/red]")

        result = await tool.execute()

        if not result.success:
            return CommandResult.error(f"[red]Git error: {result.error}[/red]")

        output = result.data.get("output", "")
        branch = result.data.get("branch", "unknown")

        # Format output with rich panel
        self.console.print(Panel(
            output or "[dim]Working tree clean[/dim]",
            title=f"[bold cyan]Git Status[/bold cyan] ({branch})",
            border_style="cyan"
        ))

        return CommandResult.ok()

    async def handle_diff(self, cmd: str) -> CommandResult:
        """
        Handle /git diff command.

        Shows diff of changes. Supports:
        - /git diff          - All unstaged changes
        - /git diff --staged - Staged changes only
        - /git diff FILE     - Specific file diff
        """
        tool = self.registry.get("git_diff")
        if not tool:
            return CommandResult.error("[red]Git diff tool not available[/red]")

        # Parse arguments
        args = cmd.replace("/git diff", "").strip()
        kwargs = {}

        if "--staged" in args:
            kwargs["staged"] = True
            args = args.replace("--staged", "").strip()

        if args:
            kwargs["file"] = args

        result = await tool.execute(**kwargs)

        if not result.success:
            return CommandResult.error(f"[red]Git error: {result.error}[/red]")

        output = result.data.get("output", "")

        if not output:
            self.console.print("[dim]No changes to display[/dim]")
            return CommandResult.ok()

        # Display with syntax highlighting
        syntax = Syntax(output, "diff", theme="monokai", line_numbers=True)
        self.console.print(Panel(
            syntax,
            title="[bold blue]Git Diff[/bold blue]",
            border_style="blue"
        ))

        return CommandResult.ok()

    async def handle_log(self, cmd: str) -> CommandResult:
        """
        Handle /git log command.

        Shows recent commit history. Supports:
        - /git log      - Last 10 commits
        - /git log -N   - Last N commits
        """
        # Parse count argument
        args = cmd.replace("/git log", "").strip()
        count = 10  # default

        if args.startswith("-") and args[1:].isdigit():
            count = int(args[1:])

        # Use bash tool for git log (more flexible)
        bash_tool = self.registry.get("bash_command")
        if not bash_tool:
            return CommandResult.error("[red]Bash tool not available[/red]")

        result = await bash_tool.execute(
            command=f"git log --oneline -n {count}"
        )

        if not result.success:
            return CommandResult.error(f"[red]Git error: {result.error}[/red]")

        output = result.data.get("output", "")

        self.console.print(Panel(
            output or "[dim]No commits found[/dim]",
            title=f"[bold yellow]Git Log[/bold yellow] (last {count})",
            border_style="yellow"
        ))

        return CommandResult.ok()

    async def handle_branch(self, cmd: str) -> CommandResult:
        """
        Handle /git branch command.

        Shows available branches with current branch highlighted.
        """
        bash_tool = self.registry.get("bash_command")
        if not bash_tool:
            return CommandResult.error("[red]Bash tool not available[/red]")

        result = await bash_tool.execute(command="git branch -a")

        if not result.success:
            return CommandResult.error(f"[red]Git error: {result.error}[/red]")

        output = result.data.get("output", "")

        self.console.print(Panel(
            output or "[dim]No branches found[/dim]",
            title="[bold green]Git Branches[/bold green]",
            border_style="green"
        ))

        return CommandResult.ok()

    # =========================================================================
    # Palette Actions (invoked from Command Palette)
    # =========================================================================

    async def palette_status(self) -> None:
        """
        Git status action from command palette.

        Simplified version for palette invocation.
        """
        tool = self.registry.get("git_status")
        if tool:
            result = await tool.execute()
            self.console.print(result.data.get("output", "[dim]No status[/dim]"))

    async def palette_diff(self) -> None:
        """
        Git diff action from command palette.

        Shows all unstaged changes.
        """
        tool = self.registry.get("git_diff")
        if tool:
            result = await tool.execute()
            output = result.data.get("output", "")
            if output:
                syntax = Syntax(output, "diff", theme="monokai")
                self.console.print(syntax)
            else:
                self.console.print("[dim]No changes[/dim]")
