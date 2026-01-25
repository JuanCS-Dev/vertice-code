"""
MAESTRO v10.0 - Command Palette Bar Component

Bottom command bar with suggestion chips and quick actions.
"""

from typing import List, Tuple
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.console import Group
from rich.padding import Padding
from rich.style import Style
from rich.box import ROUNDED

from ..theme import COLORS


class CommandPaletteBar:
    """
    Bottom command palette with suggestion chips.

    Features:
    - Quick action buttons
    - Context-aware suggestions
    - Visual command indicators
    """

    def __init__(self):
        """Initialize command palette"""
        self.commands = [
            ("🚀 Execute", COLORS["neon_green"], "/execute"),
            ("🎯 Plan", COLORS["neon_purple"], "/plan"),
            ("📊 Metrics", COLORS["neon_cyan"], "/metrics"),
            ("❓ Help", COLORS["text_secondary"], "/help"),
        ]
        self.current_input = ""

    def set_input(self, text: str):
        """
        Set current input text for context awareness.

        Args:
            text: Current input text
        """
        self.current_input = text

    def add_command(self, label: str, color: str, command: str):
        """
        Add custom command to palette.

        Args:
            label: Display label with emoji
            color: Hex color for button
            command: Command string (e.g., "/custom")
        """
        self.commands.append((label, color, command))

    def render(self, show_input_hint: bool = True) -> Panel:
        """
        Render command palette bar.

        Args:
            show_input_hint: Whether to show input hint

        Returns:
            Rich Panel ready for rendering
        """
        # Build command buttons
        command_items = []
        for label, color, _ in self.commands:
            cmd_text = Text(f" {label} ", style=f"bold black on {color}")
            command_items.append(cmd_text)

        commands_row = Columns(command_items, padding=(0, 1), expand=False)

        # Build input hint
        if show_input_hint:
            input_hint = self._build_input_hint()
            content = Group(commands_row, Padding(input_hint, (1, 0, 0, 0)))
        else:
            content = commands_row

        return Panel(
            content,
            border_style=COLORS["border_muted"],
            box=ROUNDED,
            padding=(0, 2),
            style=Style(bgcolor=COLORS["bg_elevated"]),
        )

    def _build_input_hint(self) -> Text:
        """
        Build input hint based on current context.

        Returns:
            Formatted Text object
        """
        hint = Text()

        if not self.current_input:
            # Default hint
            hint.append("Type your request or use ", style=COLORS["text_secondary"])
            hint.append("/", style=f"bold {COLORS['accent_blue']}")
            hint.append(" for commands", style=COLORS["text_secondary"])
        elif self.current_input.startswith("/"):
            # Slash command hint
            hint.append("Slash command mode ", style=COLORS["accent_blue"])
            hint.append("• Press ", style=COLORS["text_secondary"])
            hint.append("Tab", style=f"bold {COLORS['accent_blue']}")
            hint.append(" for autocomplete", style=COLORS["text_secondary"])
        else:
            # Natural language hint
            hint.append("Natural language request ", style=COLORS["accent_green"])
            hint.append("• Press ", style=COLORS["text_secondary"])
            hint.append("Enter", style=f"bold {COLORS['accent_green']}")
            hint.append(" to execute", style=COLORS["text_secondary"])

        return hint

    def get_command_suggestions(self, partial: str) -> List[Tuple[str, str, str]]:
        """
        Get command suggestions matching partial input.

        Args:
            partial: Partial command string (e.g., "/me")

        Returns:
            List of matching (label, color, command) tuples
        """
        if not partial.startswith("/"):
            return []

        matches = []
        for label, color, command in self.commands:
            if command.lower().startswith(partial.lower()):
                matches.append((label, color, command))

        return matches


class MinimalCommandBar:
    """
    Minimal command bar without buttons (for compact mode).
    """

    def __init__(self):
        """Initialize minimal bar"""
        self.hint_text = "Type your request..."

    def set_hint(self, text: str):
        """Set hint text"""
        self.hint_text = text

    def render(self) -> Panel:
        """
        Render minimal bar.

        Returns:
            Rich Panel ready for rendering
        """
        hint = Text(self.hint_text, style=COLORS["text_secondary"])

        return Panel(
            hint,
            border_style=COLORS["border_muted"],
            box=ROUNDED,
            padding=(0, 2),
            style=Style(bgcolor=COLORS["bg_elevated"]),
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def create_default_palette() -> CommandPaletteBar:
    """
    Create command palette with default commands.

    Returns:
        Configured CommandPaletteBar
    """
    return CommandPaletteBar()


def create_executor_palette() -> CommandPaletteBar:
    """
    Create command palette optimized for executor context.

    Returns:
        CommandPaletteBar with executor commands
    """
    palette = CommandPaletteBar()
    palette.commands = [
        ("⚡ Execute", COLORS["neon_cyan"], "/execute"),
        ("🛡️ Security", COLORS["neon_yellow"], "/security"),
        ("📜 History", COLORS["text_secondary"], "/history"),
        ("⚙️ Config", COLORS["text_secondary"], "/config"),
    ]
    return palette


def create_planner_palette() -> CommandPaletteBar:
    """
    Create command palette optimized for planner context.

    Returns:
        CommandPaletteBar with planner commands
    """
    palette = CommandPaletteBar()
    palette.commands = [
        ("🎯 Plan", COLORS["neon_purple"], "/plan"),
        ("🔍 Analyze", COLORS["neon_blue"], "/analyze"),
        ("📊 Breakdown", COLORS["neon_cyan"], "/breakdown"),
        ("❓ Help", COLORS["text_secondary"], "/help"),
    ]
    return palette
