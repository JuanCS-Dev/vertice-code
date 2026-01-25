"""
JulesMonitorWidget - TUI observability for Google Jules sessions.

Features:
- Real-time session status (reactive attributes)
- Activity log with auto-scroll
- Plan approval integration
- Worker-based polling (non-blocking)
- Sidebar collapsible design

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable, Coroutine, List, Optional, Any

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Button, Label, RichLog, Static

from rich.text import Text

from vertice_core.types.jules_types import (
    JulesActivity,
    JulesActivityType,
    JulesSession,
    JulesSessionState,
)

# Logger
logger = logging.getLogger(__name__)

# Type aliases
GetSessionFn = Callable[[], Coroutine[Any, Any, JulesSession]]
GetActivitiesFn = Callable[[], Coroutine[Any, Any, List[JulesActivity]]]


class JulesMonitorWidget(Widget):
    """
    Widget for monitoring a Jules session.

    Features:
    - Real-time status display (reactive)
    - Activity log with auto-scroll
    - Plan approval button
    - Polling-based updates
    - Collapsible sidebar mode

    Usage:
        monitor = JulesMonitorWidget()
        monitor.set_session(session)
        monitor.start_polling(
            lambda: client.get_session(session_id),
            lambda: client.get_activities(session_id)
        )
    """

    # Reactive attributes for automatic UI updates
    session_state: reactive[str] = reactive("UNKNOWN")
    session_title: reactive[str] = reactive("No Session")
    activity_count: reactive[int] = reactive(0)
    last_update: reactive[str] = reactive("")
    plan_pending: reactive[bool] = reactive(False)
    collapsed: reactive[bool] = reactive(False)

    # Messages
    class PlanApprovalRequested(Message):
        """User wants to approve the plan."""

        def __init__(self, session_id: str) -> None:
            self.session_id = session_id
            super().__init__()

    class SessionUpdated(Message):
        """Session state changed."""

        def __init__(self, session: JulesSession) -> None:
            self.session = session
            super().__init__()

    class SessionCompleted(Message):
        """Session finished (completed, failed, or cancelled)."""

        def __init__(self, session: JulesSession) -> None:
            self.session = session
            super().__init__()

    DEFAULT_CSS = """
    JulesMonitorWidget {
        width: 100%;
        height: auto;
        min-height: 4;
        background: $surface;
        border: solid $primary;
        padding: 0 1;
    }

    JulesMonitorWidget.collapsed {
        min-height: 3;
        max-height: 3;
    }

    JulesMonitorWidget .header {
        height: 3;
        background: $panel;
        padding: 0 1;
    }

    JulesMonitorWidget .header-title {
        text-style: bold;
        color: $accent;
    }

    JulesMonitorWidget .header-state {
        text-align: right;
    }

    JulesMonitorWidget .state-queued { color: #64748B; }
    JulesMonitorWidget .state-planning { color: #3B82F6; }
    JulesMonitorWidget .state-awaiting { color: #F59E0B; }
    JulesMonitorWidget .state-progress { color: #8B5CF6; }
    JulesMonitorWidget .state-completed { color: #22C55E; }
    JulesMonitorWidget .state-failed { color: #EF4444; }

    JulesMonitorWidget .activity-log {
        height: 12;
        margin: 1 0;
        border: solid $border;
    }

    JulesMonitorWidget.collapsed .activity-log {
        display: none;
    }

    JulesMonitorWidget .controls {
        height: 3;
        align: center middle;
    }

    JulesMonitorWidget.collapsed .controls {
        display: none;
    }

    JulesMonitorWidget Button {
        margin: 0 1;
        min-width: 12;
    }

    JulesMonitorWidget Button.approve {
        background: $success;
    }

    JulesMonitorWidget .footer {
        height: 1;
        color: $text-muted;
    }

    JulesMonitorWidget.collapsed .footer {
        display: none;
    }

    JulesMonitorWidget .compact-status {
        display: none;
    }

    JulesMonitorWidget.collapsed .compact-status {
        display: block;
        height: 1;
    }
    """

    BINDINGS = [
        ("ctrl+shift+j", "toggle_collapse", "Toggle Jules Monitor"),
    ]

    def __init__(
        self,
        session: Optional[JulesSession] = None,
        id: Optional[str] = None,
        collapsed: bool = False,
    ) -> None:
        super().__init__(id=id)
        self._session = session
        self._activities: List[JulesActivity] = []
        self._poll_timer: Optional[Timer] = None
        self._get_session_fn: Optional[GetSessionFn] = None
        self._get_activities_fn: Optional[GetActivitiesFn] = None
        self.collapsed = collapsed

        if session:
            self._update_from_session(session)

    def compose(self) -> ComposeResult:
        with Vertical():
            # Header (always visible)
            with Horizontal(classes="header"):
                yield Label(self.session_title, classes="header-title", id="title")
                yield Static(self._format_state(), classes="header-state", id="state")

            # Compact status (collapsed mode)
            yield Static(
                self._format_compact_status(),
                classes="compact-status",
                id="compact",
            )

            # Activity log (expanded mode)
            yield RichLog(
                classes="activity-log",
                id="log",
                highlight=True,
                markup=True,
                auto_scroll=True,
            )

            # Controls (expanded mode)
            with Horizontal(classes="controls"):
                yield Button(
                    "Approve Plan",
                    id="approve",
                    classes="approve",
                    disabled=not self.plan_pending,
                )
                yield Button("Refresh", id="refresh")
                yield Button("Close", id="close", variant="error")

            # Footer (expanded mode)
            yield Static(self.last_update, classes="footer", id="footer")

    def _format_state(self) -> Text:
        """Format state with color."""
        state_config = {
            "QUEUED": ("dim", "state-queued", "Queued"),
            "PLANNING": ("blue", "state-planning", "Planning"),
            "AWAITING_PLAN_APPROVAL": ("yellow", "state-awaiting", "Awaiting"),
            "IN_PROGRESS": ("magenta", "state-progress", "Running"),
            "COMPLETED": ("green", "state-completed", "Done"),
            "FAILED": ("red", "state-failed", "Failed"),
            "CANCELLED": ("red", "state-failed", "Cancelled"),
        }

        color, cls, label = state_config.get(self.session_state, ("white", "", self.session_state))

        icon = {
            "QUEUED": "",
            "PLANNING": "",
            "AWAITING_PLAN_APPROVAL": "",
            "IN_PROGRESS": "",
            "COMPLETED": "",
            "FAILED": "",
            "CANCELLED": "",
        }.get(self.session_state, "")

        return Text(f"{icon} {label}", style=color)

    def _format_compact_status(self) -> str:
        """Format compact status for collapsed mode."""
        icon = {
            "QUEUED": "",
            "PLANNING": "",
            "AWAITING_PLAN_APPROVAL": "",
            "IN_PROGRESS": "",
            "COMPLETED": "",
            "FAILED": "",
        }.get(self.session_state, "")

        return f"{icon} {self.activity_count} activities | {self.last_update}"

    def set_session(self, session: JulesSession) -> None:
        """Update monitored session."""
        self._session = session
        self._update_from_session(session)

    def _update_from_session(self, session: JulesSession) -> None:
        """Update reactive attributes from session."""
        self.session_state = session.state.value
        self.session_title = session.title or f"Jules {session.session_id[:8]}"
        self.plan_pending = session.state == JulesSessionState.AWAITING_PLAN_APPROVAL
        self.last_update = datetime.now().strftime("%H:%M:%S")

        # Update CSS class for collapsed state
        if self.collapsed:
            self.add_class("collapsed")
        else:
            self.remove_class("collapsed")

        # Post message
        self.post_message(self.SessionUpdated(session))

        # Check completion
        if session.state in (
            JulesSessionState.COMPLETED,
            JulesSessionState.FAILED,
        ):
            self.post_message(self.SessionCompleted(session))

    def add_activity(self, activity: JulesActivity) -> None:
        """Add activity to log."""
        self._activities.append(activity)
        self.activity_count = len(self._activities)

        # Format and add to log
        try:
            log = self.query_one("#log", RichLog)
            text = self._format_activity(activity)
            log.write(text)
        except Exception as e:
            logger.debug(f"Could not write to log, widget not ready: {e}")

    def _format_activity(self, activity: JulesActivity) -> Text:
        """Format activity for display (v1alpha types)."""
        icons = {
            JulesActivityType.PLAN_GENERATED: ("", "yellow"),
            JulesActivityType.PLAN_APPROVED: ("", "green"),
            JulesActivityType.PROGRESS_UPDATED: ("", "blue"),
            JulesActivityType.SESSION_COMPLETED: ("", "green"),
            JulesActivityType.SESSION_FAILED: ("", "red"),
            JulesActivityType.USER_MESSAGED: ("", "magenta"),
            JulesActivityType.AGENT_MESSAGED: ("", "cyan"),
        }

        icon, color = icons.get(activity.type, ("", "white"))
        time_str = activity.timestamp.strftime("%H:%M:%S")
        message = activity.message or str(activity.data)[:80]

        text = Text()
        text.append(f"[{time_str}] ", style="dim")
        text.append(f"{icon} ", style=color)
        text.append(message, style="white")

        return text

    def start_polling(
        self,
        get_session: GetSessionFn,
        get_activities: GetActivitiesFn,
        interval: float = 5.0,
    ) -> None:
        """Start polling for updates.

        Args:
            get_session: Async function to fetch session
            get_activities: Async function to fetch activities
            interval: Poll interval in seconds
        """
        self._get_session_fn = get_session
        self._get_activities_fn = get_activities
        self._poll_timer = self.set_interval(interval, self._poll_updates)

    def stop_polling(self) -> None:
        """Stop polling."""
        if self._poll_timer:
            self._poll_timer.stop()
            self._poll_timer = None

    async def _poll_updates(self) -> None:
        """Poll for session and activity updates."""
        if not self._get_session_fn or not self._get_activities_fn:
            return

        try:
            # Fetch session
            session = await self._get_session_fn()
            self._update_from_session(session)

            # Fetch new activities
            activities = await self._get_activities_fn()
            seen_ids = {a.activity_id for a in self._activities}

            for activity in activities:
                if activity.activity_id not in seen_ids:
                    self.add_activity(activity)

            # Stop polling if session completed
            if session.state in (
                JulesSessionState.COMPLETED,
                JulesSessionState.FAILED,
            ):
                self.stop_polling()

        except Exception as e:
            # Log error as activity
            self.add_activity(
                JulesActivity(
                    activity_id=f"error-{datetime.now().timestamp()}",
                    type=JulesActivityType.SESSION_FAILED,
                    timestamp=datetime.now(),
                    message=f"Poll error: {e}",
                )
            )

    # Watchers
    def watch_session_state(self, value: str) -> None:
        """Update state display when state changes."""
        try:
            self.query_one("#state", Static).update(self._format_state())
            self.query_one("#compact", Static).update(self._format_compact_status())
        except Exception as e:
            logger.warning(f"Failed to update session state display: {e}", exc_info=True)

    def watch_session_title(self, value: str) -> None:
        """Update title when it changes."""
        try:
            self.query_one("#title", Label).update(value)
        except Exception as e:
            logger.warning(f"Failed to update session title: {e}", exc_info=True)

    def watch_plan_pending(self, value: bool) -> None:
        """Enable/disable approve button."""
        try:
            self.query_one("#approve", Button).disabled = not value
        except Exception as e:
            logger.warning(f"Failed to update approve button state: {e}", exc_info=True)

    def watch_last_update(self, value: str) -> None:
        """Update footer."""
        try:
            self.query_one("#footer", Static).update(f"Updated: {value}")
            self.query_one("#compact", Static).update(self._format_compact_status())
        except Exception as e:
            logger.warning(f"Failed to update footer: {e}", exc_info=True)

    def watch_collapsed(self, value: bool) -> None:
        """Toggle collapsed state."""
        if value:
            self.add_class("collapsed")
        else:
            self.remove_class("collapsed")

    # Actions
    def action_toggle_collapse(self) -> None:
        """Toggle collapsed state."""
        self.collapsed = not self.collapsed

    # Button handlers
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "approve" and self._session:
            self.post_message(self.PlanApprovalRequested(self._session.session_id))
        elif event.button.id == "refresh":
            self.call_later(self._poll_updates)
        elif event.button.id == "close":
            self.stop_polling()
            self.remove()

    def on_unmount(self) -> None:
        """Clean up when widget is removed."""
        self.stop_polling()


__all__ = ["JulesMonitorWidget"]
