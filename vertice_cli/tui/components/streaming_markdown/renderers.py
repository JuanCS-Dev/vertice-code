"""
Streaming Markdown Renderers - Specialized Block Rendering.

This module provides rendering functions for specialized markdown blocks:
- Tool call rendering (Claude Code Web and Gemini Native styles)
- Status badge rendering
- Diff block rendering
- Heading rendering

Philosophy:
    "Each block type deserves specialized treatment."
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from rich.text import Text
from rich.syntax import Syntax
from rich.panel import Panel
from rich.console import RenderableType

if TYPE_CHECKING:
    from ..block_detector import BlockInfo


# Tool icons for Claude Code style
TOOL_ICONS = {
    "Read": ("📖", "bright_cyan"),
    "Write": ("✏️", "bright_green"),
    "Edit": ("📝", "bright_yellow"),
    "Bash": ("💻", "bright_magenta"),
    "Glob": ("🔍", "bright_blue"),
    "Grep": ("🔎", "bright_blue"),
    "Task": ("📋", "bright_white"),
    "WebFetch": ("🌐", "bright_cyan"),
    "WebSearch": ("🔍", "bright_cyan"),
    "Update Todos": ("✅", "bright_green"),
    "TodoWrite": ("✅", "bright_green"),
    "AskUserQuestion": ("❓", "bright_yellow"),
}

# Tool icons for Gemini Native format
GEMINI_TOOL_ICONS = {
    "code_execution": ("🐍", "bright_green"),
    "google_search_retrieval": ("🔍", "bright_blue"),
}

# Status badge styles
STATUS_BADGE_STYLES = {
    "🔴": ("bold red", "background: red"),
    "🟠": ("bold bright_red", "background: orange"),
    "🟡": ("bold yellow", "background: yellow"),
    "🟢": ("bold green", "background: green"),
    "⚪": ("dim white", "background: white"),
    "✅": ("bold bright_green", "background: green"),
    "❌": ("bold bright_red", "background: red"),
    "⚠️": ("bold bright_yellow", "background: yellow"),
}

# Heading styles by level - Theme-adaptive color hierarchy
# Using Rich semantic colors that work in both light and dark themes
HEADING_STYLES = {
    1: "bold bright_blue",  # Primary heading - bright for contrast
    2: "bold bright_cyan",  # Accent heading - cyan stands out
    3: "bold",  # Standard bold - uses theme foreground
    4: "bold dim",  # Muted heading
    5: "dim",  # More muted
    6: "italic dim",  # Least prominent
}


def render_heading(block: "BlockInfo") -> RenderableType:
    """
    Render heading with styled formatting.

    Clean, modern style without showing # symbols.
    Uses theme-adaptive colors for light/dark compatibility.

    Args:
        block: Block info with heading content

    Returns:
        Rich Text renderable
    """
    level = block.metadata.get("level", 1)
    text_content = block.metadata.get("text", block.content)

    style = HEADING_STYLES.get(level, "bold")

    text = Text()

    # H1 gets a special treatment with underline effect
    if level == 1:
        text.append(text_content, style=style)
        text.append("\n")
        text.append("─" * min(len(text_content), 50), style="dim")  # Theme-adaptive
    # H2 gets a subtle prefix
    elif level == 2:
        text.append("▸ ", style="dim")  # Theme-adaptive chevron
        text.append(text_content, style=style)
    else:
        # H3+ just styled text
        text.append(text_content, style=style)

    return text


def render_status_badge(block: "BlockInfo") -> RenderableType:
    """
    Render status badge Claude Code style.

    Formats: 🔴 BLOCKER, 🟡 WARNING, 🟢 OK, ✅ SUCCESS, ❌ ERROR

    Args:
        block: Block info with status content

    Returns:
        Rich Text renderable
    """
    text = Text()
    content = block.content.strip()

    for emoji, (style, _bg) in STATUS_BADGE_STYLES.items():
        if content.startswith(emoji):
            status_text = content[len(emoji) :].strip()
            text.append(f"{emoji} ", style="bold")
            text.append(status_text, style=style)
            return text

    # Fallback
    text.append(content, style="white")
    return text


def render_diff(block: "BlockInfo") -> RenderableType:
    """
    Render diff block GitHub style.

    Uses syntax highlighting for diff format.

    Args:
        block: Block info with diff content

    Returns:
        Rich renderable (Syntax or Panel)
    """
    try:
        return Syntax(
            block.content,
            "diff",
            theme="monokai",
            line_numbers=True,
            word_wrap=True,
        )
    except (ValueError, TypeError):
        # Fallback: manual colorization
        text = Text()
        for line in block.content.split("\n"):
            if line.startswith("+"):
                text.append(line + "\n", style="green")
            elif line.startswith("-"):
                text.append(line + "\n", style="red")
            elif line.startswith("@@"):
                text.append(line + "\n", style="cyan")
            else:
                text.append(line + "\n", style="dim")
        return Panel(text, title="Diff", border_style="dim")


def render_tool_call(block: "BlockInfo") -> RenderableType:
    """
    Render tool call Claude Code Web or Gemini Native style.

    Gemini Format: [TOOL_CALL:name:{args}]
    Claude Format: • Read /path/to/file

    Args:
        block: Block info with tool call content

    Returns:
        Rich Text renderable
    """
    content = block.content.strip()

    # Gemini Native Format
    if content.startswith("[TOOL_CALL:"):
        return _render_gemini_tool_call(content)

    # Claude Code Format
    return _render_claude_tool_call(content)


def _render_gemini_tool_call(content: str) -> RenderableType:
    """Render Gemini native tool call format."""
    try:
        # [TOOL_CALL:name:{...}]
        inner = content[11:]
        if inner.endswith("]"):
            inner = inner[:-1]

        if ":" in inner:
            tool_name, args = inner.split(":", 1)
        else:
            tool_name = inner
            args = "{}"

        icon, color = GEMINI_TOOL_ICONS.get(tool_name, ("🛠️", "bright_cyan"))

        result = Text()
        result.append(f"{icon} ", style="bold")
        result.append(tool_name, style=f"bold {color}")
        result.append(" ", style="dim")
        result.append(args, style="italic #888888")
        return result
    except (ValueError, IndexError, KeyError):
        return Text(content)


def _render_claude_tool_call(content: str) -> RenderableType:
    """Render Claude Code style tool call."""
    lines = content.split("\n")
    if not lines:
        return Text(content)

    # Parse first line (tool call)
    first_line = lines[0].strip()
    # Remove ** bold markers if present
    first_line = re.sub(r"\*\*", "", first_line)

    match = re.match(r"^[•●]\s*(\w+(?:\s+\w+)?)\s*(.*)", first_line)
    if not match:
        return Text(content)

    tool_name = match.group(1).strip()
    args = match.group(2).strip()

    icon, color = TOOL_ICONS.get(tool_name, ("•", "white"))

    # Build output
    result = Text()
    result.append(f"{icon} ", style="bold")
    result.append(tool_name, style=f"bold {color}")
    if args:
        # Remove backticks for paths
        args_clean = args.strip("`")
        result.append(" ", style="dim")
        result.append(args_clean, style="italic #888888")
    result.append("\n")

    # Render output lines
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue

        _append_tool_output_line(result, line, stripped)

    # Remove trailing newline
    if result.plain.endswith("\n"):
        result = _apply_tool_styles(content, tool_name, icon, color)

    return result


def _append_tool_output_line(result: Text, line: str, stripped: str) -> None:
    """Append a tool output line with proper styling."""
    # Tool output line (└ resultado)
    if stripped.startswith("└") or stripped.startswith("├"):
        output_text = stripped[1:].strip()
        result.append("  └ ", style="dim #666666")

        # Check for strikethrough (~~text~~)
        if "~~" in output_text:
            _append_strikethrough_text(result, output_text)
        # Check for checkbox
        elif stripped.startswith("└ ☐") or stripped.startswith("└ □"):
            checkbox_text = output_text.lstrip("☐□ ")
            result.append("☐ ", style="bold bright_yellow")
            result.append(checkbox_text, style="bright_white")
        else:
            result.append(output_text, style="dim #aaaaaa")
        result.append("\n")

    # Indented continuation
    elif line.startswith("  "):
        result.append("  ", style="")
        if "~~" in stripped:
            _append_strikethrough_text(result, stripped)
        elif stripped.startswith("☐") or stripped.startswith("□"):
            checkbox_text = stripped.lstrip("☐□ ")
            result.append("☐ ", style="bold bright_yellow")
            result.append(checkbox_text, style="bright_white")
        else:
            result.append(stripped, style="dim #aaaaaa")
        result.append("\n")


def _append_strikethrough_text(result: Text, text: str) -> None:
    """Append text with strikethrough portions styled."""
    parts = re.split(r"(~~[^~]+~~)", text)
    for part in parts:
        if part.startswith("~~") and part.endswith("~~"):
            result.append(part[2:-2], style="strike dim #888888")
        else:
            result.append(part, style="dim #aaaaaa")


def _apply_tool_styles(content: str, tool_name: str, icon: str, color: str) -> Text:
    """Apply consistent styling to tool output."""
    lines = content.strip().split("\n")
    result = Text()

    # First line
    first_line = re.sub(r"\*\*", "", lines[0].strip())
    match = re.match(r"^[•●]\s*(\w+(?:\s+\w+)?)\s*(.*)", first_line)
    if match:
        args = match.group(2).strip().strip("`")
        result.append(f"{icon} ", style="bold")
        result.append(tool_name, style=f"bold {color}")
        if args:
            result.append(" ", style="dim")
            result.append(args, style="italic #888888")

    # Output lines
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        result.append("\n")

        if stripped.startswith("└") or stripped.startswith("├"):
            output_text = stripped[1:].strip()
            result.append("  └ ", style="dim #666666")
            if "~~" in output_text:
                _append_strikethrough_text(result, output_text)
            elif output_text.startswith("☐") or output_text.startswith("□"):
                checkbox_text = output_text.lstrip("☐□ ")
                result.append("☐ ", style="bold bright_yellow")
                result.append(checkbox_text, style="bright_white")
            else:
                result.append(output_text, style="dim #aaaaaa")
        elif line.startswith("  "):
            result.append("  ", style="")
            if "~~" in stripped:
                _append_strikethrough_text(result, stripped)
            elif stripped.startswith("☐") or stripped.startswith("□"):
                checkbox_text = stripped.lstrip("☐□ ")
                result.append("☐ ", style="bold bright_yellow")
                result.append(checkbox_text, style="bright_white")
            else:
                result.append(stripped, style="dim #aaaaaa")

    return result


__all__ = [
    "render_heading",
    "render_status_badge",
    "render_diff",
    "render_tool_call",
    "TOOL_ICONS",
    "HEADING_STYLES",
    "STATUS_BADGE_STYLES",
]
