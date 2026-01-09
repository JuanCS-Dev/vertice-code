"""
Modal System - VERTICE TUI Visual Upgrade.

Provides modern modal dialogs using Textual ModalScreen pattern.
Includes: ConfirmDialog, AlertDialog, InputDialog, FilePickerDialog.

Phase 11: Visual Upgrade Sprint 1.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static, DirectoryTree


class ConfirmDialog(ModalScreen[bool]):
    """
    Confirmation dialog with Yes/No buttons.

    Accessibility:
        - role="dialog" for screen readers
        - Focus trapped within dialog
        - Keyboard navigation: Y/N, Enter/Escape

    Usage:
        def handle_result(confirmed: bool) -> None:
            if confirmed:
                self.do_action()

        self.push_screen(ConfirmDialog("Delete file?"), handle_result)
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", priority=True),
        Binding("enter", "confirm", "Confirm", priority=True),
        Binding("y", "confirm", "Yes"),
        Binding("n", "cancel", "No"),
        Binding("tab", "focus_next", "Next", show=False),
        Binding("shift+tab", "focus_previous", "Previous", show=False),
    ]

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
    }

    ConfirmDialog > Vertical {
        width: 60;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    ConfirmDialog .dialog-title {
        text-align: center;
        text-style: bold;
        color: $text;
        padding: 1 0;
    }

    ConfirmDialog .dialog-message {
        text-align: center;
        color: $text-muted;
        padding: 1 0 2 0;
    }

    ConfirmDialog .dialog-buttons {
        width: 100%;
        height: auto;
        align: center middle;
    }

    ConfirmDialog Button {
        margin: 0 1;
        min-width: 12;
    }
    """

    def __init__(
        self,
        message: str,
        title: str = "Confirm",
        yes_label: str = "Yes",
        no_label: str = "No",
        destructive: bool = False,
    ) -> None:
        super().__init__()
        self.message = message
        self.title = title
        self.yes_label = yes_label
        self.no_label = no_label
        self.destructive = destructive

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog-container"):
            yield Label(self.title, classes="dialog-title", id="dialog-title")
            yield Label(self.message, classes="dialog-message", id="dialog-message")
            with Horizontal(classes="dialog-buttons"):
                variant = "error" if self.destructive else "primary"
                yield Button(self.yes_label, variant=variant, id="yes")
                yield Button(self.no_label, variant="default", id="no")

    def on_mount(self) -> None:
        """Focus the appropriate button on mount."""
        # Focus No button for destructive actions (safer default)
        focus_id = "no" if self.destructive else "yes"
        self.query_one(f"#{focus_id}", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


class AlertDialog(ModalScreen[None]):
    """
    Alert dialog with single OK button.

    Accessibility:
        - role="alertdialog" for screen readers
        - Auto-focus on OK button
        - Simple keyboard dismiss (Enter/Escape)

    Usage:
        self.push_screen(AlertDialog("Operation completed!", "Success"))
    """

    BINDINGS = [
        Binding("escape", "dismiss_dialog", "Close", priority=True),
        Binding("enter", "dismiss_dialog", "OK", priority=True),
    ]

    DEFAULT_CSS = """
    AlertDialog {
        align: center middle;
    }

    AlertDialog > Vertical {
        width: 60;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: thick $accent;
        padding: 1 2;
    }

    AlertDialog .dialog-title {
        text-align: center;
        text-style: bold;
        color: $text;
        padding: 1 0;
    }

    AlertDialog .dialog-message {
        text-align: center;
        color: $text-muted;
        padding: 1 0 2 0;
    }

    AlertDialog .dialog-buttons {
        width: 100%;
        height: auto;
        align: center middle;
    }

    AlertDialog.success .dialog-title {
        color: $success;
    }

    AlertDialog.error .dialog-title {
        color: $error;
    }

    AlertDialog.warning .dialog-title {
        color: $warning;
    }
    """

    def __init__(
        self,
        message: str,
        title: str = "Alert",
        alert_type: str = "info",
    ) -> None:
        super().__init__(classes=alert_type)
        self.message = message
        self.title = title
        self.alert_type = alert_type

    def compose(self) -> ComposeResult:
        icon = self._get_icon()
        with Vertical(id="alert-container"):
            yield Label(f"{icon} {self.title}", classes="dialog-title", id="alert-title")
            yield Label(self.message, classes="dialog-message", id="alert-message")
            with Horizontal(classes="dialog-buttons"):
                yield Button("OK", variant="primary", id="ok")

    def on_mount(self) -> None:
        """Auto-focus OK button."""
        self.query_one("#ok", Button).focus()

    def _get_icon(self) -> str:
        icons = {
            "success": "✓",
            "error": "✗",
            "warning": "⚠",
            "info": "ℹ",
        }
        return icons.get(self.alert_type, "ℹ")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def action_dismiss_dialog(self) -> None:
        self.dismiss(None)


class InputDialog(ModalScreen[Optional[str]]):
    """
    Input dialog with text field.

    Returns the input value or None if cancelled.

    Accessibility:
        - Auto-focus on input field
        - Tab navigation between input and buttons
        - Enter submits, Escape cancels

    Usage:
        def handle_input(value: str | None) -> None:
            if value:
                self.process_name(value)

        self.push_screen(InputDialog("Enter name:"), handle_input)
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", priority=True),
        Binding("tab", "focus_next", "Next", show=False),
        Binding("shift+tab", "focus_previous", "Previous", show=False),
    ]

    DEFAULT_CSS = """
    InputDialog {
        align: center middle;
    }

    InputDialog > Vertical {
        width: 70;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    InputDialog .dialog-title {
        text-align: center;
        text-style: bold;
        color: $text;
        padding: 1 0;
    }

    InputDialog .dialog-prompt {
        color: $text-muted;
        padding: 1 0;
    }

    InputDialog Input {
        margin: 1 0;
    }

    InputDialog .dialog-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    InputDialog Button {
        margin: 0 1;
        min-width: 12;
    }
    """

    def __init__(
        self,
        prompt: str,
        title: str = "Input",
        placeholder: str = "",
        default_value: str = "",
        password: bool = False,
    ) -> None:
        super().__init__()
        self.prompt = prompt
        self.title = title
        self.placeholder = placeholder
        self.default_value = default_value
        self.password = password

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self.title, classes="dialog-title")
            yield Label(self.prompt, classes="dialog-prompt")
            yield Input(
                value=self.default_value,
                placeholder=self.placeholder,
                password=self.password,
                id="input",
            )
            with Horizontal(classes="dialog-buttons"):
                yield Button("OK", variant="primary", id="ok")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            value = self.query_one("#input", Input).value
            self.dismiss(value)
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def action_cancel(self) -> None:
        self.dismiss(None)


class FilePickerDialog(ModalScreen[Optional[Path]]):
    """
    File picker dialog using DirectoryTree.

    Returns the selected path or None if cancelled.

    Accessibility:
        - Arrow key navigation in tree
        - Tab between tree and buttons
        - Enter selects, Escape cancels

    Usage:
        def handle_file(path: Path | None) -> None:
            if path:
                self.open_file(path)

        self.push_screen(FilePickerDialog("/home"), handle_file)
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", priority=True),
        Binding("tab", "focus_next", "Next", show=False),
        Binding("shift+tab", "focus_previous", "Previous", show=False),
    ]

    DEFAULT_CSS = """
    FilePickerDialog {
        align: center middle;
    }

    FilePickerDialog > Vertical {
        width: 80;
        height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    FilePickerDialog .dialog-title {
        text-align: center;
        text-style: bold;
        color: $text;
        padding: 1 0;
        dock: top;
    }

    FilePickerDialog .selected-path {
        color: $accent;
        padding: 0 1;
        height: 1;
        dock: bottom;
        margin-bottom: 3;
    }

    FilePickerDialog DirectoryTree {
        height: 1fr;
        margin: 1 0;
        scrollbar-gutter: stable;
    }

    FilePickerDialog .dialog-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        dock: bottom;
    }

    FilePickerDialog Button {
        margin: 0 1;
        min-width: 12;
    }
    """

    def __init__(
        self,
        root: str = ".",
        title: str = "Select File",
        show_hidden: bool = False,
    ) -> None:
        super().__init__()
        self.root = root
        self.title = title
        self.show_hidden = show_hidden
        self._selected_path: Optional[Path] = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self.title, classes="dialog-title")
            yield DirectoryTree(self.root, id="tree")
            yield Static("No file selected", classes="selected-path", id="selected")
            with Horizontal(classes="dialog-buttons"):
                yield Button("Select", variant="primary", id="select")
                yield Button("Cancel", variant="default", id="cancel")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self._selected_path = event.path
        self.query_one("#selected", Static).update(str(event.path))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "select":
            self.dismiss(self._selected_path)
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class ProgressDialog(ModalScreen[None]):
    """
    Progress dialog with animated indicator.

    Cannot be dismissed by user - must be closed programmatically.

    Accessibility:
        - aria-busy="true" semantics
        - Live region for progress updates
        - Non-dismissible (no keyboard escape)

    Usage:
        dialog = ProgressDialog("Processing...")
        self.push_screen(dialog)
        await self.do_work()
        dialog.dismiss(None)
    """

    # No bindings - cannot be dismissed by user
    BINDINGS = []

    DEFAULT_CSS = """
    ProgressDialog {
        align: center middle;
    }

    ProgressDialog > Vertical {
        width: 50;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 2 3;
    }

    ProgressDialog .dialog-message {
        text-align: center;
        color: $text;
        padding: 1 0;
    }

    ProgressDialog .spinner {
        text-align: center;
        color: $accent;
        padding: 1 0;
    }
    """

    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str = "Loading...") -> None:
        super().__init__()
        self.message = message
        self._frame = 0

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self.SPINNER_FRAMES[0], classes="spinner", id="spinner")
            yield Label(self.message, classes="dialog-message")

    def on_mount(self) -> None:
        self.set_interval(0.1, self._animate)

    def _animate(self) -> None:
        self._frame = (self._frame + 1) % len(self.SPINNER_FRAMES)
        self.query_one("#spinner", Static).update(self.SPINNER_FRAMES[self._frame])

    def update_message(self, message: str) -> None:
        """Update the progress message."""
        self.message = message
        try:
            self.query_one(".dialog-message", Label).update(message)
        except (AttributeError, ValueError):
            pass


# Convenience functions for common dialogs
async def confirm(
    app,
    message: str,
    title: str = "Confirm",
    destructive: bool = False,
) -> bool:
    """
    Show a confirmation dialog and wait for result.

    Usage:
        if await confirm(self.app, "Delete this file?", destructive=True):
            self.delete_file()
    """
    return await app.push_screen_wait(ConfirmDialog(message, title, destructive=destructive))


async def alert(
    app,
    message: str,
    title: str = "Alert",
    alert_type: str = "info",
) -> None:
    """
    Show an alert dialog and wait for dismissal.

    Usage:
        await alert(self.app, "File saved!", "Success", "success")
    """
    await app.push_screen_wait(AlertDialog(message, title, alert_type))


async def prompt(
    app,
    message: str,
    title: str = "Input",
    default: str = "",
) -> Optional[str]:
    """
    Show an input dialog and wait for result.

    Usage:
        name = await prompt(self.app, "Enter your name:")
        if name:
            self.greet(name)
    """
    return await app.push_screen_wait(InputDialog(message, title, default_value=default))


__all__ = [
    "ConfirmDialog",
    "AlertDialog",
    "InputDialog",
    "FilePickerDialog",
    "ProgressDialog",
    "confirm",
    "alert",
    "prompt",
]
