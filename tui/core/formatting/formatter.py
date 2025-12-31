"""
Output Formatter - Rich Panel formatting for LLM responses.

Provides beautiful, consistent formatting for LLM outputs and tools.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text
from rich.table import Table
from rich.console import Group
from rich import box

from .colors import Colors, Icons
from .truncation import TRUNCATOR, TRUNCATION_CONFIG


class OutputFormatter:
    """
    Format outputs with rich.Panel for consistent, beautiful display.

    Usage:
        formatter = OutputFormatter()
        panel = formatter.format_response("Hello world")
        console.print(panel)
    """

    # Default styles - Using JuanCS brand colors
    RESPONSE_BORDER: str = Colors.PRIMARY   # Orange for AI responses
    SUCCESS_BORDER: str = Colors.SUCCESS    # Green (universal)
    ERROR_BORDER: str = Colors.ERROR        # Red (universal)
    WARNING_BORDER: str = Colors.WARNING    # Amber
    INFO_BORDER: str = Colors.INFO          # Blue

    # Max content length before truncation
    MAX_CONTENT_LENGTH: int = 50000   # 50K chars
    MAX_LINES: int = 500              # 500 lines

    @staticmethod
    def format_response(
        text: str,
        title: str = "Response",
        border_style: str = None,
        expand: bool = True,
        smart_truncate: bool = True
    ) -> Panel:
        """
        Format LLM response in a styled Panel with smart truncation.

        Args:
            text: Response text (may contain markdown)
            title: Panel title
            border_style: Border color (defaults to PRIMARY orange)
            expand: Whether panel should expand to full width
            smart_truncate: Use SmartTruncator for intelligent truncation

        Returns:
            rich.Panel with formatted content
        """
        border_style = border_style or Colors.PRIMARY

        # Use smart truncation
        if smart_truncate:
            truncated_content = TRUNCATOR.truncate_text(text)
            display_text = truncated_content.content
            is_truncated = truncated_content.is_truncated
            truncation_info = truncated_content.truncation_info
        else:
            # Legacy truncation (fallback)
            is_truncated = False
            if len(text) > OutputFormatter.MAX_CONTENT_LENGTH:
                display_text = text[:OutputFormatter.MAX_CONTENT_LENGTH]
                is_truncated = True
            else:
                display_text = text

            lines = display_text.split('\n')
            if len(lines) > OutputFormatter.MAX_LINES:
                display_text = '\n'.join(lines[:OutputFormatter.MAX_LINES])
                is_truncated = True

            truncation_info = ""

        # Parse as markdown for rich formatting
        try:
            content: Any = Markdown(display_text)
        except Exception:
            content = Text(display_text)

        # Build final content with truncation indicator
        if is_truncated and truncation_info:
            final_content: Any = Group(
                content,
                Text(""),  # Spacer
                Text(truncation_info, style=Colors.DIM)
            )
        else:
            final_content = content

        # Build title with optional truncation marker
        title_str = f"[{border_style}]{title}[/{border_style}]"
        if is_truncated:
            title_str += f" [{Colors.DIM}](truncated)[/{Colors.DIM}]"

        return Panel(
            final_content,
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
        Format tool execution result with smart truncation.

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
            icon = Icons.SUCCESS
            content_text = str(data) if data else "Success"
        else:
            style = OutputFormatter.ERROR_BORDER
            icon = Icons.ERROR
            content_text = error or "Failed"

        # Smart truncation for tool output
        truncated = TRUNCATOR.truncate_tool_output(content_text, tool_name)
        display_text = truncated.content

        # Add truncation indicator if needed
        if truncated.is_truncated:
            display_text += f"\n\n[{Colors.DIM}]{Icons.TRUNCATED} {truncated.expand_hint}[/{Colors.DIM}]"

        return Panel(
            Text(display_text),
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
        line_numbers: bool = True,
        show_line_count: bool = True
    ) -> Panel:
        """
        Format code with syntax highlighting in a Panel.

        Args:
            code: Source code
            language: Programming language for highlighting
            title: Optional title (defaults to language)
            line_numbers: Whether to show line numbers
            show_line_count: Show total line count in title

        Returns:
            rich.Panel with syntax highlighted code
        """
        # Smart truncation for code
        truncated = TRUNCATOR.truncate_code(code, language)
        display_code = truncated.content
        total_lines = truncated.full_length

        # Add truncation comment if needed
        if truncated.is_truncated:
            display_code += f"\n\n{truncated.expand_hint}"

        syntax = Syntax(
            display_code,
            language,
            theme="dracula",
            line_numbers=line_numbers,
            word_wrap=True,
            background_color="#1e1e2e"
        )

        # Build title with line count
        display_title = title or language.upper()
        if show_line_count:
            display_title += f" ({total_lines} lines)"
        if truncated.is_truncated:
            display_title += f" [{Colors.DIM}]truncated[/{Colors.DIM}]"

        return Panel(
            syntax,
            title=f"[{Colors.PRIMARY}]{Icons.CODE} {display_title}[/{Colors.PRIMARY}]",
            border_style=Colors.PRIMARY,
            padding=(0, 1)
        )

    @staticmethod
    def format_table(
        headers: List[str],
        rows: List[List[Any]],
        title: str = None,
        show_row_count: bool = True
    ) -> Panel:
        """
        Format a table with smart truncation.

        Args:
            headers: List of column headers
            rows: List of row data (each row is a list)
            title: Optional table title
            show_row_count: Show total row count in title

        Returns:
            rich.Panel containing the formatted table
        """
        total_rows = len(rows)
        total_cols = len(headers)

        # Smart truncation
        trunc_headers, trunc_rows, is_truncated, truncation_info = (
            TRUNCATOR.truncate_table_data(headers, rows)
        )

        # Build Rich Table
        table = Table(
            box=box.ROUNDED,
            header_style=f"bold {Colors.PRIMARY}",
            row_styles=["", Colors.DIM],
            padding=(0, 1),
            collapse_padding=True,
            show_lines=False
        )

        # Add columns with max width
        for header in trunc_headers:
            table.add_column(
                header,
                style=Colors.SECONDARY,
                max_width=TRUNCATION_CONFIG.max_cell_width,
                overflow="ellipsis"
            )

        # Add rows
        for row in trunc_rows:
            table.add_row(*[str(cell) for cell in row])

        # Build title
        title_parts: List[str] = []
        if title:
            title_parts.append(title)
        if show_row_count:
            title_parts.append(f"{total_rows} rows x {total_cols} cols")
        if is_truncated:
            title_parts.append(f"[{Colors.DIM}]{truncation_info}[/{Colors.DIM}]")

        display_title = " | ".join(title_parts) if title_parts else "Table"

        return Panel(
            table,
            title=f"[{Colors.PRIMARY}]{display_title}[/{Colors.PRIMARY}]",
            border_style=Colors.PRIMARY,
            padding=(0, 1)
        )

    @staticmethod
    def format_error(message: str, title: str = "Error") -> Panel:
        """Format error message with smart truncation."""
        if len(message) > TRUNCATION_CONFIG.max_error_length:
            display_msg = message[:TRUNCATION_CONFIG.max_error_length]
            hidden = len(message) - TRUNCATION_CONFIG.max_error_length
            display_msg += f"\n\n[{Colors.DIM}]{Icons.TRUNCATED} ... {hidden} more chars[/{Colors.DIM}]"
        else:
            display_msg = message

        return Panel(
            Text(display_msg, style=Colors.ERROR),
            title=f"[{Colors.ERROR}]{Icons.ERROR} {title}[/{Colors.ERROR}]",
            border_style=Colors.ERROR,
            padding=(0, 1)
        )

    @staticmethod
    def format_success(message: str, title: str = "Success") -> Panel:
        """Format success message."""
        return Panel(
            Text(message, style=Colors.SUCCESS),
            title=f"[{Colors.SUCCESS}]{Icons.SUCCESS} {title}[/{Colors.SUCCESS}]",
            border_style=Colors.SUCCESS,
            padding=(0, 1)
        )

    @staticmethod
    def format_warning(message: str, title: str = "Warning") -> Panel:
        """Format warning message."""
        return Panel(
            Text(message, style=Colors.WARNING),
            title=f"[{Colors.WARNING}]{Icons.WARNING} {title}[/{Colors.WARNING}]",
            border_style=Colors.WARNING,
            padding=(0, 1)
        )

    @staticmethod
    def format_info(message: str, title: str = "Info") -> Panel:
        """Format info message."""
        return Panel(
            Text(message, style=Colors.INFO),
            title=f"[{Colors.INFO}]{Icons.INFO} {title}[/{Colors.INFO}]",
            border_style=Colors.INFO,
            padding=(0, 1)
        )

    @staticmethod
    def format_action(action: str) -> Text:
        """Format action indicator with orange color."""
        text = Text()
        text.append(f"{Icons.EXECUTING} ", style=f"bold {Colors.ACTION}")
        text.append(action, style=Colors.MUTED)
        return text

    @staticmethod
    def format_thinking() -> Text:
        """Format thinking indicator with orange color."""
        text = Text()
        text.append(f"{Icons.THINKING} ", style=f"bold {Colors.ACTION}")
        text.append("Thinking...", style=f"italic {Colors.MUTED}")
        return text

    @staticmethod
    def format_tool_executing(tool_name: str, args: Dict[str, Any] = None) -> Text:
        """Format tool execution indicator."""
        text = Text()
        text.append(f"{Icons.TOOL} ", style=f"bold {Colors.TOOL_EXEC}")
        text.append("Executing: ", style=Colors.MUTED)
        text.append(tool_name, style=f"bold {Colors.PRIMARY}")
        if args:
            args_str = str(args)[:50] + "..." if len(str(args)) > 50 else str(args)
            text.append(f" {args_str}", style=Colors.DIM)
        return text

    @staticmethod
    def format_tool_success(tool_name: str, result: str = None) -> Text:
        """Format tool success message."""
        text = Text()
        text.append(f"{Icons.SUCCESS} ", style=f"bold {Colors.SUCCESS}")
        text.append(tool_name, style=f"bold {Colors.PRIMARY}")
        text.append(": ", style=Colors.MUTED)
        text.append("Success", style=Colors.SUCCESS)
        if result:
            result_str = str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
            text.append(f" - {result_str}", style=Colors.DIM)
        return text

    @staticmethod
    def format_tool_error(tool_name: str, error: str) -> Text:
        """Format tool error message."""
        text = Text()
        text.append(f"{Icons.ERROR} ", style=f"bold {Colors.ERROR}")
        text.append(tool_name, style=f"bold {Colors.PRIMARY}")
        text.append(": ", style=Colors.MUTED)
        text.append(error[:200], style=Colors.ERROR)
        return text

    @staticmethod
    def format_agent_routing(agent_name: str, confidence: float) -> Text:
        """Format agent auto-routing message."""
        text = Text()
        text.append(f"{Icons.ROUTING} ", style=f"bold {Colors.ROUTING}")
        text.append("Auto-routing to ", style=Colors.MUTED)
        text.append(f"{agent_name.title()}Agent", style=f"bold {Colors.AGENT}")
        text.append(f" (confidence: {int(confidence*100)}%)", style=Colors.DIM)
        return text

    @staticmethod
    def format_agent_description(description: str) -> Text:
        """Format agent description."""
        text = Text()
        text.append("   ", style="")
        text.append(description, style=f"italic {Colors.SECONDARY}")
        return text

    @staticmethod
    def format_governance_report(report: str) -> Text:
        """Format governance observation report."""
        text = Text()
        text.append(f"{Icons.SECURITY} ", style=f"bold {Colors.INFO}")
        text.append(report, style=Colors.MUTED)
        return text
