"""
Smart Truncation System - Claude Code / OpenAI Codex Style.

Intelligent content truncation with expansion support.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .colors import Colors, Icons


@dataclass
class TruncationConfig:
    """Configuration for smart truncation behavior."""

    # Content limits (increased from original 5000)
    max_chars: int = 50000  # 50K chars before truncation
    max_lines: int = 500  # Max lines before truncation
    preview_lines: int = 30  # Lines shown when truncated
    preview_chars: int = 3000  # Chars shown when truncated

    # Table limits
    max_table_rows: int = 50  # Max rows visible
    max_table_cols: int = 10  # Max columns visible
    max_cell_width: int = 50  # Max chars per cell

    # Code block limits
    max_code_lines: int = 40  # Code lines before collapse
    code_preview_lines: int = 20  # Lines shown in preview

    # Tool output limits
    max_tool_output: int = 2000  # Tool result chars
    max_error_length: int = 500  # Error message chars


# Global config instance
TRUNCATION_CONFIG = TruncationConfig()


@dataclass
class TruncatedContent:
    """Represents content that may be truncated with expansion capability."""

    content: str
    is_truncated: bool
    full_length: int
    preview_length: int
    content_type: str  # "text", "code", "table", "tool_output"
    expand_hint: str = ""

    @property
    def truncation_info(self) -> str:
        """Human-readable truncation info."""
        if not self.is_truncated:
            return ""
        hidden = self.full_length - self.preview_length
        if self.content_type == "code":
            return f"[{Colors.DIM}]{Icons.TRUNCATED} {hidden} more lines (use /expand to see full)[/{Colors.DIM}]"
        elif self.content_type == "table":
            return f"[{Colors.DIM}]{Icons.TRUNCATED} {hidden} more rows[/{Colors.DIM}]"
        else:
            return f"[{Colors.DIM}]{Icons.TRUNCATED} {hidden} more chars[/{Colors.DIM}]"


class SmartTruncator:
    """
    Intelligent content truncation with expansion support.

    Features:
    - Preserves semantic boundaries (paragraphs, code blocks)
    - Shows truncation indicator with size info
    - Supports /expand command to see full content
    - Different strategies for different content types
    """

    def __init__(self, config: TruncationConfig = None) -> None:
        """Initialize truncator with config."""
        self.config = config or TRUNCATION_CONFIG

    def truncate_text(
        self, text: str, max_lines: int = None, max_chars: int = None
    ) -> TruncatedContent:
        """
        Truncate text intelligently, preserving paragraph boundaries.

        Args:
            text: Input text
            max_lines: Override max lines
            max_chars: Override max chars

        Returns:
            TruncatedContent with preview and metadata
        """
        max_lines = max_lines or self.config.preview_lines
        max_chars = max_chars or self.config.preview_chars

        lines = text.split("\n")
        full_length = len(text)

        # Check if truncation needed
        if len(lines) <= max_lines and len(text) <= max_chars:
            return TruncatedContent(
                content=text,
                is_truncated=False,
                full_length=full_length,
                preview_length=full_length,
                content_type="text",
            )

        # Truncate by lines first, then by chars
        preview_lines = lines[:max_lines]
        preview = "\n".join(preview_lines)

        if len(preview) > max_chars:
            preview = preview[:max_chars]
            # Try to break at paragraph/sentence boundary
            last_para = preview.rfind("\n\n")
            last_sentence = max(preview.rfind(". "), preview.rfind(".\n"))

            if last_para > max_chars * 0.6:
                preview = preview[:last_para]
            elif last_sentence > max_chars * 0.6:
                preview = preview[: last_sentence + 1]

        return TruncatedContent(
            content=preview,
            is_truncated=True,
            full_length=full_length,
            preview_length=len(preview),
            content_type="text",
            expand_hint="Use /expand to see full response",
        )

    def truncate_code(self, code: str, language: str = "text") -> TruncatedContent:
        """
        Truncate code blocks, preserving function/class boundaries when possible.

        Args:
            code: Source code
            language: Programming language

        Returns:
            TruncatedContent with preview
        """
        lines = code.split("\n")
        full_lines = len(lines)

        if full_lines <= self.config.code_preview_lines:
            return TruncatedContent(
                content=code,
                is_truncated=False,
                full_length=full_lines,
                preview_length=full_lines,
                content_type="code",
            )

        # Take preview lines
        preview_lines = lines[: self.config.code_preview_lines]

        # Try to end at a logical boundary (empty line, closing brace)
        for i in range(len(preview_lines) - 1, max(10, len(preview_lines) - 10), -1):
            line = preview_lines[i].strip()
            if line == "" or line in ["}", "]", ")", "end", "fi", "done"]:
                preview_lines = preview_lines[: i + 1]
                break

        preview = "\n".join(preview_lines)
        hidden_lines = full_lines - len(preview_lines)

        return TruncatedContent(
            content=preview,
            is_truncated=True,
            full_length=full_lines,
            preview_length=len(preview_lines),
            content_type="code",
            expand_hint=f"# ... {hidden_lines} more lines",
        )

    def truncate_table_data(
        self, headers: List[str], rows: List[List[str]], max_rows: int = None, max_cols: int = None
    ) -> Tuple[List[str], List[List[str]], bool, str]:
        """
        Truncate table data for display.

        Returns:
            (truncated_headers, truncated_rows, is_truncated, info_message)
        """
        max_rows_limit = max_rows or self.config.max_table_rows
        max_cols_limit = max_cols or self.config.max_table_cols

        truncated_cols = False
        truncated_rows_flag = False
        info_parts: List[str] = []

        result_headers = list(headers)
        result_rows = [list(row) for row in rows]

        # Truncate columns
        if len(result_headers) > max_cols_limit:
            result_headers = result_headers[:max_cols_limit] + [
                f"...+{len(headers) - max_cols_limit}"
            ]
            result_rows = [row[:max_cols_limit] + ["..."] for row in result_rows]
            truncated_cols = True
            info_parts.append(f"{len(headers) - max_cols_limit} cols hidden")

        # Truncate rows
        if len(result_rows) > max_rows_limit:
            hidden_count = len(result_rows) - max_rows_limit
            result_rows = result_rows[:max_rows_limit]
            truncated_rows_flag = True
            info_parts.append(f"{hidden_count} rows hidden")

        # Truncate cell content
        max_width = self.config.max_cell_width
        for i, row in enumerate(result_rows):
            result_rows[i] = [
                (str(cell)[: max_width - 3] + "..." if len(str(cell)) > max_width else str(cell))
                for cell in row
            ]

        is_truncated = truncated_cols or truncated_rows_flag
        info = " | ".join(info_parts) if info_parts else ""

        return result_headers, result_rows, is_truncated, info

    def truncate_tool_output(self, output: str, tool_name: str = "") -> TruncatedContent:
        """
        Truncate tool execution output.

        Args:
            output: Tool output string
            tool_name: Name of the tool for context

        Returns:
            TruncatedContent with preview
        """
        max_chars = self.config.max_tool_output
        full_length = len(output)

        if full_length <= max_chars:
            return TruncatedContent(
                content=output,
                is_truncated=False,
                full_length=full_length,
                preview_length=full_length,
                content_type="tool_output",
            )

        # For tool output, try to end at a line boundary
        preview = output[:max_chars]
        last_newline = preview.rfind("\n")
        if last_newline > max_chars * 0.7:
            preview = preview[:last_newline]

        return TruncatedContent(
            content=preview,
            is_truncated=True,
            full_length=full_length,
            preview_length=len(preview),
            content_type="tool_output",
            expand_hint=f"... {full_length - len(preview)} more chars",
        )


# Global truncator instance
TRUNCATOR = SmartTruncator()
