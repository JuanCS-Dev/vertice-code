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
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input
from textual import on, events

# Local imports
from vertice_core.tui.constants import HELP_TEXT
from vertice_core.tui.widgets import AutocompleteDropdown, ResponseView, StatusBar, TokenDashboard
from vertice_core.tui.widgets.fuzzy_search_modal import FuzzySearchModal
from vertice_core.tui.handlers import CommandRouter
from vertice_core.tui.themes import (
    THEME_VERTICE_DARK,
    THEME_VERTICE_LIGHT,
    THEME_LIGHT,
    THEME_DARK,
    ThemeManager,
)
from vertice_core.tui.app_styles import APP_CSS, detect_language


@dataclass
class ChatPerf:
    request_id: str
    prompt_chars: int
    t_submit: float
    t_worker_start: float | None = None
    t_first_sse: float | None = None
    t_first_text_delta: float | None = None
    t_done: float | None = None
    text_chars: int = 0
    outcome: str = "unknown"
    error: str | None = None


def _append_jsonl_sync(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(record, ensure_ascii=False) + "\n")


class VerticeApp(App):
    """
    Vértice - Sovereign Intelligence & Tactical Execution.

    A beautiful, fast, minimal TUI for AI-powered development.
    60fps rendering, security-first design, extensible core.
    """

    TITLE = "VERTICE"
    SUB_TITLE = "Agent Agency"
    LAYERS = ["base", "autocomplete"]
    CSS = APP_CSS
    ALLOW_SELECT = True  # Enable mouse text selection (Shift+drag for native selection)

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+c", "quit", "Exit", show=True),
        Binding("ctrl+l", "clear", "Clear", show=True),
        Binding("ctrl+k", "command_palette", "Commands", show=True),
        Binding("ctrl+f", "search", "Search", show=True),
        Binding("ctrl+space", "panic_button", "Emergency Stop", show=True),
        Binding("ctrl+h", "show_help", "Help", show=True),
        Binding("ctrl+t", "toggle_theme", "Theme", show=True),
        Binding("ctrl+d", "toggle_dashboard", "Tokens", show=True),
        Binding("ctrl+m", "toggle_tribunal", "Tribunal", show=True),
        Binding("ctrl+p", "toggle_prometheus", "Prometheus", show=True),
        Binding("ctrl+r", "registry", "Registry", show=True),
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

    AUTOCOMPLETE_DEBOUNCE_S: ClassVar[float] = 0.06

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
        self._perf_log_path = self._resolve_perf_log_path()
        self._prompt: Input | None = None
        self._autocomplete: AutocompleteDropdown | None = None
        self._response_view: ResponseView | None = None
        self._status_bar: StatusBar | None = None
        self._token_dashboard: TokenDashboard | None = None

    def _resolve_perf_log_path(self) -> Path | None:
        path_str = os.getenv("VERTICE_TUI_PERF_LOG_PATH", "").strip()
        if not path_str:
            return None
        return Path(path_str).expanduser()

    @property
    def bridge(self):
        """Lazy load the integration bridge."""
        if self._bridge is None:
            from vertice_core.tui.core.bridge import get_bridge

            self._bridge = get_bridge()
        return self._bridge

    @bridge.setter
    def bridge(self, value):
        """Allow setting bridge for testing purposes."""
        self._bridge = value

    @property
    def router(self) -> CommandRouter:
        """Lazy load the command router."""
        if self._router is None:
            self._router = CommandRouter(self)
        return self._router

    def compose(self) -> ComposeResult:
        """Compose the UI - Gemini CLI style."""
        yield Header(show_clock=True)

        # Token Dashboard (collapsible, below header)
        yield TokenDashboard(id="token-dashboard", classes="collapsed")

        with Container(id="main"):
            yield ResponseView(id="response")
            with Horizontal(id="input-area"):
                from textual.widgets import Static

                yield Static("❯", id="prompt-icon")
                yield Input(placeholder="Type your command or ask anything...", id="prompt")

        yield AutocompleteDropdown(id="autocomplete")
        yield StatusBar()
        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted - show banner and init bridge."""
        self.register_theme(THEME_VERTICE_DARK)
        self.register_theme(THEME_VERTICE_LIGHT)
        self.register_theme(THEME_LIGHT)
        self.register_theme(THEME_DARK)
        self.theme = ThemeManager.get_theme_preference()

        self._autocomplete = self.query_one("#autocomplete", AutocompleteDropdown)
        self._prompt = self.query_one("#prompt", Input)
        self._response_view = self.query_one("#response", ResponseView)
        self._status_bar = self.query_one(StatusBar)
        self._token_dashboard = self.query_one("#token-dashboard", TokenDashboard)

        # Restore PROMETHEUS mode preference
        prometheus_enabled = ThemeManager.get_prometheus_preference()
        if prometheus_enabled:
            status = self._status_bar
            status.prometheus_mode = True
            self.bridge.prometheus_mode = True

        response = self._response_view
        response.add_banner()

        # Initialize TokenDashboard with model limits
        dashboard = self._token_dashboard
        model_limits = {
            "gpt-4": 128_000,
            "gpt-4-turbo": 128_000,
            # Claude 4.5 via Vertex AI
            "sonnet-4.5": 200_000,
            "opus-4.5": 200_000,
            "claude-sonnet-4-5@20250929": 200_000,
            "claude-opus-4-5@20251101": 200_000,
            "gemini-3": 2_000_000,
        }
        # Default to 32k for unknown models
        default_limit = 32_000
        try:
            current_model = getattr(self.bridge, "model_name", "unknown")
            limit = model_limits.get(current_model, default_limit)
            dashboard.update_usage(0, limit)
        except (AttributeError, KeyError):
            dashboard.update_usage(0, default_limit)

        status = self._status_bar
        try:
            status.llm_connected = self.bridge.is_connected
            status.agent_count = (
                len(self.bridge.agents.available_agents) if self.bridge.agents else 0
            )
            status.tool_count = self.bridge.tools.get_tool_count() if self.bridge.tools else 0
            status.governance_status = (
                self.bridge.governance.get_status_emoji() if self.bridge.governance else "??"
            )

            if self.bridge.is_connected:
                # Get provider info dynamically
                provider_name = "LLM"
                if (
                    hasattr(self.bridge.llm, "_vertice_coreent")
                    and self.bridge.llm._vertice_coreent
                ):
                    providers = self.bridge.llm._vertice_coreent.get_available_providers()
                    current = self.bridge.llm._vertice_coreent.current_provider
                    if current:
                        provider_name = current.capitalize()
                    elif providers:
                        provider_name = f"{len(providers)} providers"
                else:
                    provider_name = "Gemini"

                # Build concise status
                parts = []
                if status.tool_count > 0:
                    parts.append(f"{status.tool_count} tools")
                if status.agent_count > 0:
                    parts.append(f"{status.agent_count} agents")

                status_str = " | ".join(parts) if parts else ""
                help_hint = "Type [bold cyan]/help[/bold cyan] for commands or just chat."

                response.add_system_message(
                    f"✅ **{provider_name} connected!** {status_str}\n\n{help_hint}"
                )
            else:
                response.add_system_message(
                    "⚠️ **No LLM configured.** Set API keys for providers:\n"
                    "- `GROQ_API_KEY` (free, fast)\n"
                    "- `GEMINI_API_KEY` (Google)\n"
                    "- `MISTRAL_API_KEY` (EU)\n\n"
                    "Type `/help` for available commands."
                )
        except Exception as e:
            response.add_system_message(f"⚠️ Bridge init: {e}\n\nType `/help` for commands.")

        self._prompt.focus()

        # Performance: Start background warm-up of heavy components
        # This loads providers and tool schemas without blocking the UI rendering
        self.run_worker(self.bridge.warmup(), name="bridge_warmup", group="system")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission with robust validation and error handling."""
        status = None
        try:
            response = self._response_view
            if response is None:
                response = self.query_one("#response", ResponseView)
                self._response_view = response

            autocomplete = self._autocomplete
            if autocomplete is None:
                autocomplete = self.query_one("#autocomplete", AutocompleteDropdown)
                self._autocomplete = autocomplete

            prompt = self._prompt
            if prompt is None:
                prompt = self.query_one("#prompt", Input)
                self._prompt = prompt

            status = self._status_bar
            if status is None:
                status = self.query_one(StatusBar)
                self._status_bar = status

            # Input validation and sanitization
            if not event.value or not isinstance(event.value, str):
                return

            user_input = event.value.strip()
            submit_time = time.perf_counter()

            # Length validation
            if len(user_input) > 5000:  # Reasonable limit for terminal input
                response.current_response += "\n❌ Error: Input too long (max 5000 characters)"
                return

            if len(user_input) == 0:
                return

            # Content validation - prevent obvious injection attempts
            dangerous_patterns = ["<script", "javascript:", "data:", "\x00", "\r\n\r\n"]
            if any(pattern in user_input.lower() for pattern in dangerous_patterns):
                response.current_response += "\n❌ Error: Invalid input content"
                return

            # Rate limiting check - simple in-memory for TUI
            current_time = asyncio.get_event_loop().time()
            if hasattr(self, "_last_input_time"):
                time_diff = current_time - self._last_input_time
                if time_diff < 0.1:  # Minimum 100ms between inputs
                    return  # Silently ignore rapid inputs
            self._last_input_time = current_time

            # UI updates
            autocomplete.hide()

            prompt.value = ""

            # History management with bounds checking and memory optimization
            self.history.append(user_input)
            if len(self.history) > 1000:  # Limit history size for memory efficiency
                self.history = self.history[-1000:]
            self.history_index = len(self.history)

            # Memory optimization: limit concurrent operations
            if hasattr(self, "_active_operations"):
                # Clean up completed operations
                self._active_operations = [op for op in self._active_operations if not op.done()]
                if len(self._active_operations) > 3:  # Max 3 concurrent operations
                    return  # Silently drop if too many operations
            else:
                self._active_operations = []

            response.add_user_message(user_input)

            status.mode = "PROCESSING"

            # CRITICAL: Force UI refresh so user sees their input immediately
            # Using run_worker ensures the handler returns immediately, allowing
            # the event loop to repaint the screen while chat processes in background.
            self.refresh()  # Request screen redraw

            # Generate unique task ID
            task_id = f"chat_{time.time_ns()}"

            # Command routing via Worker API (Textual Best Practice)
            # Note: Timeouts and Error handling are now managed within the workers/tasks
            # run_worker returns a Worker object but we fire-and-forget here for speed
            if user_input.startswith("/"):
                self.run_worker(
                    self._handle_command(user_input, response),
                    name=f"cmd_{task_id}",
                    group="chat_dispatch",
                    exclusive=True,
                )
            else:
                perf = None
                if self._perf_log_path is not None:
                    perf = ChatPerf(
                        request_id=task_id,
                        prompt_chars=len(user_input),
                        t_submit=submit_time,
                    )
                self.run_worker(
                    self._handle_chat_with_timeout(user_input, response, perf),
                    name=task_id,
                    group="chat_dispatch",
                    exclusive=True,
                )

        except Exception as e:
            # Ultimate error handler - ensure TUI remains functional
            try:
                response = self.query_one("#response", ResponseView)
                response.current_response += f"\n💥 Critical error: {str(e)[:100]}"
                self.notify("Critical error occurred", severity="error")
                if status is not None:
                    status.mode = "READY"
            except Exception as log_error:
                # If even error reporting fails, at least log it
                print(
                    f"CRITICAL: Unhandled error in input submission: {e}, logging failed: {log_error}"
                )

    @on(Input.Changed, "#prompt")
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes for autocomplete."""
        text = event.value or ""
        autocomplete = self._autocomplete or self.query_one("#autocomplete", AutocompleteDropdown)

        if not text:
            autocomplete.hide()
            return

        # Check for @ file picker trigger
        has_at_trigger = any(
            text[i] == "@" and (i == 0 or text[i - 1].isspace())
            for i in range(len(text) - 1, -1, -1)
        )

        # Show autocomplete for / commands or @ files
        should_autocomplete = text.startswith("/") or has_at_trigger or len(text) >= 2
        if not should_autocomplete:
            autocomplete.hide()
            return

        self.run_worker(
            self._update_autocomplete_after_debounce(text),
            name="autocomplete",
            group="autocomplete",
            exclusive=True,
        )

    async def _update_autocomplete_after_debounce(self, text: str) -> None:
        """Debounced autocomplete update (keeps input handlers non-blocking)."""
        await asyncio.sleep(self.AUTOCOMPLETE_DEBOUNCE_S)

        prompt = self._prompt
        if prompt is None or prompt.value != text:
            return

        autocomplete = self._autocomplete
        if autocomplete is None:
            return

        try:
            completer = self.bridge.autocomplete
            get_completions = getattr(
                completer, "get_completions_threadsafe", completer.get_completions
            )
            completions = await asyncio.to_thread(get_completions, text, 15)
        except Exception:
            autocomplete.hide()
            return

        if prompt.value != text:
            return

        if completions:
            autocomplete.show_completions(completions)
        else:
            autocomplete.hide()

    async def on_key(self, event: events.Key) -> None:
        """Handle special keys for autocomplete navigation."""
        autocomplete = self._autocomplete
        if autocomplete is None:
            autocomplete = self.query_one("#autocomplete", AutocompleteDropdown)
            self._autocomplete = autocomplete

        prompt = self._prompt
        if prompt is None:
            prompt = self.query_one("#prompt", Input)
            self._prompt = prompt

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

    async def _handle_command(self, cmd: str, view: ResponseView) -> None:
        """Run a slash command with timeout and UI-safe error handling."""
        status = self.query_one(StatusBar)
        status.mode = "PROCESSING"
        try:
            await asyncio.wait_for(self.router.dispatch(cmd, view), timeout=30.0)
        except asyncio.TimeoutError:
            view.add_error("Command timed out after 30s")
            self.notify("Command timed out", severity="error")
        except Exception as op_error:
            error_msg = str(op_error)
            if len(error_msg) > 200:
                error_msg = error_msg[:197] + "..."
            view.add_error(f"Command failed: {error_msg}")
            self.notify(f"Command failed: {error_msg[:50]}...", severity="error")
        finally:
            status.mode = "READY"

    async def _handle_chat_with_timeout(
        self, message: str, view: ResponseView, perf: ChatPerf | None
    ) -> None:
        """Run chat with a hard timeout (runs in a Worker)."""
        try:
            await asyncio.wait_for(self._handle_chat(message, view, perf), timeout=120.0)
        except asyncio.TimeoutError:
            view.add_error("Chat timed out after 120s")
            self.notify("Chat timed out", severity="error")

    def _emit_chat_perf(self, perf: ChatPerf) -> None:
        """Emit a single JSONL perf record (best-effort, non-blocking)."""
        if self._perf_log_path is None:
            return

        def _ms(start: float | None, end: float | None) -> float | None:
            if start is None or end is None:
                return None
            return (end - start) * 1000.0

        record = {
            "request_id": perf.request_id,
            "prompt_chars": perf.prompt_chars,
            "text_chars": perf.text_chars,
            "outcome": perf.outcome,
            "error": perf.error,
            "t_submit_to_worker_ms": _ms(perf.t_submit, perf.t_worker_start),
            "t_submit_to_first_sse_ms": _ms(perf.t_submit, perf.t_first_sse),
            "t_submit_to_first_text_delta_ms": _ms(perf.t_submit, perf.t_first_text_delta),
            "t_total_ms": _ms(perf.t_submit, perf.t_done),
        }

        async def _write() -> None:
            try:
                await asyncio.to_thread(_append_jsonl_sync, self._perf_log_path, record)
            except Exception:
                pass

        try:
            asyncio.get_running_loop().create_task(_write())
        except RuntimeError:
            pass

    async def _handle_chat(
        self, message: str, view: ResponseView, perf: ChatPerf | None = None
    ) -> None:
        """Handle natural language chat via Gemini Open Responses streaming."""
        from vertice_core.tui.core.openresponses_events import (
            OpenResponsesParser,
            OpenResponsesOutputTextDeltaEvent,
        )

        # Create task for operation tracking
        current_task = asyncio.current_task()
        if hasattr(self, "_active_operations"):
            self._active_operations.append(current_task)

        self.is_processing = True
        status = self._status_bar
        if status is None:
            status = self.query_one(StatusBar)
            self._status_bar = status
        status.mode = "THINKING"

        # Immediate UI feedback (don’t wait for the first SSE event).
        view.start_thinking()
        await asyncio.sleep(0)

        parser = OpenResponsesParser()
        if perf is not None:
            perf.t_worker_start = time.perf_counter()

        try:
            # bridge.chat primarily yields Open Responses SSE blocks, but some internal
            # components may still emit plain text (e.g. tool execution summaries).
            # Keep the UI resilient by treating non-SSE lines as text deltas.
            async for sse_chunk in self.bridge.chat(message):
                if perf is not None and perf.t_first_sse is None:
                    perf.t_first_sse = time.perf_counter()

                # SSE chunks may contain multiple lines
                for line in sse_chunk.splitlines(keepends=True):
                    event = parser.feed(line)
                    if event:
                        if perf is not None and isinstance(
                            event, OpenResponsesOutputTextDeltaEvent
                        ):
                            if perf.t_first_text_delta is None:
                                perf.t_first_text_delta = time.perf_counter()
                            perf.text_chars += len(event.delta)
                        await view.handle_open_responses_event(event)
                        continue

                    # Non-SSE passthrough: allow legacy/plain text chunks to render.
                    if line.startswith(("event: ", "data: ")):
                        continue
                    if not line.strip():
                        continue

                    if perf is not None:
                        if perf.t_first_text_delta is None:
                            perf.t_first_text_delta = time.perf_counter()
                        perf.text_chars += len(line)
                    view.append_chunk(line)

                # Optimized: removed unnecessary delay for better streaming performance

            status.governance_status = self.bridge.governance.get_status_emoji()
        except Exception as e:
            view.add_error(f"Chat error: {e}")
            status.errors += 1
            if perf is not None:
                perf.outcome = "error"
                perf.error = str(e)[:300]
        finally:
            if perf is not None:
                perf.t_done = time.perf_counter()
                task = asyncio.current_task()
                if task is not None and task.cancelling() and perf.outcome != "error":
                    perf.outcome = "cancelled"
                if perf.outcome == "unknown":
                    perf.outcome = "ok"
                self._emit_chat_perf(perf)

            # Clean up operation tracking
            if hasattr(self, "_active_operations") and current_task in self._active_operations:
                self._active_operations.remove(current_task)

            self.is_processing = False
            status.mode = "READY"
            await view.end_thinking()

    async def _execute_bash(self, command: str, view: ResponseView) -> None:
        """Execute bash command SECURELY via whitelist."""
        from vertice_core.tui.core.safe_executor import get_safe_executor

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
            try:
                self.workers.cancel_group(self, "chat_dispatch")
            except Exception:
                pass

            try:
                status = self.query_one(StatusBar)
                status.mode = "READY"
            except Exception:
                pass

            try:
                response = self.query_one("#response", ResponseView)
                self.run_worker(response.end_thinking(), name="cancel_end_thinking", group="system")
                response.add_error("Operation cancelled")
            except Exception:
                pass

    def action_toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        new_theme = ThemeManager.toggle_theme(self.theme)
        self.theme = new_theme
        response = self.query_one("#response", ResponseView)
        theme_name = "Claude Light ☀️" if new_theme == "claude-light" else "Matrix Dark 🌙"
        response.add_system_message(f"Theme switched to **{theme_name}**")

    def action_toggle_dashboard(self) -> None:
        """Toggle TokenDashboard visibility (collapsed/expanded)."""
        dashboard = self.query_one("#token-dashboard", TokenDashboard)
        if dashboard.has_class("collapsed"):
            dashboard.remove_class("collapsed")
        else:
            dashboard.add_class("collapsed")

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

    def action_toggle_prometheus(self) -> None:
        """Toggle PROMETHEUS mode - self-evolving meta-agent."""
        status = self.query_one(StatusBar)
        status.prometheus_mode = not status.prometheus_mode

        # Update bridge
        self.bridge.prometheus_mode = status.prometheus_mode

        # Persist preference
        ThemeManager.save_prometheus_preference(status.prometheus_mode)

        # User feedback
        response = self.query_one("#response", ResponseView)
        if status.prometheus_mode:
            mode_text = (
                "**🔥 PROMETHEUS MODE ENABLED**\n\n"
                "Self-evolving meta-agent activated:\n"
                "- 🌐 World Model simulation (SimuRA)\n"
                "- 🧠 6-type memory system (MIRIX)\n"
                "- 🔄 Self-reflection engine (Reflexion)\n"
                "- 📈 Co-evolution learning (Agent0)\n\n"
                "*Complex tasks will use enhanced reasoning.*"
            )
        else:
            mode_text = "**PROMETHEUS MODE DISABLED**\n\nReturned to standard mode."

        response.add_system_message(mode_text)

    def action_command_palette(self) -> None:
        """Open command palette (Ctrl+K)."""
        from vertice_core.tui.screens.command_palette import CommandPaletteScreen

        self.push_screen(CommandPaletteScreen(self.bridge))

    def action_search(self) -> None:
        """Open fuzzy search across sessions (Ctrl+F)."""
        # Get current session ID from session manager if available
        current_session_id = None
        if hasattr(self, "session_manager") and self.session_manager:
            try:
                # This would get current session ID
                current_session_id = getattr(self.session_manager, "current_session_id", None)
            except Exception:
                pass

        # Create and mount fuzzy search modal
        modal = FuzzySearchModal(
            session_manager=getattr(self, "session_manager", None),
            current_session_id=current_session_id,
            id="fuzzy-search-modal",
        )

        # Mount the modal
        self.mount(modal)
        modal.focus()

    def action_panic_button(self) -> None:
        """Emergency stop for all running agents (Safety UX)."""
        # Stop any ongoing processing
        if hasattr(self, "is_processing") and self.is_processing:
            self.is_processing = False

        # Cancel any pending tasks
        if hasattr(self.bridge, "cancel_all"):
            self.bridge.cancel_all()

        # Update UI to reflect emergency stop
        status = self._status_bar
        if status is None:
            status = self.query_one(StatusBar)
            self._status_bar = status
        status.mode = "EMERGENCY_STOP"
        status.errors += 1

        # Show emergency stop notification
        self.notify(
            "🚨 EMERGENCY STOP ACTIVATED - All agents halted", severity="warning", timeout=3.0
        )

        # Log the emergency stop
        print("🚨 EMERGENCY STOP: All agent operations halted by user")

    def action_registry(self) -> None:
        """Open registry screen (Ctrl+R)."""
        from vertice_core.tui.screens.registry_screen import RegistryScreen

        self.push_screen(RegistryScreen(self.bridge))

    # Scroll actions
    def action_scroll_up(self) -> None:
        """Scroll ResponseView up by one line."""
        response = self._response_view
        if response is None:
            response = self.query_one("#response", ResponseView)
            self._response_view = response
        response.scroll_up(animate=False)

    def action_scroll_down(self) -> None:
        """Scroll ResponseView down by one line."""
        response = self._response_view
        if response is None:
            response = self.query_one("#response", ResponseView)
            self._response_view = response
        response.scroll_down(animate=False)

    def action_scroll_up_page(self) -> None:
        """Scroll ResponseView up by one page."""
        response = self._response_view
        if response is None:
            response = self.query_one("#response", ResponseView)
            self._response_view = response
        response.scroll_page_up(animate=False)

    def action_scroll_down_page(self) -> None:
        """Scroll ResponseView down by one page."""
        response = self._response_view
        if response is None:
            response = self.query_one("#response", ResponseView)
            self._response_view = response
        response.scroll_page_down(animate=False)

    def action_scroll_home(self) -> None:
        """Scroll ResponseView to top."""
        response = self._response_view
        if response is None:
            response = self.query_one("#response", ResponseView)
            self._response_view = response
        response.scroll_home(animate=False)

    def action_scroll_end(self) -> None:
        """Scroll ResponseView to bottom."""
        response = self._response_view
        if response is None:
            response = self.query_one("#response", ResponseView)
            self._response_view = response
        response.scroll_end(animate=False)


def main() -> None:
    """Run the Vértice CLI application."""
    app = VerticeApp()
    app.run()


# Backward compatibility alias
QwenApp = VerticeApp


if __name__ == "__main__":
    main()
