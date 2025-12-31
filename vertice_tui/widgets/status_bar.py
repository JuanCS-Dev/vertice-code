"""
Status Bar Widget - Phase 9 Premium Design.

Modern status bar with Model, Agent, Tokens, Cost display.
Uses Unicode minimalista (no emojis).

Phase 10: Sprint 5 - Added MiniTokenMeter integration.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Static

from vertice_tui.widgets.token_meter import MiniTokenMeter


class StatusBar(Horizontal):
    """Premium status bar with Model, Agent, Tokens, Cost metrics."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        dock: bottom;
        background: $surface;
        padding: 0 1;
    }

    StatusBar > Static {
        width: auto;
        padding: 0 1;
    }

    .mode {
        color: $accent;
        text-style: bold;
    }

    .model {
        color: $primary;
    }

    .agent {
        color: $secondary;
    }

    .tokens {
        color: $foreground;
    }

    MiniTokenMeter {
        width: auto;
        min-width: 14;
    }

    .cost {
        color: $warning;
    }

    .separator {
        color: $border;
    }

    .errors {
        color: $error;
    }
    """

    # Core metrics
    mode: reactive[str] = reactive("READY")
    model_name: reactive[str] = reactive("gemini-2.0")
    agent_name: reactive[str] = reactive("Coder")
    token_used: reactive[int] = reactive(0)
    token_limit: reactive[int] = reactive(8000)
    cost: reactive[float] = reactive(0.0)
    errors: reactive[int] = reactive(0)

    # Legacy compatibility
    llm_connected: reactive[bool] = reactive(False)
    governance_status: reactive[str] = reactive("")
    agent_count: reactive[int] = reactive(13)
    tool_count: reactive[int] = reactive(0)
    tribunal_mode: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        """Compose premium status bar."""
        yield Static(self._format_mode(), id="mode", classes="mode")
        yield Static(" | ", classes="separator")
        yield Static(self._format_model(), id="model", classes="model")
        yield Static(" | ", classes="separator")
        yield Static(self._format_agent(), id="agent", classes="agent")
        yield Static(" | ", classes="separator")
        yield MiniTokenMeter(id="mini-meter")
        yield Static(" | ", classes="separator")
        yield Static(self._format_cost(), id="cost", classes="cost")
        yield Static(" | ", classes="separator")
        yield Static(self._format_errors(), id="errors", classes="errors")

    def _format_mode(self) -> str:
        """Format mode indicator."""
        icons = {
            "READY": "▸",
            "PROCESSING": "◐",
            "THINKING": "◑",
            "ERROR": "✗",
        }
        icon = icons.get(self.mode, "▸")
        return f"{icon} {self.mode}"

    def _format_model(self) -> str:
        """Format model name."""
        if self.tribunal_mode:
            return "[bold #EF4444]TRIBUNAL[/bold #EF4444]"
        if not self.llm_connected:
            return "[dim]No Model[/dim]"
        return f"[bold]{self.model_name}[/bold]"

    def _format_agent(self) -> str:
        """Format current agent."""
        return f"◆ {self.agent_name}"

    def _format_tokens(self) -> str:
        """Format token usage."""
        if self.token_limit > 0:
            ratio = self.token_used / self.token_limit
            if ratio > 0.9:
                color = "#EF4444"  # Red
            elif ratio > 0.7:
                color = "#F59E0B"  # Amber
            else:
                color = "#22C55E"  # Green
            return f"[{color}]{self._format_number(self.token_used)}/{self._format_number(self.token_limit)}[/{color}]"
        return f"{self._format_number(self.token_used)} tokens"

    def _format_cost(self) -> str:
        """Format cost tracker."""
        if self.cost >= 1.0:
            return f"[bold #F59E0B]${self.cost:.2f}[/bold #F59E0B]"
        return f"${self.cost:.3f}"

    def _format_errors(self) -> str:
        """Format error count."""
        if self.errors > 0:
            return f"[#EF4444]✗ {self.errors}[/#EF4444]"
        return "[#22C55E]✓[/#22C55E]"

    @staticmethod
    def _format_number(n: int) -> str:
        """Format number with K/M suffix."""
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n/1_000:.1f}k"
        return str(n)

    # Watchers for reactive updates
    def watch_mode(self, value: str) -> None:
        self._update_element("#mode", self._format_mode())

    def watch_model_name(self, value: str) -> None:
        self._update_element("#model", self._format_model())

    def watch_agent_name(self, value: str) -> None:
        self._update_element("#agent", self._format_agent())

    def watch_token_used(self, value: int) -> None:
        self._update_element("#tokens", self._format_tokens())

    def watch_token_limit(self, value: int) -> None:
        self._update_element("#tokens", self._format_tokens())

    def watch_cost(self, value: float) -> None:
        self._update_element("#cost", self._format_cost())

    def watch_errors(self, value: int) -> None:
        self._update_element("#errors", self._format_errors())

    def watch_llm_connected(self, value: bool) -> None:
        self._update_element("#model", self._format_model())

    def watch_tribunal_mode(self, value: bool) -> None:
        self._update_element("#model", self._format_model())

    def watch_token_used(self, value: int) -> None:
        """Update mini token meter when token usage changes."""
        self._update_mini_meter()

    def watch_token_limit(self, value: int) -> None:
        """Update mini token meter when limit changes."""
        self._update_mini_meter()

    def _update_mini_meter(self) -> None:
        """Update the MiniTokenMeter widget."""
        try:
            meter = self.query_one("#mini-meter", MiniTokenMeter)
            meter.used = self.token_used
            meter.limit = self.token_limit
        except Exception:
            pass

    def update_tokens(self, used: int, limit: int) -> None:
        """Update token usage in mini meter.

        This is the preferred method for updating tokens from other components.

        Args:
            used: Number of tokens used
            limit: Maximum token limit
        """
        self.token_used = used
        self.token_limit = limit

    def _update_element(self, element_id: str, content: str) -> None:
        """Safely update element content."""
        try:
            self.query_one(element_id, Static).update(content)
        except Exception as e:
            # UI element may not exist yet during initialization
            import logging
            logging.debug(f"StatusBar element {element_id} update failed: {e}")
