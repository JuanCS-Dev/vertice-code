"""
JuanCS Dev-Code - The Minimal Masterpiece
==========================================

A beautiful, 60fps TUI inspired by:
- Gemini CLI's visual design
- Claude Code's simplicity
- Textual's power

Philosophy: "Perfection is achieved not when there is nothing more to add,
            but when there is nothing left to take away." - Antoine de Saint-Exupéry

Follows CODE_CONSTITUTION: <500 lines, 100% type hints

Soli Deo Gloria
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input
from textual import on, events

# Local imports
from vertice_tui.constants import HELP_TEXT
from vertice_tui.widgets import AutocompleteDropdown, ResponseView, StatusBar
from vertice_tui.handlers import CommandRouter
from vertice_tui.themes import THEME_LIGHT, THEME_DARK, ThemeManager
from vertice_tui.app_styles import APP_CSS, detect_language


class QwenApp(App):
    """
    JuanCS Dev-Code - The Minimal Masterpiece.

    A beautiful, fast, minimal TUI for AI-powered development.
    60fps rendering, security-first design, extensible core.
    """

    TITLE = "JuanCS Dev-Code"
    SUB_TITLE = "The Developer's Ally"
    LAYERS = ["base", "autocomplete"]
    CSS = APP_CSS

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+c", "quit", "Exit", show=True),
        Binding("ctrl+l", "clear", "Clear", show=True),
        Binding("ctrl+p", "show_help", "Help", show=True),
        Binding("ctrl+t", "toggle_theme", "Theme", show=True),
        Binding("ctrl+m", "toggle_tribunal", "Tribunal", show=True),
        Binding("escape", "cancel", "Cancel", show=False),
        # Scroll bindings for ResponseView (PageUp/PageDown always work)
        Binding("pageup", "scroll_up_page", "Page Up", show=False),
        Binding("pagedown", "scroll_down_page", "Page Down", show=False),
        Binding("ctrl+home", "scroll_home", "Top", show=False),
        Binding("ctrl+end", "scroll_end", "Bottom", show=False),
        # Ctrl+Arrow for fine scroll (Up/Down reserved for history)
        Binding("ctrl+up", "scroll_up", "Scroll Up", show=False),
        Binding("ctrl+down", "scroll_down", "Scroll Down", show=False),
    ]

    # State
    is_processing: reactive[bool] = reactive(False)

    def __init__(self) -> None:
        super().__init__()
        self.history: list[str] = []
        self.history_index = -1
        self._bridge = None  # Lazy loaded
        self._router = None  # Lazy loaded
        self._pending_image = None
        self._pending_pdf = None

    @property
    def bridge(self):
        """Lazy load the integration bridge."""
        if self._bridge is None:
            from vertice_tui.core.bridge import get_bridge
            self._bridge = get_bridge()
        return self._bridge

    @property
    def router(self) -> CommandRouter:
        """Lazy load the command router."""
        if self._router is None:
            self._router = CommandRouter(self)
        return self._router

    def compose(self) -> ComposeResult:
        """Compose the UI - Gemini CLI style."""
        yield Header(show_clock=True)

        with Container(id="main"):
            yield ResponseView(id="response")
            with Horizontal(id="input-area"):
                from textual.widgets import Static
                yield Static("❯", id="prompt-icon")
                yield Input(
                    placeholder="Type your command or ask anything...",
                    id="prompt"
                )

        yield AutocompleteDropdown(id="autocomplete")
        yield StatusBar()
        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted - show banner and init bridge."""
        self.register_theme(THEME_LIGHT)
        self.register_theme(THEME_DARK)
        self.theme = ThemeManager.get_theme_preference()

        response = self.query_one("#response", ResponseView)
        response.add_banner()

        status = self.query_one(StatusBar)
        try:
            status.llm_connected = self.bridge.is_connected
            status.agent_count = len(self.bridge.agents.available_agents)
            status.tool_count = self.bridge.tools.get_tool_count()
            status.governance_status = self.bridge.governance.get_status_emoji()

            if self.bridge.is_connected:
                tool_msg = f" {status.tool_count} tools loaded." if status.tool_count > 0 else ""
                response.add_system_message(
                    f"✅ **Gemini connected!**{tool_msg} Type `/help` for commands or just chat."
                )
            else:
                response.add_system_message(
                    "⚠️ **No LLM configured.** Set `GEMINI_API_KEY` for full functionality.\n\n"
                    "Type `/help` for available commands."
                )
        except Exception as e:
            response.add_system_message(f"⚠️ Bridge init: {e}\n\nType `/help` for commands.")

        self.query_one("#prompt", Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission."""
        user_input = event.value.strip()
        if not user_input:
            return

        autocomplete = self.query_one("#autocomplete", AutocompleteDropdown)
        autocomplete.hide()

        prompt = self.query_one("#prompt", Input)
        prompt.value = ""

        self.history.append(user_input)
        self.history_index = len(self.history)

        response = self.query_one("#response", ResponseView)
        response.add_user_message(user_input)

        status = self.query_one(StatusBar)
        status.mode = "PROCESSING"

        try:
            if user_input.startswith("/"):
                await self.router.dispatch(user_input, response)
            else:
                await self._handle_chat(user_input, response)
        finally:
            status.mode = "READY"

    @on(Input.Changed, "#prompt")
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes for autocomplete."""
        text = event.value
        autocomplete = self.query_one("#autocomplete", AutocompleteDropdown)

        if not text:
            autocomplete.hide()
            return

        # Check for @ file picker trigger
        has_at_trigger = any(
            text[i] == '@' and (i == 0 or text[i-1].isspace())
            for i in range(len(text) - 1, -1, -1)
        )

        if not text.startswith("/") and not has_at_trigger and len(text) < 2:
            autocomplete.hide()
            return

        try:
            completions = self.bridge.autocomplete.get_completions(text, max_results=15)
            autocomplete.show_completions(completions)
        except Exception:
            autocomplete.hide()

    async def on_key(self, event: events.Key) -> None:
        """Handle special keys for autocomplete navigation."""
        autocomplete = self.query_one("#autocomplete", AutocompleteDropdown)
        prompt = self.query_one("#prompt", Input)

        if not autocomplete.has_class("visible"):
            # Handle history navigation when autocomplete hidden
            if event.key == "up" and self.history:
                event.prevent_default()
                if self.history_index > 0:
                    self.history_index -= 1
                    prompt.value = self.history[self.history_index]
                    prompt.cursor_position = len(prompt.value)
            elif event.key == "down" and self.history:
                event.prevent_default()
                if self.history_index < len(self.history) - 1:
                    self.history_index += 1
                    prompt.value = self.history[self.history_index]
                    prompt.cursor_position = len(prompt.value)
            return

        if event.key == "up":
            event.prevent_default()
            autocomplete.move_selection(-1)
        elif event.key == "down":
            event.prevent_default()
            autocomplete.move_selection(1)
        elif event.key in ("tab", "enter"):
            selected = autocomplete.get_selected()
            if selected:
                event.prevent_default()
                prompt.value = selected + " "
                prompt.cursor_position = len(prompt.value)
                autocomplete.hide()
        elif event.key == "escape":
            event.prevent_default()
            autocomplete.hide()

    async def _handle_chat(self, message: str, view: ResponseView) -> None:
        """Handle natural language chat via Gemini streaming."""
        self.is_processing = True
        view.start_thinking()

        status = self.query_one(StatusBar)
        status.mode = "THINKING"

        try:
            async for chunk in self.bridge.chat(message):
                view.append_chunk(chunk)
                await asyncio.sleep(0)

            view.add_success("✓ Response complete")
            status.governance_status = self.bridge.governance.get_status_emoji()
        except Exception as e:
            view.add_error(f"Chat error: {e}")
            status.errors += 1
        finally:
            self.is_processing = False
            status.mode = "READY"
            view.end_thinking()

    async def _execute_bash(self, command: str, view: ResponseView) -> None:
        """Execute bash command SECURELY via whitelist."""
        from vertice_tui.core.safe_executor import get_safe_executor

        executor = get_safe_executor()
        is_allowed, reason = executor.is_command_allowed(command)

        if not is_allowed:
            view.add_error(f"🚫 Command blocked: {reason}")
            view.add_action("Allowed commands:")
            for category, commands in executor.get_allowed_commands_by_category().items():
                view.add_action(f"  [{category}]")
                for cmd in commands[:3]:
                    view.add_action(f"    • {cmd}")
            return

        view.add_action(f"🔒 Executing (whitelisted): {command}")
        result = await executor.execute(command)

        if result.success:
            if result.stdout:
                view.add_code_block(result.stdout, language="bash", title=command)
            view.add_success(f"✓ Command completed (exit code: {result.exit_code})")
        else:
            error_msg = result.error_message or result.stderr or "Unknown error"
            view.add_error(f"Command failed: {error_msg}")
            if result.stderr:
                view.add_code_block(result.stderr, language="text", title="stderr")

    async def _read_file(self, path_str: str, view: ResponseView) -> None:
        """Read and display file with syntax highlighting."""
        path = Path(path_str).expanduser()
        view.add_action(f"Reading: {path}")

        if not path.exists():
            view.add_error(f"File not found: {path}")
            return
        if not path.is_file():
            view.add_error(f"Not a file: {path}")
            return

        try:
            content = path.read_text()
            language = detect_language(path.suffix)
            view.add_code_block(content, language=language, title=str(path.name))
            view.add_success(f"Read {len(content):,} characters")
        except Exception as e:
            view.add_error(f"Read error: {e}")

    # Actions
    def action_quit(self) -> None:
        """Exit the application."""
        self.exit()

    def action_clear(self) -> None:
        """Clear the response view."""
        response = self.query_one("#response", ResponseView)
        response.clear_all()
        response.add_banner()

    def action_show_help(self) -> None:
        """Show help."""
        response = self.query_one("#response", ResponseView)
        response.add_system_message(HELP_TEXT)

    def action_cancel(self) -> None:
        """Cancel current operation."""
        if self.is_processing:
            self.is_processing = False
            response = self.query_one("#response", ResponseView)
            response.end_thinking()
            response.add_error("Operation cancelled")

    def action_toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        new_theme = ThemeManager.toggle_theme(self.theme)
        self.theme = new_theme
        response = self.query_one("#response", ResponseView)
        theme_name = "Claude Light ☀️" if new_theme == "claude-light" else "Matrix Dark 🌙"
        response.add_system_message(f"Theme switched to **{theme_name}**")

    def action_toggle_tribunal(self) -> None:
        """Toggle TRIBUNAL mode - forces all requests through MAXIMUS."""
        status = self.query_one(StatusBar)
        status.tribunal_mode = not status.tribunal_mode

        if status.tribunal_mode:
            self.bridge._provider_mode = "maximus"
            mode_text = (
                "**⚖️ TRIBUNAL MODE ENABLED**\n\n"
                "All requests now pass through MAXIMUS:\n"
                "- 🔍 VERITAS: Truth verification\n"
                "- 🧠 SOPHIA: Depth analysis\n"
                "- ⚖️ DIKĒ: Justice evaluation\n\n"
                "*Responses may take longer but ensure maximum accuracy.*"
            )
        else:
            self.bridge._provider_mode = "auto"
            mode_text = "**TRIBUNAL MODE DISABLED**\n\nReturned to auto-routing mode."

        response = self.query_one("#response", ResponseView)
        response.add_system_message(mode_text)

    # Scroll actions
    def action_scroll_up(self) -> None:
        """Scroll ResponseView up by one line."""
        self.query_one("#response", ResponseView).scroll_up(animate=False)

    def action_scroll_down(self) -> None:
        """Scroll ResponseView down by one line."""
        self.query_one("#response", ResponseView).scroll_down(animate=False)

    def action_scroll_up_page(self) -> None:
        """Scroll ResponseView up by one page."""
        self.query_one("#response", ResponseView).scroll_page_up(animate=False)

    def action_scroll_down_page(self) -> None:
        """Scroll ResponseView down by one page."""
        self.query_one("#response", ResponseView).scroll_page_down(animate=False)

    def action_scroll_home(self) -> None:
        """Scroll ResponseView to top."""
        self.query_one("#response", ResponseView).scroll_home(animate=False)

    def action_scroll_end(self) -> None:
        """Scroll ResponseView to bottom."""
        self.query_one("#response", ResponseView).scroll_end(animate=False)


def main() -> None:
    """Run the QWEN CLI application."""
    app = QwenApp()
    app.run(mouse=False)


if __name__ == "__main__":
    main()
