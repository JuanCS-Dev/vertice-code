"""
FileOpsHandler - File Operations Command Handler.

SCALE & SUSTAIN Phase 1.3 - Semantic Modularization.

Handles: File palette actions (read, write, edit, search)
         File-related slash commands.

Principles:
- Single Responsibility: Only file operations
- Semantic Clarity: Clear naming and documentation
- Scalability: Easy to add new file operations

Author: Vertice Team
Date: 2026-01-02
"""

from typing import TYPE_CHECKING, Optional, Callable, Coroutine, Any

from rich.panel import Panel
from rich.table import Table

from .dispatcher import CommandResult

if TYPE_CHECKING:
    from vertice_cli.shell_main import InteractiveShell


class FileOpsHandler:
    """
    Handler for file-related operations.

    Encapsulates file operations following the Command Pattern.
    Supports both slash commands and palette actions.
    """

    def __init__(self, shell: 'InteractiveShell'):
        """
        Initialize with shell reference.

        Args:
            shell: The InteractiveShell instance providing access to
                   registry, console, input, and LLM processing.
        """
        self.shell = shell
        self.console = shell.console
        self.registry = shell.registry

    # =========================================================================
    # Slash Commands
    # =========================================================================

    async def handle_read(self, cmd: str) -> CommandResult:
        """
        Handle /read FILE command.

        Reads and displays file content with syntax highlighting.
        """
        file_path = cmd.replace("/read", "").strip()

        if not file_path:
            return CommandResult.error("[red]Usage: /read <file_path>[/red]")

        tool = self.registry.get("read_file")
        if not tool:
            return CommandResult.error("[red]Read file tool not available[/red]")

        result = await tool.execute(path=file_path)

        if not result.success:
            return CommandResult.error(f"[red]Error: {result.error}[/red]")

        content = result.data.get("content", "")

        # Use shell's result renderer for consistent output
        if hasattr(self.shell, '_result_renderer'):
            self.shell._result_renderer.render("read_file", result, {"path": file_path})
        else:
            self.console.print(Panel(content, title=file_path))

        return CommandResult.ok()

    async def handle_write(self, cmd: str) -> CommandResult:
        """
        Handle /write FILE command.

        Writes content to a file (prompts for content).
        """
        file_path = cmd.replace("/write", "").strip()

        if not file_path:
            return CommandResult.error("[red]Usage: /write <file_path>[/red]")

        # Prompt for content
        content = await self.shell.enhanced_input.prompt_async(
            f"Content for {file_path}: "
        )

        if not content:
            return CommandResult.error("[yellow]Write cancelled[/yellow]")

        tool = self.registry.get("write_file")
        if not tool:
            return CommandResult.error("[red]Write file tool not available[/red]")

        result = await tool.execute(path=file_path, content=content)

        if not result.success:
            return CommandResult.error(f"[red]Error: {result.error}[/red]")

        return CommandResult.ok(f"[green]Written to {file_path}[/green]")

    async def handle_search(self, cmd: str) -> CommandResult:
        """
        Handle /search PATTERN command.

        Searches for files matching pattern.
        """
        pattern = cmd.replace("/search", "").strip()

        if not pattern:
            return CommandResult.error("[red]Usage: /search <pattern>[/red]")

        tool = self.registry.get("search_files")
        if not tool:
            return CommandResult.error("[red]Search tool not available[/red]")

        result = await tool.execute(pattern=pattern)

        if not result.success:
            return CommandResult.error(f"[red]Error: {result.error}[/red]")

        matches = result.data.get("matches", [])

        if not matches:
            self.console.print(f"[dim]No matches for '{pattern}'[/dim]")
            return CommandResult.ok()

        # Display results in table
        table = Table(title=f"Search Results: {pattern}")
        table.add_column("File", style="cyan")
        table.add_column("Line", justify="right", style="yellow")
        table.add_column("Content", style="white")

        for match in matches[:20]:  # Limit to 20 results
            table.add_row(
                match.get("file", ""),
                str(match.get("line", "")),
                match.get("text", "")[:80]  # Truncate long lines
            )

        self.console.print(table)

        if len(matches) > 20:
            self.console.print(f"[dim]... and {len(matches) - 20} more matches[/dim]")

        return CommandResult.ok()

    async def handle_tree(self, cmd: str) -> CommandResult:
        """
        Handle /tree [PATH] command.

        Shows directory tree structure.
        """
        path = cmd.replace("/tree", "").strip() or "."

        tool = self.registry.get("get_directory_tree")
        if not tool:
            return CommandResult.error("[red]Tree tool not available[/red]")

        result = await tool.execute(path=path)

        if not result.success:
            return CommandResult.error(f"[red]Error: {result.error}[/red]")

        tree = result.data.get("tree", "")

        self.console.print(Panel(
            tree or "[dim]Empty directory[/dim]",
            title=f"[bold cyan]Directory Tree[/bold cyan] ({path})",
            border_style="cyan"
        ))

        return CommandResult.ok()

    # =========================================================================
    # Palette Actions (invoked from Command Palette)
    # =========================================================================

    async def palette_read_file(self) -> None:
        """
        Read file action from command palette.

        Prompts for file path and delegates to LLM processing.
        """
        file_path = await self.shell.enhanced_input.prompt_async("File path: ")
        if file_path:
            await self.shell._process_request_with_llm(f"read {file_path}", None)

    async def palette_write_file(self) -> None:
        """
        Write file action from command palette.

        Prompts for file path and content, then processes via LLM.
        """
        file_path = await self.shell.enhanced_input.prompt_async("File path: ")
        if file_path:
            content = await self.shell.enhanced_input.prompt_async("Content: ")
            if content:
                await self.shell._process_request_with_llm(
                    f"write {file_path} with: {content}", None
                )

    async def palette_edit_file(self) -> None:
        """
        Edit file action from command palette.

        Prompts for file path and edit instruction.
        """
        file_path = await self.shell.enhanced_input.prompt_async("File path: ")
        if file_path:
            instruction = await self.shell.enhanced_input.prompt_async(
                "Edit instruction: "
            )
            if instruction:
                await self.shell._process_request_with_llm(
                    f"edit {file_path}: {instruction}", None
                )

    async def palette_search_files(self) -> None:
        """
        Search files action from command palette.

        Prompts for search pattern and processes via LLM.
        """
        pattern = await self.shell.enhanced_input.prompt_async("Search pattern: ")
        if pattern:
            await self.shell._process_request_with_llm(f"search for {pattern}", None)

    def palette_list_tools(self) -> None:
        """
        List tools action from command palette.

        Displays all available tools in a formatted table.
        """
        tools = self.registry.list_tools()

        table = Table(title="Available Tools")
        table.add_column("Tool", style="cyan")
        table.add_column("Category", style="yellow")
        table.add_column("Description", style="white")

        for tool_name in sorted(tools):
            tool = self.registry.get(tool_name)
            category = getattr(tool, 'category', None)
            category_str = category.value if hasattr(category, 'value') else str(category or '')
            description = getattr(tool, 'description', '')
            table.add_row(tool_name, category_str, description[:60])

        self.console.print(table)
