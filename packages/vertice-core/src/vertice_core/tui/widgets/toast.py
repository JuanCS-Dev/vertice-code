"""
Toast Helpers - VERTICE TUI Visual Upgrade.

Simple wrappers around Textual's built-in notify() system.
Textual already handles: positioning, stacking, auto-dismiss, styling.

Phase 11: Visual Upgrade Sprint 1.

References:
- https://textual.textualize.io/widgets/toast/
"""

from __future__ import annotations

from typing import Optional


def toast_success(app, message: str, title: str = "Success", timeout: float = 3.0) -> None:
    """Show a success notification."""
    app.notify(f"✓ {message}", title=title, timeout=timeout)


def toast_error(app, message: str, title: str = "Error", timeout: float = 6.0) -> None:
    """Show an error notification."""
    app.notify(message, title=title, severity="error", timeout=timeout)


def toast_warning(app, message: str, title: str = "Warning", timeout: float = 5.0) -> None:
    """Show a warning notification."""
    app.notify(message, title=title, severity="warning", timeout=timeout)


def toast_info(app, message: str, title: Optional[str] = None, timeout: float = 4.0) -> None:
    """Show an info notification."""
    app.notify(message, title=title, timeout=timeout)


def toast_copied(app, what: str = "Copied to clipboard") -> None:
    """Special toast for copy operations."""
    app.notify(f"✓ {what}", title="Copied!", timeout=2.0)


class ToastMixin:
    """
    Mixin to add convenient toast methods to any Textual App.

    Usage:
        class MyApp(App, ToastMixin):
            def some_action(self):
                self.toast_success("Done!")
    """

    def toast_success(self, message: str, title: str = "Success") -> None:
        toast_success(self, message, title)

    def toast_error(self, message: str, title: str = "Error") -> None:
        toast_error(self, message, title)

    def toast_warning(self, message: str, title: str = "Warning") -> None:
        toast_warning(self, message, title)

    def toast_info(self, message: str, title: Optional[str] = None) -> None:
        toast_info(self, message, title)

    def toast_copied(self, what: str = "Copied to clipboard") -> None:
        toast_copied(self, what)


__all__ = [
    "toast_success",
    "toast_error",
    "toast_warning",
    "toast_info",
    "toast_copied",
    "ToastMixin",
]
