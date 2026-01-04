"""
Result Renderers - Visual presentation using Rich.

Design Principles:
- Separation from data formatting (renderers receive FormattedResult)
- Tool-specific visual styles
- Consistent Rich theme usage
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console

from .formatters import FormattedResult, ToolResultFormatter


class ResultRenderer:
    """
    Renders tool results to Rich console.

    Uses ToolResultFormatter for data transformation,
    then applies tool-specific visual styling.
    """

    def __init__(self, console: "Console"):
        self.console = console
        self.formatter = ToolResultFormatter()

    def render(
        self,
        tool_name: str,
        result: Any,
        args: Dict[str, Any],
    ) -> str:
        """
        Render tool result to console and return summary string.

        Args:
            tool_name: Name of the executed tool
            result: Tool execution result
            args: Arguments passed to tool

        Returns:
            Summary string for logging
        """
        if not result.success:
            return self._render_error(tool_name, result)

        # Get formatted result
        formatted = self.formatter.format(tool_name, result, args)

        # Dispatch to tool-specific renderer
        renderer_method = getattr(self, f"_render_{tool_name.lower()}", self._render_default)
        renderer_method(formatted, result, args)

        # Return summary with status icon
        icon = "✓" if formatted.success else "❌"
        return f"{icon} {formatted.summary}"

    def _render_error(self, tool_name: str, result: Any) -> str:
        """Render error result."""
        error_msg = result.error or str(result.data)
        self.console.print(f"[red]❌ {tool_name}: {error_msg}[/red]")
        return f"❌ {error_msg}"

    def _render_default(
        self,
        formatted: FormattedResult,
        result: Any,
        args: Dict[str, Any],
    ) -> None:
        """Default renderer - just print summary and details."""
        self.console.print(f"[green]✓ {formatted.summary}[/green]")
        if formatted.details:
            self.console.print(formatted.details)

    def _render_read_file(
        self,
        formatted: FormattedResult,
        result: Any,
        args: Dict[str, Any],
    ) -> None:
        """Render read_file with syntax highlighting."""
        from rich.syntax import Syntax

        # Detect language from file extension
        path = result.metadata.get("path", args.get("path", ""))
        lang = Path(path).suffix.lstrip(".") or "text"

        # Language mapping for common extensions
        lang_map = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "jsx": "jsx",
            "tsx": "tsx",
            "md": "markdown",
            "yml": "yaml",
            "json": "json",
            "rs": "rust",
            "go": "go",
            "rb": "ruby",
            "sh": "bash",
            "bash": "bash",
        }
        lang = lang_map.get(lang, lang)

        # Render with syntax highlighting
        if formatted.details:
            syntax = Syntax(
                formatted.details,
                lang,
                theme="monokai",
                line_numbers=True,
                word_wrap=True,
            )
            self.console.print(syntax)

        self.console.print(f"[green]✓ {formatted.summary}[/green]")

    # Alias for alternative tool name
    _render_readfile = _render_read_file

    def _render_search_files(
        self,
        formatted: FormattedResult,
        result: Any,
        args: Dict[str, Any],
    ) -> None:
        """Render search results as table."""
        from rich.table import Table

        pattern = args.get("pattern", "?")
        matches = result.data or []

        if not matches:
            self.console.print("[yellow]No matches found[/yellow]")
            return

        table = Table(title=f"Search Results: '{pattern}'")
        table.add_column("File", style="cyan")
        table.add_column("Line", style="yellow", justify="right")
        table.add_column("Text", style="white")

        for match in matches[:10]:  # Limit to 10 results
            table.add_row(
                str(match.get("file", "")),
                str(match.get("line", "")),
                str(match.get("text", ""))[:80],
            )

        self.console.print(table)

        if len(matches) > 10:
            self.console.print(f"[dim]... and {len(matches) - 10} more matches[/dim]")

        self.console.print(f"[green]✓ {formatted.summary}[/green]")

    _render_searchfiles = _render_search_files

    def _render_bash_command(
        self,
        formatted: FormattedResult,
        result: Any,
        args: Dict[str, Any],
    ) -> None:
        """Render bash command output."""
        data = result.data or {}

        if data.get("stdout"):
            self.console.print("[dim]stdout:[/dim]")
            self.console.print(data["stdout"])

        if data.get("stderr"):
            self.console.print("[yellow]stderr:[/yellow]")
            self.console.print(data["stderr"])

        self.console.print(f"[green]✓ {formatted.summary}[/green]")

    _render_bash = _render_bash_command

    def _render_git_status(
        self,
        formatted: FormattedResult,
        result: Any,
        args: Dict[str, Any],
    ) -> None:
        """Render git status in a panel."""
        from rich.panel import Panel

        self.console.print(
            Panel(
                formatted.details or "Clean working tree",
                title="Git Status",
                border_style="green",
            )
        )

    _render_gitstatus = _render_git_status

    def _render_git_diff(
        self,
        formatted: FormattedResult,
        result: Any,
        args: Dict[str, Any],
    ) -> None:
        """Render git diff with syntax highlighting."""
        from rich.panel import Panel
        from rich.syntax import Syntax

        if formatted.details:
            syntax = Syntax(formatted.details, "diff", theme="monokai")
            self.console.print(
                Panel(
                    syntax,
                    title="[bold]Git Diff[/bold]",
                    border_style="blue",
                )
            )
        else:
            self.console.print("[dim]No changes[/dim]")

    _render_gitdiff = _render_git_diff

    def _render_list_directory(
        self,
        formatted: FormattedResult,
        result: Any,
        args: Dict[str, Any],
    ) -> None:
        """Render directory listing."""
        data = result.data or {}
        directories = data.get("directories", [])
        files = data.get("files", [])

        self.console.print(f"[cyan]Directories ({len(directories)}):[/cyan]")
        for d in directories[:10]:
            name = d.get("name", d) if isinstance(d, dict) else d
            self.console.print(f"  [bold cyan]{name}/[/bold cyan]")

        self.console.print(f"\n[cyan]Files ({len(files)}):[/cyan]")
        for f in files[:10]:
            if isinstance(f, dict):
                name = f.get("name", "")
                size = f.get("size", 0)
                self.console.print(f"  {name} ({size} bytes)")
            else:
                self.console.print(f"  {f}")

        if len(directories) > 10 or len(files) > 10:
            self.console.print("[dim]... truncated[/dim]")

        self.console.print(f"[green]✓ {formatted.summary}[/green]")

    _render_listdirectory = _render_list_directory

    def _render_get_directory_tree(
        self,
        formatted: FormattedResult,
        result: Any,
        args: Dict[str, Any],
    ) -> None:
        """Render directory tree in a panel."""
        from rich.panel import Panel

        self.console.print(
            Panel(
                formatted.details or "",
                title="Directory Tree",
                border_style="blue",
            )
        )

    _render_getdirectorytree = _render_get_directory_tree

    def _render_ls(
        self,
        formatted: FormattedResult,
        result: Any,
        args: Dict[str, Any],
    ) -> None:
        """Render ls output."""
        items = result.data or []
        long_format = result.metadata.get("long_format", False)

        for item in items:
            icon = "📁" if item.get("type") == "dir" else "📄"
            name = item.get("name", str(item))

            if item.get("type") == "dir":
                name = f"[bold cyan]{name}[/bold cyan]"

            if long_format:
                size = item.get("size", 0)
                self.console.print(f"{icon} {name} ({size} bytes)")
            else:
                self.console.print(f"{icon} {name}")

        self.console.print(f"[green]✓ {formatted.summary}[/green]")

    def _render_pwd(
        self,
        formatted: FormattedResult,
        result: Any,
        args: Dict[str, Any],
    ) -> None:
        """Render current working directory."""
        self.console.print(f"[bold green]{result.data}[/bold green]")

    def _render_cd(
        self,
        formatted: FormattedResult,
        result: Any,
        args: Dict[str, Any],
    ) -> None:
        """Render directory change."""
        new_cwd = result.metadata.get("new_cwd", "")
        self.console.print(f"[green]→ {new_cwd}[/green]")

    def _render_cat(
        self,
        formatted: FormattedResult,
        result: Any,
        args: Dict[str, Any],
    ) -> None:
        """Render cat output with syntax highlighting."""
        from rich.syntax import Syntax

        path = result.metadata.get("path", "")
        lang = Path(path).suffix.lstrip(".") or "text"

        if result.data:
            syntax = Syntax(
                str(result.data),
                lang,
                theme="monokai",
                line_numbers=True,
            )
            self.console.print(syntax)

        self.console.print(f"[green]✓ {formatted.summary}[/green]")

    def render_batch(
        self,
        results: List[tuple],
    ) -> List[str]:
        """
        Render multiple tool results.

        Args:
            results: List of (tool_name, result, args) tuples

        Returns:
            List of summary strings
        """
        summaries = []
        for tool_name, result, args in results:
            summary = self.render(tool_name, result, args)
            summaries.append(summary)
        return summaries
