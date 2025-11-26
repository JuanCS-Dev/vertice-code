"""
Output Formatter - Rich Panel formatting for LLM responses and tool results.
============================================================================

Provides beautiful, consistent formatting for:
- LLM responses (cyan bordered panels)
- Tool execution results (green/red panels)
- Code blocks with syntax highlighting
- Error messages

Design Philosophy:
- Panel com borda (rich.Panel) for all major outputs
- Cyan for AI responses
- Green for success, Red for errors
- Smart truncation for long outputs
"""

from typing import Any, Optional
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text
from rich.console import Console, RenderableType


class OutputFormatter:
    """
    Format outputs with rich.Panel for consistent, beautiful display.

    Usage:
        formatter = OutputFormatter()
        panel = formatter.format_response("Hello world")
        console.print(panel)
    """

    # Default styles
    RESPONSE_BORDER = "cyan"
    SUCCESS_BORDER = "green"
    ERROR_BORDER = "red"
    WARNING_BORDER = "yellow"
    INFO_BORDER = "blue"

    # Max content length before truncation
    MAX_CONTENT_LENGTH = 5000
    MAX_LINES = 100

    @staticmethod
    def format_response(
        text: str,
        title: str = "Response",
        border_style: str = "cyan",
        expand: bool = True
    ) -> Panel:
        """
        Format LLM response in a styled Panel.

        Args:
            text: Response text (may contain markdown)
            title: Panel title
            border_style: Border color
            expand: Whether panel should expand to full width

        Returns:
            rich.Panel with formatted content
        """
        # Truncate if too long
        truncated = False
        if len(text) > OutputFormatter.MAX_CONTENT_LENGTH:
            text = text[:OutputFormatter.MAX_CONTENT_LENGTH] + "\n\n[dim]... (truncated)[/dim]"
            truncated = True

        lines = text.split('\n')
        if len(lines) > OutputFormatter.MAX_LINES:
            text = '\n'.join(lines[:OutputFormatter.MAX_LINES]) + "\n\n[dim]... (truncated)[/dim]"
            truncated = True

        # Parse as markdown for rich formatting
        try:
            content = Markdown(text)
        except Exception:
            # Fallback to plain text
            content = Text(text)

        title_str = f"[{border_style}]{title}[/{border_style}]"
        if truncated:
            title_str += " [dim](truncated)[/dim]"

        return Panel(
            content,
            title=title_str,
            border_style=border_style,
            padding=(1, 2),
            expand=expand
        )

    @staticmethod
    def format_tool_result(
        tool_name: str,
        success: bool,
        data: Any = None,
        error: Optional[str] = None
    ) -> Panel:
        """
        Format tool execution result.

        Args:
            tool_name: Name of the executed tool
            success: Whether execution succeeded
            data: Result data (on success)
            error: Error message (on failure)

        Returns:
            rich.Panel with result
        """
        if success:
            style = OutputFormatter.SUCCESS_BORDER
            icon = "✓"
            content_text = str(data) if data else "Success"
        else:
            style = OutputFormatter.ERROR_BORDER
            icon = "✗"
            content_text = error or "Failed"

        # Truncate long content
        if len(content_text) > 500:
            content_text = content_text[:500] + "..."

        return Panel(
            Text(content_text),
            title=f"[{style}]{icon} {tool_name}[/{style}]",
            border_style=style,
            padding=(0, 1),
            expand=False
        )

    @staticmethod
    def format_code_block(
        code: str,
        language: str = "python",
        title: Optional[str] = None,
        line_numbers: bool = True
    ) -> Panel:
        """
        Format code with syntax highlighting in a Panel.

        Args:
            code: Source code
            language: Programming language for highlighting
            title: Optional title (defaults to language)
            line_numbers: Whether to show line numbers

        Returns:
            rich.Panel with syntax highlighted code
        """
        # Truncate very long code
        lines = code.split('\n')
        if len(lines) > 100:
            code = '\n'.join(lines[:100]) + f"\n\n# ... ({len(lines) - 100} more lines)"

        syntax = Syntax(
            code,
            language,
            theme="dracula",
            line_numbers=line_numbers,
            word_wrap=True,
            background_color="#1e1e2e"
        )

        display_title = title or language.upper()

        return Panel(
            syntax,
            title=f"[cyan]{display_title}[/cyan]",
            border_style="cyan",
            padding=(0, 1)
        )

    @staticmethod
    def format_error(message: str, title: str = "Error") -> Panel:
        """Format error message."""
        return Panel(
            Text(message, style="red"),
            title=f"[red]✗ {title}[/red]",
            border_style="red",
            padding=(0, 1)
        )

    @staticmethod
    def format_success(message: str, title: str = "Success") -> Panel:
        """Format success message."""
        return Panel(
            Text(message, style="green"),
            title=f"[green]✓ {title}[/green]",
            border_style="green",
            padding=(0, 1)
        )

    @staticmethod
    def format_warning(message: str, title: str = "Warning") -> Panel:
        """Format warning message."""
        return Panel(
            Text(message, style="yellow"),
            title=f"[yellow]⚠ {title}[/yellow]",
            border_style="yellow",
            padding=(0, 1)
        )

    @staticmethod
    def format_info(message: str, title: str = "Info") -> Panel:
        """Format info message."""
        return Panel(
            Text(message),
            title=f"[blue]ℹ {title}[/blue]",
            border_style="blue",
            padding=(0, 1)
        )

    @staticmethod
    def format_action(action: str) -> Text:
        """Format action indicator (dim text)."""
        return Text(f"● {action}", style="dim italic")

    @staticmethod
    def format_thinking() -> Text:
        """Format thinking indicator."""
        return Text("● Thinking...", style="dim italic")


# Convenience functions
def response_panel(text: str, title: str = "Response") -> Panel:
    """Quick helper for response panels."""
    return OutputFormatter.format_response(text, title)


def tool_panel(name: str, success: bool, data: Any = None, error: str = None) -> Panel:
    """Quick helper for tool result panels."""
    return OutputFormatter.format_tool_result(name, success, data, error)


def code_panel(code: str, language: str = "python") -> Panel:
    """Quick helper for code panels."""
    return OutputFormatter.format_code_block(code, language)
