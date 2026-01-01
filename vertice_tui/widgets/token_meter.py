"""
TokenDashboard - Real-time Token Usage Widget.

Visual dashboard for context usage monitoring:
- Progress bar with color-coded thresholds
- Breakdown by category (messages, files, summary)
- Compression ratio display
- Auto-compact indicator

References:
- Claude Code /context command
- Cursor token meter
- Gemini 3 thinking level indicator

Phase 10: Sprint 4 - Context Optimization

Soli Deo Gloria
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive
from textual.widgets import Static


@dataclass
class TokenBreakdown:
    """Breakdown of token usage by category."""

    messages: int = 0
    files: int = 0
    summary: int = 0
    system: int = 0
    tools: int = 0

    @property
    def total(self) -> int:
        return self.messages + self.files + self.summary + self.system + self.tools

    def to_dict(self) -> Dict[str, int]:
        return {
            "messages": self.messages,
            "files": self.files,
            "summary": self.summary,
            "system": self.system,
            "tools": self.tools,
            "total": self.total,
        }


class TokenMeter(Static):
    """
    Compact token usage meter with progress bar.

    Shows: [====----] 8.5k/32k (27%)

    Color coding:
    - Green: < 60%
    - Yellow: 60-85%
    - Orange: 85-95%
    - Red: > 95%
    """

    DEFAULT_CSS = """
    TokenMeter {
        height: 1;
        padding: 0;
    }
    """

    used: reactive[int] = reactive(0)
    limit: reactive[int] = reactive(32000)

    def render(self) -> str:
        """Render the token meter."""
        if self.limit == 0:
            return "[dim]No limit[/dim]"

        ratio = self.used / self.limit
        percent = ratio * 100

        # Color based on usage
        if ratio >= 0.95:
            color = "#EF4444"  # Red
            bar_char = "█"
        elif ratio >= 0.85:
            color = "#F97316"  # Orange
            bar_char = "▓"
        elif ratio >= 0.60:
            color = "#F59E0B"  # Yellow
            bar_char = "▒"
        else:
            color = "#22C55E"  # Green
            bar_char = "░"

        # Build progress bar (10 chars wide)
        filled = int(ratio * 10)
        empty = 10 - filled
        bar = f"[{color}]{bar_char * filled}[/{color}][dim]{'─' * empty}[/dim]"

        # Format numbers
        used_str = self._format_tokens(self.used)
        limit_str = self._format_tokens(self.limit)

        return f"\\[{bar}] [{color}]{used_str}/{limit_str}[/{color}] ({percent:.0f}%)"

    @staticmethod
    def _format_tokens(n: int) -> str:
        """Format token count with K/M suffix."""
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n/1_000:.1f}k"
        return str(n)


class TokenBreakdownWidget(Vertical):
    """
    Detailed token breakdown by category.

    Shows:
    Messages: 4.2k (49%)
    Files:    2.1k (25%)
    Summary:  1.5k (18%)
    System:   0.7k (8%)
    """

    DEFAULT_CSS = """
    TokenBreakdownWidget {
        height: auto;
        padding: 0 1;
    }

    TokenBreakdownWidget .category {
        height: 1;
    }

    TokenBreakdownWidget .category-name {
        width: 10;
        color: $foreground-muted;
    }

    TokenBreakdownWidget .category-bar {
        width: 15;
    }

    TokenBreakdownWidget .category-value {
        width: 10;
        text-align: right;
    }
    """

    breakdown: reactive[TokenBreakdown] = reactive(TokenBreakdown)

    def compose(self) -> ComposeResult:
        """Compose breakdown display."""
        yield Horizontal(
            Static("Messages:", classes="category-name"),
            Static("", id="msg-bar", classes="category-bar"),
            Static("0", id="msg-value", classes="category-value"),
            classes="category",
        )
        yield Horizontal(
            Static("Files:", classes="category-name"),
            Static("", id="file-bar", classes="category-bar"),
            Static("0", id="file-value", classes="category-value"),
            classes="category",
        )
        yield Horizontal(
            Static("Summary:", classes="category-name"),
            Static("", id="sum-bar", classes="category-bar"),
            Static("0", id="sum-value", classes="category-value"),
            classes="category",
        )
        yield Horizontal(
            Static("System:", classes="category-name"),
            Static("", id="sys-bar", classes="category-bar"),
            Static("0", id="sys-value", classes="category-value"),
            classes="category",
        )

    def watch_breakdown(self, value: TokenBreakdown) -> None:
        """Update display when breakdown changes."""
        total = value.total if value.total > 0 else 1

        categories = [
            ("msg", value.messages, "#3B82F6"),  # Blue
            ("file", value.files, "#8B5CF6"),  # Purple
            ("sum", value.summary, "#10B981"),  # Emerald
            ("sys", value.system, "#6B7280"),  # Gray
        ]

        for prefix, tokens, color in categories:
            ratio = tokens / total
            bar_width = int(ratio * 10)
            bar = f"[{color}]{'█' * bar_width}[/{color}]{'░' * (10 - bar_width)}"

            try:
                self.query_one(f"#{prefix}-bar", Static).update(bar)
                self.query_one(f"#{prefix}-value", Static).update(
                    f"{self._format_tokens(tokens)} ({ratio*100:.0f}%)"
                )
            except Exception:
                pass

    @staticmethod
    def _format_tokens(n: int) -> str:
        if n >= 1_000:
            return f"{n/1_000:.1f}k"
        return str(n)


class CompressionIndicator(Static):
    """
    Shows compression status and ratio.

    Displays: ◐ 3.2x compressed | Auto-compact: 85%
    """

    DEFAULT_CSS = """
    CompressionIndicator {
        height: 1;
        padding: 0;
    }
    """

    compression_ratio: reactive[float] = reactive(1.0)
    auto_compact_threshold: reactive[float] = reactive(0.85)
    is_compacting: reactive[bool] = reactive(False)
    compressions_count: reactive[int] = reactive(0)

    def render(self) -> str:
        """Render compression indicator."""
        parts = []

        # Compression status
        if self.is_compacting:
            parts.append("[#F59E0B]◐ Compacting...[/#F59E0B]")
        elif self.compression_ratio > 1.0:
            parts.append(f"[#22C55E]◆ {self.compression_ratio:.1f}x compressed[/#22C55E]")
        else:
            parts.append("[dim]○ No compression[/dim]")

        # Auto-compact threshold
        threshold_pct = int(self.auto_compact_threshold * 100)
        parts.append(f"[dim]Auto: {threshold_pct}%[/dim]")

        # Compressions count
        if self.compressions_count > 0:
            parts.append(f"[dim]({self.compressions_count}x)[/dim]")

        return " | ".join(parts)


class ThinkingLevelIndicator(Static):
    """
    Shows current thinking level (Gemini 3 style).

    Displays: ◇◇◆◇ Medium
    """

    DEFAULT_CSS = """
    ThinkingLevelIndicator {
        height: 1;
        padding: 0;
    }
    """

    level: reactive[str] = reactive("medium")

    LEVELS = ["minimal", "low", "medium", "high"]
    COLORS = {
        "minimal": "#6B7280",  # Gray
        "low": "#22C55E",  # Green
        "medium": "#3B82F6",  # Blue
        "high": "#8B5CF6",  # Purple
    }

    def render(self) -> str:
        """Render thinking level indicator."""
        level_idx = self.LEVELS.index(self.level) if self.level in self.LEVELS else 2
        color = self.COLORS.get(self.level, "#3B82F6")

        # Build indicator diamonds
        diamonds = ""
        for i, lvl in enumerate(self.LEVELS):
            if i == level_idx:
                diamonds += f"[{color}]◆[/{color}]"
            else:
                diamonds += "[dim]◇[/dim]"

        return f"{diamonds} [{color}]{self.level.capitalize()}[/{color}]"


class TokenDashboard(Vertical):
    """
    Complete token usage dashboard.

    Combines all metrics into a collapsible panel:
    - Token meter with progress
    - Category breakdown
    - Compression status
    - Thinking level

    Usage:
        dashboard = TokenDashboard()
        dashboard.update_usage(used=8500, limit=32000)
        dashboard.update_breakdown(messages=4200, files=2100, ...)
    """

    DEFAULT_CSS = """
    TokenDashboard {
        height: auto;
        max-height: 10;
        padding: 0 1;
        background: $surface;
    }

    TokenDashboard.collapsed {
        height: 1;
        overflow: hidden;
    }

    TokenDashboard .header {
        height: 1;
        margin-bottom: 1;
    }

    TokenDashboard .header-title {
        width: auto;
        text-style: bold;
        color: $accent;
    }

    TokenDashboard .header-toggle {
        width: auto;
        dock: right;
        color: $foreground-muted;
    }

    TokenDashboard .section {
        margin-top: 1;
    }

    TokenDashboard .section-title {
        color: $foreground-muted;
        text-style: italic;
    }
    """

    # State
    collapsed: reactive[bool] = reactive(False)
    used_tokens: reactive[int] = reactive(0)
    max_tokens: reactive[int] = reactive(32000)

    def __init__(
        self,
        title: str = "Context Usage",
        **kwargs: Any,
    ) -> None:
        """Initialize token dashboard."""
        super().__init__(**kwargs)
        self.border_title = title
        self._breakdown = TokenBreakdown()
        self._compression_ratio = 1.0
        self._thinking_level = "medium"

    def compose(self) -> ComposeResult:
        """Compose dashboard widgets."""
        # Main meter
        yield TokenMeter(id="meter")

        # Breakdown (shown when expanded)
        yield Static("Breakdown", classes="section-title")
        yield TokenBreakdownWidget(id="breakdown")

        # Compression & Thinking
        yield Static("Status", classes="section-title")
        yield Horizontal(
            CompressionIndicator(id="compression"),
            Static(" | "),
            ThinkingLevelIndicator(id="thinking"),
        )

    def update_usage(
        self,
        used: int,
        limit: Optional[int] = None,
    ) -> None:
        """Update token usage display."""
        self.used_tokens = used
        if limit is not None:
            self.max_tokens = limit

        try:
            meter = self.query_one("#meter", TokenMeter)
            meter.used = used
            if limit is not None:
                meter.limit = limit
        except Exception:
            pass

    def update_breakdown(
        self,
        messages: int = 0,
        files: int = 0,
        summary: int = 0,
        system: int = 0,
        tools: int = 0,
    ) -> None:
        """Update token breakdown by category."""
        self._breakdown = TokenBreakdown(
            messages=messages,
            files=files,
            summary=summary,
            system=system,
            tools=tools,
        )

        try:
            widget = self.query_one("#breakdown", TokenBreakdownWidget)
            widget.breakdown = self._breakdown
        except Exception:
            pass

    def update_compression(
        self,
        ratio: float,
        is_compacting: bool = False,
        count: int = 0,
    ) -> None:
        """Update compression status."""
        self._compression_ratio = ratio

        try:
            indicator = self.query_one("#compression", CompressionIndicator)
            indicator.compression_ratio = ratio
            indicator.is_compacting = is_compacting
            indicator.compressions_count = count
        except Exception:
            pass

    def update_thinking_level(self, level: str) -> None:
        """Update thinking level indicator."""
        self._thinking_level = level

        try:
            indicator = self.query_one("#thinking", ThinkingLevelIndicator)
            indicator.level = level
        except Exception:
            pass

    def toggle_collapsed(self) -> None:
        """Toggle collapsed state."""
        self.collapsed = not self.collapsed
        if self.collapsed:
            self.add_class("collapsed")
        else:
            self.remove_class("collapsed")

    def get_stats(self) -> Dict[str, Any]:
        """Get current dashboard stats."""
        return {
            "used_tokens": self.used_tokens,
            "max_tokens": self.max_tokens,
            "utilization": (
                f"{self.used_tokens / self.max_tokens * 100:.1f}%"
                if self.max_tokens > 0 else "N/A"
            ),
            "breakdown": self._breakdown.to_dict(),
            "compression_ratio": self._compression_ratio,
            "thinking_level": self._thinking_level,
        }


class MiniTokenMeter(Static):
    """
    Minimal single-line token meter for status bars.

    Shows: ▰▰▰▱▱ 15k/32k
    """

    DEFAULT_CSS = """
    MiniTokenMeter {
        height: 1;
        width: auto;
        padding: 0;
    }
    """

    used: reactive[int] = reactive(0)
    limit: reactive[int] = reactive(32000)

    def render(self) -> str:
        """Render mini meter."""
        if self.limit == 0:
            return "[dim]--[/dim]"

        ratio = min(self.used / self.limit, 1.0)

        # Color based on usage
        if ratio >= 0.90:
            color = "#EF4444"
        elif ratio >= 0.75:
            color = "#F59E0B"
        else:
            color = "#22C55E"

        # 5-segment bar
        filled = int(ratio * 5)
        bar = f"[{color}]{'▰' * filled}[/{color}][dim]{'▱' * (5 - filled)}[/dim]"

        # Format numbers
        used_str = self._format_k(self.used)
        limit_str = self._format_k(self.limit)

        return f"{bar} {used_str}/{limit_str}"

    @staticmethod
    def _format_k(n: int) -> str:
        if n >= 1000:
            return f"{n//1000}k"
        return str(n)


__all__ = [
    "TokenBreakdown",
    "TokenMeter",
    "TokenBreakdownWidget",
    "CompressionIndicator",
    "ThinkingLevelIndicator",
    "TokenDashboard",
    "MiniTokenMeter",
]
