"""
PaletteHandler - Command Palette Management.

SCALE & SUSTAIN Phase 1.6 - Semantic Modularization.

Handles:
- Command palette registration
- Interactive palette display
- Squad/workflow palette actions

Principles:
- Single Responsibility: Palette interaction lifecycle
- Semantic Clarity: All palette operations in one place
- Scalability: Easy to add new palette commands

Author: Vertice Team
Date: 2026-01-02
"""

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from vertice_cli.shell_main import InteractiveShell

logger = logging.getLogger(__name__)


class PaletteHandler:
    """
    Handler for command palette operations.

    Manages:
    1. Registration of palette commands
    2. Interactive palette search/selection
    3. Squad and workflow palette actions
    """

    def __init__(self, shell: "InteractiveShell"):
        """
        Initialize with shell reference.

        Args:
            shell: The InteractiveShell instance providing access to
                   palette, console, handlers, etc.
        """
        self.shell = shell
        self.console = shell.console
        self.palette = shell.palette
        self.enhanced_input = shell.enhanced_input

    # =========================================================================
    # Palette Registration
    # =========================================================================

    def register_palette_commands(self) -> None:
        """
        Register commands in command palette (Ctrl+K).

        SCALE & SUSTAIN Phase 1.3: Delegates to modular handlers for
        maintainability and semantic clarity.
        """
        from vertice_cli.tui.components.palette import Command, CommandCategory
        from vertice_cli.core.help_system import help_system

        # File operations - delegated to FileOpsHandler
        self.palette.add_command(
            Command(
                id="file.read",
                title="Read File",
                description="Read and display file contents",
                category=CommandCategory.FILE,
                keywords=["open", "cat", "view", "show"],
                keybinding=None,
                action=lambda: self.shell._file_ops_handler.palette_read_file(),
            )
        )

        self.palette.add_command(
            Command(
                id="file.write",
                title="Write File",
                description="Create or overwrite a file",
                category=CommandCategory.FILE,
                keywords=["create", "save", "new"],
                action=lambda: self.shell._file_ops_handler.palette_write_file(),
            )
        )

        self.palette.add_command(
            Command(
                id="file.edit",
                title="Edit File",
                description="Edit file with AI assistance",
                category=CommandCategory.EDIT,
                keywords=["modify", "change", "update", "fix"],
                action=lambda: self.shell._file_ops_handler.palette_edit_file(),
            )
        )

        # Git operations - delegated to GitHandler
        self.palette.add_command(
            Command(
                id="git.status",
                title="Git Status",
                description="Show git repository status",
                category=CommandCategory.GIT,
                keywords=["git", "status", "changes", "diff"],
                action=lambda: self.shell._git_handler.palette_status(),
            )
        )

        self.palette.add_command(
            Command(
                id="git.diff",
                title="Git Diff",
                description="Show git diff",
                category=CommandCategory.GIT,
                keywords=["git", "diff", "changes"],
                action=lambda: self.shell._git_handler.palette_diff(),
            )
        )

        # Search operations - delegated to FileOpsHandler
        self.palette.add_command(
            Command(
                id="search.files",
                title="Search Files",
                description="Search for text in files",
                category=CommandCategory.SEARCH,
                keywords=["find", "grep", "search", "locate"],
                action=lambda: self.shell._file_ops_handler.palette_search_files(),
            )
        )

        # Help & System
        self.palette.add_command(
            Command(
                id="help.main",
                title="Help",
                description="Show main help",
                category=CommandCategory.HELP,
                keywords=["help", "docs", "guide"],
                keybinding="?",
                action=lambda: help_system.show_main_help(),
            )
        )

        self.palette.add_command(
            Command(
                id="system.clear",
                title="Clear Screen",
                description="Clear the terminal screen",
                category=CommandCategory.SYSTEM,
                keywords=["clear", "cls", "clean"],
                action=self.console.clear,
            )
        )

        self.palette.add_command(
            Command(
                id="tools.list",
                title="List Available Tools",
                description="Show all registered tools",
                category=CommandCategory.TOOLS,
                keywords=["tools", "list", "available"],
                action=lambda: self.shell._file_ops_handler.palette_list_tools(),
            )
        )

        # DevSquad commands
        self.palette.add_command(
            Command(
                id="squad.run",
                title="Run DevSquad Mission",
                description="Execute a complex task with agent squad",
                category=CommandCategory.TOOLS,
                keywords=["squad", "mission", "agent", "devsquad"],
                action=lambda: self.palette_run_squad(),
            )
        )

        self.palette.add_command(
            Command(
                id="workflow.list",
                title="List Workflows",
                description="Show available workflows",
                category=CommandCategory.TOOLS,
                keywords=["workflow", "list", "template"],
                action=lambda: self.palette_list_workflows(),
            )
        )

    # =========================================================================
    # Interactive Palette
    # =========================================================================

    async def show_palette_interactive(self) -> Optional["Command"]:
        """
        Show interactive palette and return selected command.

        Returns:
            Selected Command or None if cancelled.
        """
        from vertice_cli.tui.components.palette import CATEGORY_CONFIG

        # Show search prompt
        query = await self.enhanced_input.prompt_async("[cyan]Command Palette >[/cyan] ")

        if not query or not query.strip():
            return None

        # Fuzzy search
        results = self.palette.search(query, limit=10)

        if not results:
            self.console.print("[yellow]No commands found[/yellow]")
            return None

        # Display results
        self.console.print("\n[cyan]Results:[/cyan]")
        for i, cmd in enumerate(results, 1):
            category_icon = CATEGORY_CONFIG.get(cmd.category, {}).get("icon", "📄")
            self.console.print(f"  {i}. {category_icon} {cmd.title} - [dim]{cmd.description}[/dim]")

        # Get selection
        try:
            selection = await self.enhanced_input.prompt_async(
                "\nSelect (1-10) or Enter to cancel: "
            )
            if selection and selection.isdigit():
                idx = int(selection) - 1
                if 0 <= idx < len(results):
                    return results[idx]
        except (ValueError, IndexError):
            pass

        return None

    # =========================================================================
    # Palette Actions
    # =========================================================================

    async def palette_run_squad(self) -> None:
        """Handle squad run from palette."""
        self.console.print("[bold blue]🤖 DevSquad Mission[/bold blue]")

        # Use input_session if available, or simple prompt
        try:
            request = await self.shell.input_session.prompt_async("Mission Request: ")
        except (AttributeError, EOFError, KeyboardInterrupt):
            # Fallback if input_session not fully set up in tests or some modes
            request = self.console.input("Mission Request: ")

        if not request:
            return

        try:
            with self.console.status("[bold green]DevSquad Active...[/bold green]"):
                result = await self.shell.squad.execute_workflow(request)
            self.console.print(self.shell.squad.get_phase_summary(result))
        except Exception as e:
            self.console.print(f"[bold red]Error:[/bold red] {e}")

    def palette_list_workflows(self) -> None:
        """Handle workflow list from palette."""
        from vertice_cli.orchestration.workflows import WorkflowLibrary
        from rich.table import Table

        lib = WorkflowLibrary()
        workflows = lib.list_workflows()

        table = Table(title="Available Workflows")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="blue")
        table.add_column("Description", style="white")

        for w in workflows:
            table.add_row(w.id, w.name, w.description)

        self.console.print(table)
