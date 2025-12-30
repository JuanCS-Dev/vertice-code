"""
Status Bar Widget.

Expanded status bar with LLM, governance, agent, and tool metrics.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Static


class StatusBar(Horizontal):
    """Expanded status bar with LLM, governance, agent, and tool metrics."""

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
        color: $success;
        text-style: bold;
    }

    .llm-status {
        color: $secondary;
    }

    .governance {
        color: $warning;
    }

    .agents {
        color: $primary;
    }

    .tools {
        color: $primary;
    }

    .errors {
        color: $error;
    }
    """

    mode: reactive[str] = reactive("READY")
    llm_connected: reactive[bool] = reactive(False)
    governance_status: reactive[str] = reactive("👀 Observer")
    agent_count: reactive[int] = reactive(13)
    tool_count: reactive[int] = reactive(0)
    errors: reactive[int] = reactive(0)
    tribunal_mode: reactive[bool] = reactive(False)  # MAXIMUS Tribunal Mode

    def compose(self) -> ComposeResult:
        yield Static(self._format_mode(), id="mode", classes="mode")
        yield Static(self._format_llm(), id="llm-status", classes="llm-status")
        yield Static(self._format_governance(), id="governance", classes="governance")
        yield Static(self._format_agents(), id="agents", classes="agents")
        yield Static(self._format_tools(), id="tools", classes="tools")
        yield Static(self._format_errors(), id="errors", classes="errors")

    def _format_mode(self) -> str:
        return f"⚡ {self.mode}"

    def _format_llm(self) -> str:
        if self.tribunal_mode:
            return "[bold red]⚖️ TRIBUNAL[/bold red]"
        if self.llm_connected:
            return "✅ Gemini"
        return "❌ No LLM"

    def _format_governance(self) -> str:
        return self.governance_status

    def _format_agents(self) -> str:
        return f"🤖 {self.agent_count}"

    def _format_tools(self) -> str:
        return f"🔧 {self.tool_count}"

    def _format_errors(self) -> str:
        icon = "✗" if self.errors > 0 else "✓"
        color = "red" if self.errors > 0 else "green"
        return f"[{color}]{icon} {self.errors}[/{color}]"

    def watch_mode(self, value: str) -> None:
        try:
            self.query_one("#mode", Static).update(self._format_mode())
        except Exception:
            pass

    def watch_llm_connected(self, value: bool) -> None:
        try:
            self.query_one("#llm-status", Static).update(self._format_llm())
        except Exception:
            pass

    def watch_governance_status(self, value: str) -> None:
        try:
            self.query_one("#governance", Static).update(self._format_governance())
        except Exception:
            pass

    def watch_agent_count(self, value: int) -> None:
        try:
            self.query_one("#agents", Static).update(self._format_agents())
        except Exception:
            pass

    def watch_tool_count(self, value: int) -> None:
        try:
            self.query_one("#tools", Static).update(self._format_tools())
        except Exception:
            pass

    def watch_errors(self, value: int) -> None:
        try:
            self.query_one("#errors", Static).update(self._format_errors())
        except Exception:
            pass

    def watch_tribunal_mode(self, value: bool) -> None:
        """Update LLM status when tribunal mode changes."""
        try:
            self.query_one("#llm-status", Static).update(self._format_llm())
        except Exception:
            pass
