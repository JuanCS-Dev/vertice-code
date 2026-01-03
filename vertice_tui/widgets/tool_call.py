"""
Tool Call Visualization - VERTICE TUI Visual Upgrade.

Displays tool/function calls with status and expandable details.
Inspired by Claude Code's spinner animations and status indicators.

Phase 11: Visual Upgrade Sprint 1.

References:
- https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
- Spinner rendering and status visibility improvements
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import Static, Collapsible
from textual.widget import Widget


class ToolStatus(Enum):
    """Tool call status."""
    PENDING = ("pending", "○", "#64748B")  # Gray
    RUNNING = ("running", "◐", "#3B82F6")  # Blue (animated)
    SUCCESS = ("success", "✓", "#22C55E")  # Green
    ERROR = ("error", "✗", "#EF4444")  # Red
    CANCELLED = ("cancelled", "⊘", "#F59E0B")  # Amber

    def __init__(self, status_name: str, icon: str, color: str):
        self.status_name = status_name
        self.icon = icon
        self.color = color


@dataclass
class ToolCallData:
    """Data for a tool call."""
    name: str
    status: ToolStatus = ToolStatus.PENDING
    input_data: Optional[str] = None
    output_data: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    id: str = field(default_factory=lambda: f"tool-{datetime.now().timestamp()}")


class ToolCallWidget(Widget):
    """
    Widget displaying a single tool call with status.

    Features:
    - Animated spinner during execution
    - Color-coded status (pending/running/success/error)
    - Expandable details showing input/output
    - Elapsed time display

    Usage:
        tool = ToolCallWidget(ToolCallData(name="read_file", input_data="/path/to/file"))
        tool.start()
        # ... tool executes ...
        tool.complete(output_data="file contents")
    """

    SPINNER_FRAMES = ["◐", "◓", "◑", "◒"]

    DEFAULT_CSS = """
    ToolCallWidget {
        width: 100%;
        height: auto;
        margin: 0 0 1 0;
        background: $surface;
        border-left: thick $border;
        padding: 0 1;
    }

    ToolCallWidget.pending {
        border-left: thick #64748B;
    }

    ToolCallWidget.running {
        border-left: thick #3B82F6;
    }

    ToolCallWidget.success {
        border-left: thick #22C55E;
    }

    ToolCallWidget.error {
        border-left: thick #EF4444;
    }

    ToolCallWidget .tool-header {
        height: 1;
    }

    ToolCallWidget .tool-name {
        text-style: bold;
    }

    ToolCallWidget .tool-time {
        color: $text-muted;
        text-align: right;
    }

    ToolCallWidget Collapsible {
        padding-left: 2;
    }

    ToolCallWidget .tool-input {
        color: #94A3B8;
    }

    ToolCallWidget .tool-output {
        color: #E2E8F0;
    }

    ToolCallWidget .tool-error {
        color: #EF4444;
    }
    """

    status: reactive[ToolStatus] = reactive(ToolStatus.PENDING)

    def __init__(self, data: ToolCallData, **kwargs) -> None:
        super().__init__(classes=data.status.status_name, **kwargs)
        self.data = data
        self._spinner_frame = 0
        self._spinner_timer: Optional[Timer] = None

    def compose(self) -> ComposeResult:
        yield Static(self._format_header(), classes="tool-header", id="header")
        with Collapsible(title="Details", collapsed=True, id="details"):
            if self.data.input_data:
                yield Static(f"Input: {self.data.input_data}", classes="tool-input")
            if self.data.output_data:
                yield Static(f"Output: {self.data.output_data}", classes="tool-output")
            if self.data.error_message:
                yield Static(f"Error: {self.data.error_message}", classes="tool-error")

    def _format_header(self) -> str:
        """Format tool call header."""
        icon = self.data.status.icon
        color = self.data.status.color

        if self.data.status == ToolStatus.RUNNING:
            icon = self.SPINNER_FRAMES[self._spinner_frame]

        time_str = ""
        if self.data.started_at:
            if self.data.ended_at:
                elapsed = (self.data.ended_at - self.data.started_at).total_seconds()
                time_str = f" ({elapsed:.2f}s)"
            else:
                elapsed = (datetime.now() - self.data.started_at).total_seconds()
                time_str = f" ({elapsed:.1f}s...)"

        return f"[{color}]{icon}[/] [bold]{self.data.name}[/][dim]{time_str}[/]"

    def start(self) -> None:
        """Start tool execution - show running spinner."""
        self.data.status = ToolStatus.RUNNING
        self.data.started_at = datetime.now()
        self.status = ToolStatus.RUNNING
        self._update_classes()

        # Start spinner animation
        self._spinner_timer = self.set_interval(0.1, self._animate_spinner)

    def complete(self, output_data: Optional[str] = None) -> None:
        """Complete tool execution successfully."""
        self.data.status = ToolStatus.SUCCESS
        self.data.output_data = output_data
        self.data.ended_at = datetime.now()
        self.status = ToolStatus.SUCCESS
        self._stop_spinner()
        self._update_display()

    def fail(self, error_message: str) -> None:
        """Mark tool as failed."""
        self.data.status = ToolStatus.ERROR
        self.data.error_message = error_message
        self.data.ended_at = datetime.now()
        self.status = ToolStatus.ERROR
        self._stop_spinner()
        self._update_display()

    def cancel(self) -> None:
        """Cancel tool execution."""
        self.data.status = ToolStatus.CANCELLED
        self.data.ended_at = datetime.now()
        self.status = ToolStatus.CANCELLED
        self._stop_spinner()
        self._update_display()

    def _animate_spinner(self) -> None:
        """Animate the spinner."""
        self._spinner_frame = (self._spinner_frame + 1) % len(self.SPINNER_FRAMES)
        self._update_display()

    def _stop_spinner(self) -> None:
        """Stop spinner animation."""
        if self._spinner_timer:
            self._spinner_timer.stop()
            self._spinner_timer = None

    def _update_classes(self) -> None:
        """Update CSS classes based on status."""
        for status in ToolStatus:
            self.remove_class(status.status_name)
        self.add_class(self.data.status.status_name)

    def _update_display(self) -> None:
        """Update the display."""
        self._update_classes()
        try:
            self.query_one("#header", Static).update(self._format_header())
        except Exception:
            pass


class ToolCallStack(Vertical):
    """
    Container for stacking multiple tool calls.

    Shows a timeline of tool executions.
    """

    DEFAULT_CSS = """
    ToolCallStack {
        width: 100%;
        height: auto;
        padding: 1;
    }

    ToolCallStack .stack-header {
        height: 1;
        color: $text-muted;
        margin-bottom: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._tools: List[ToolCallWidget] = []

    def compose(self) -> ComposeResult:
        yield Static("Tool Calls", classes="stack-header")

    def add_tool(self, data: ToolCallData) -> ToolCallWidget:
        """Add a new tool call to the stack."""
        widget = ToolCallWidget(data)
        self._tools.append(widget)
        self.mount(widget)
        return widget

    def clear(self) -> None:
        """Clear all tool calls."""
        for tool in self._tools:
            tool.remove()
        self._tools.clear()

    @property
    def running_count(self) -> int:
        """Count of currently running tools."""
        return sum(1 for t in self._tools if t.data.status == ToolStatus.RUNNING)

    @property
    def success_count(self) -> int:
        """Count of successful tools."""
        return sum(1 for t in self._tools if t.data.status == ToolStatus.SUCCESS)

    @property
    def error_count(self) -> int:
        """Count of failed tools."""
        return sum(1 for t in self._tools if t.data.status == ToolStatus.ERROR)


__all__ = [
    "ToolStatus",
    "ToolCallData",
    "ToolCallWidget",
    "ToolCallStack",
]
