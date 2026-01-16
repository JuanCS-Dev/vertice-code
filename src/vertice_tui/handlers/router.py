"""
Command Router for JuanCS Dev-Code.

Routes slash commands to appropriate handlers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vertice_tui.app import QwenApp
    from vertice_tui.widgets.response_view import ResponseView


class CommandRouter:
    """
    Routes slash commands to appropriate handler modules.

    Lazy loads handlers to avoid circular imports.
    """

    def __init__(self, app: "QwenApp"):
        self.app = app
        self._basic = None
        self._agents = None
        self._claude_parity = None
        self._session = None
        self._operations = None
        self._context = None
        self._a2a = None

    @property
    def basic(self):
        """Lazy load basic commands handler."""
        if self._basic is None:
            from vertice_tui.handlers.basic import BasicCommandHandler

            self._basic = BasicCommandHandler(self.app)
        return self._basic

    @property
    def agents(self):
        """Lazy load agents handler."""
        if self._agents is None:
            from vertice_tui.handlers.agents import AgentCommandHandler

            self._agents = AgentCommandHandler(self.app)
        return self._agents

    @property
    def claude_parity(self):
        """Lazy load Claude parity handler."""
        if self._claude_parity is None:
            from vertice_tui.handlers.claude_parity import ClaudeParityHandler

            self._claude_parity = ClaudeParityHandler(self.app)
        return self._claude_parity

    @property
    def session(self):
        """Lazy load session handler."""
        if self._session is None:
            from vertice_tui.handlers.session import SessionCommandHandler

            self._session = SessionCommandHandler(self.app)
        return self._session

    @property
    def operations(self):
        """Lazy load operations handler."""
        if self._operations is None:
            from vertice_tui.handlers.operations import OperationsHandler

            self._operations = OperationsHandler(self.app)
        return self._operations

    @property
    def context(self):
        """Lazy load context commands handler."""
        if self._context is None:
            from vertice_tui.handlers.context_commands import ContextCommandHandler

            self._context = ContextCommandHandler(self.app)
        return self._context

    @property
    def a2a(self):
        """Lazy load A2A commands handler."""
        if self._a2a is None:
            from vertice_tui.handlers.a2a import A2ACommandHandler

            self._a2a = A2ACommandHandler(self.app)
        return self._a2a

    async def dispatch(self, cmd: str, view: "ResponseView") -> bool:
        """
        Dispatch a command to the appropriate handler.

        Returns True if command was handled, False otherwise.
        """
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # File context commands (Phase 10: Claude Code parity)
        if command in ("/add", "/remove", "/files", "/context-files"):
            await self.context.handle(command, args, view)
            return True

        # Basic commands
        if command in (
            "/help",
            "/clear",
            "/quit",
            "/exit",
            "/run",
            "/read",
            "/agents",
            "/status",
            "/tools",
            "/palette",
            "/history",
            "/context",
            "/context-clear",
            "/prometheus",
            "/providers",
        ):
            await self.basic.handle(command, args, view)
            return True

        # Agent commands
        if command in (
            "/plan",
            "/execute",
            "/architect",
            "/review",
            "/explore",
            "/refactor",
            "/test",
            "/security",
            "/docs",
            "/perf",
            "/devops",
            "/justica",
            "/sofia",
            "/data",
            # Core agents (Phase 6)
            "/orchestrator",
            "/coder",
            "/researcher",
        ):
            await self.agents.handle(command, args, view)
            return True

        # A2A commands (Phase 6.3)
        if command == "/a2a":
            await self.a2a.handle(command, args, view)
            return True

        # Claude parity commands
        if command in (
            "/compact",
            "/cost",
            "/tokens",
            "/todos",
            "/todo",
            "/model",
            "/init",
            "/hooks",
            "/mcp",
            "/router",
            "/router-status",
            "/route",
            "/bashes",
            "/bg",
            "/kill",
            "/notebook",
            "/task",
            "/subagents",
            "/ask",
            "/commands",
            "/command-create",
            "/command-delete",
            "/plan-mode",
            "/plan-status",
            "/plan-note",
            "/plan-exit",
            "/plan-approve",
        ):
            await self.claude_parity.handle(command, args, view)
            return True

        # Session commands
        if command in (
            "/resume",
            "/save",
            "/sessions",
            "/checkpoint",
            "/rewind",
            "/export",
            "/doctor",
            "/permissions",
            "/sandbox",
            "/login",
            "/logout",
            "/auth",
            "/memory",
            "/remember",
        ):
            await self.session.handle(command, args, view)
            return True

        # Operations commands
        if command in (
            "/pr",
            "/pr-draft",
            "/image",
            "/pdf",
            "/audit",
            "/diff",
            "/backup",
            "/restore",
            "/undo",
            "/redo",
            "/undo-stack",
            "/secrets",
            "/secrets-staged",
        ):
            await self.operations.handle(command, args, view)
            return True

        # TRIBUNAL mode toggle (MAXIMUS integration)
        if command == "/tribunal":
            self.app.action_toggle_tribunal()
            return True

        # Check for custom command
        custom_cmd_name = command.lstrip("/")
        custom_prompt = self.app.bridge.execute_custom_command(custom_cmd_name, args)

        if custom_prompt:
            if view:
                view.add_system_message(f"📜 *Running custom command: `/{custom_cmd_name}`*")
            await self.app._handle_chat(custom_prompt, view)
            return True

        # Unknown command
        view.add_error(f"Unknown command: {command}")
        view.add_system_message("Type `/help` for available commands.")
        return False

    async def _handle_export(self, view) -> None:
        """Handle conversation export command."""
        from vertice_tui.widgets.export_modal import ExportModal
        from vertice_tui.widgets.session_tabs import SessionData

        # Get current sessions (mock for now - would integrate with actual session manager)
        sessions = [
            SessionData(
                title="Test Session 1",
                messages=[
                    {"role": "user", "content": "Hello", "timestamp": "2026-01-09T14:00:00"},
                    {
                        "role": "assistant",
                        "content": "Hi there!",
                        "timestamp": "2026-01-09T14:00:01",
                    },
                ],
            )
        ]

        current_session_id = sessions[0].id if sessions else None

        # Show export modal
        modal = ExportModal(sessions, current_session_id)
        await self.app.mount(modal)
        view.add_success("📤 Export modal opened. Select template and export your conversations!")
        return True
