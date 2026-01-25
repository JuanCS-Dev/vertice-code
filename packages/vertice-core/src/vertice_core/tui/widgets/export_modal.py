"""
Export Modal - UI for conversation export
========================================

Modal para exportar conversas em Markdown com opções de template.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Static, RadioSet, RadioButton, Input
from textual.screen import ModalScreen

from vertice_core.tui.handlers.export_handler import get_export_handler
from vertice_core.tui.widgets.session_tabs import SessionData


class ExportModal(ModalScreen[None]):
    """
    Modal for exporting conversations to Markdown.

    Features:
    - Template selection (formatted/raw)
    - Filename input
    - Session selection
    - Export status feedback
    """

    DEFAULT_CSS = """
    ExportModal {
        width: 70%;
        height: 60%;
        align: center middle;
    }

    ExportModal > Vertical {
        padding: 2;
        background: $surface;
        border: solid $primary;
        border-radius: 1;
    }

    ExportModal RadioSet {
        margin: 1 0;
    }

    ExportModal Input {
        margin: 1 0;
    }

    ExportModal .status {
        margin-top: 1;
        color: $success;
    }

    ExportModal .error {
        margin-top: 1;
        color: $error;
    }
    """

    def __init__(self, sessions: List[SessionData], current_session_id: Optional[str] = None):
        super().__init__()
        self.sessions = sessions
        self.current_session_id = current_session_id
        self.export_handler = get_export_handler()
        self.selected_sessions: List[SessionData] = []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("📤 Export Conversations", classes="title")

            # Template selection
            with Vertical():
                yield Static("Template:", classes="label")
                with RadioSet():
                    yield RadioButton("Formatted (Beautiful, readable)", value=True, id="formatted")
                    yield RadioButton("Raw (Data dump for analysis)", id="raw")

            # Session selection
            with Vertical():
                yield Static("Sessions to export:", classes="label")
                with RadioSet(id="session-selector"):
                    for session in self.sessions:
                        label = f"{session.title} ({len(session.messages)} messages)"
                        if session.id == self.current_session_id:
                            label += " [CURRENT]"
                        yield RadioButton(
                            label,
                            value=(session.id == self.current_session_id),
                            id=f"session-{session.id}",
                        )

            # Filename
            yield Static("Filename (optional):", classes="label")
            yield Input(placeholder="auto-generated if empty", id="filename")

            # Actions
            with Horizontal():
                yield Button("Export", variant="primary", id="export-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

            # Status
            yield Static("", id="status")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "export-btn":
            await self._perform_export()
        elif event.button.id == "cancel-btn":
            self.dismiss()

    async def _perform_export(self) -> None:
        """Perform the export operation."""
        try:
            # Get selected template
            template = "formatted"  # default
            radio_set = self.query_one("RadioSet")
            for radio in radio_set.query("RadioButton"):
                if radio.value and radio.id:
                    template = radio.id
                    break

            # Get selected sessions
            session_selector = self.query_one("#session-selector", RadioSet)
            selected_sessions = []
            for radio in session_selector.query("RadioButton"):
                if radio.value and radio.id and radio.id.startswith("session-"):
                    session_id = radio.id[8:]  # Remove "session-" prefix
                    session = next((s for s in self.sessions if s.id == session_id), None)
                    if session:
                        selected_sessions.append(session)

            if not selected_sessions:
                self._show_status("No sessions selected", "error")
                return

            # Get filename
            filename_input = self.query_one("#filename", Input)
            custom_filename = filename_input.value.strip() if filename_input.value else None

            # Perform export
            exported_files = []
            for session in selected_sessions:
                if custom_filename and len(selected_sessions) == 1:
                    # Use custom filename for single export
                    exported_file = self.export_handler.export_session(
                        session, template, custom_filename
                    )
                else:
                    # Auto-generate filename
                    exported_file = self.export_handler.export_session(session, template)

                exported_files.append(exported_file)

            # Show success
            if len(exported_files) == 1:
                self._show_status(f"✅ Exported to: {exported_files[0]}", "success")
            else:
                self._show_status(f"✅ Exported {len(exported_files)} files", "success")

        except Exception as e:
            self._show_status(f"❌ Export failed: {e}", "error")

    def _show_status(self, message: str, status_type: str) -> None:
        """Show status message."""
        status = self.query_one("#status", Static)
        status.update(message)
        status.remove_class("status", "error")
        status.add_class(status_type)
