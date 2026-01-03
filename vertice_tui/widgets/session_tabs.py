"""
Session Tabs - Multiple chat sessions with TabbedContent.

Uses Textual's TabbedContent for session management:
- Multiple chat sessions
- Dynamic tab creation/removal
- Session persistence
- Tab close button

Phase 11: Visual Upgrade - Layout & Navigation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, ClassVar
from uuid import uuid4

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Static, TabbedContent, TabPane, ContentSwitcher
from textual.reactive import reactive
from textual.widget import Widget
from textual.message import Message


@dataclass
class SessionData:
    """Data for a single chat session."""
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    title: str = "New Chat"
    created_at: datetime = field(default_factory=datetime.now)
    messages: List[Dict] = field(default_factory=list)
    context: Dict = field(default_factory=dict)

    @property
    def display_title(self) -> str:
        """Get display title (truncated)."""
        if len(self.title) > 20:
            return self.title[:17] + "..."
        return self.title


class SessionPane(TabPane):
    """Individual session tab pane."""

    DEFAULT_CSS = """
    SessionPane {
        width: 100%;
        height: 100%;
    }
    """

    def __init__(
        self,
        session: SessionData,
        *children,
        id: Optional[str] = None,
    ) -> None:
        self.session = session
        super().__init__(
            session.display_title,
            *children,
            id=id or f"session-{session.id}",
        )


class SessionTabs(Widget):
    """
    Multi-session tab manager with TabbedContent.

    Features:
    - Create new sessions (Ctrl+N)
    - Close sessions (Ctrl+W)
    - Switch sessions (Ctrl+Tab)
    - Session data persistence
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+n", "new_session", "New Session", show=True),
        Binding("ctrl+w", "close_session", "Close Session", show=False),
        Binding("ctrl+tab", "next_session", "Next Session", show=False),
        Binding("ctrl+shift+tab", "prev_session", "Previous Session", show=False),
    ]

    DEFAULT_CSS = """
    SessionTabs {
        width: 100%;
        height: 100%;
    }

    SessionTabs TabbedContent {
        width: 100%;
        height: 100%;
    }

    SessionTabs TabPane {
        width: 100%;
        height: 100%;
        padding: 0;
    }

    SessionTabs .session-content {
        width: 100%;
        height: 100%;
    }
    """

    active_session_id: reactive[str] = reactive("")

    class SessionCreated(Message):
        """New session was created."""
        def __init__(self, session: SessionData) -> None:
            self.session = session
            super().__init__()

    class SessionClosed(Message):
        """Session was closed."""
        def __init__(self, session_id: str) -> None:
            self.session_id = session_id
            super().__init__()

    class SessionActivated(Message):
        """Session was activated."""
        def __init__(self, session: SessionData) -> None:
            self.session = session
            super().__init__()

    def __init__(self, id: Optional[str] = None) -> None:
        super().__init__(id=id)
        self._sessions: Dict[str, SessionData] = {}
        self._tabbed_content: Optional[TabbedContent] = None

    def compose(self) -> ComposeResult:
        self._tabbed_content = TabbedContent(id="session-tabs")
        yield self._tabbed_content

    def on_mount(self) -> None:
        # Create initial session
        self.create_session("Chat 1")

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        """Handle tab activation."""
        pane = event.pane
        if isinstance(pane, SessionPane):
            self.active_session_id = pane.session.id
            self.post_message(self.SessionActivated(pane.session))

    @property
    def active_session(self) -> Optional[SessionData]:
        """Get currently active session."""
        return self._sessions.get(self.active_session_id)

    @property
    def session_count(self) -> int:
        """Get number of sessions."""
        return len(self._sessions)

    def create_session(self, title: str = "New Chat") -> SessionData:
        """Create a new session tab."""
        session = SessionData(title=title)
        self._sessions[session.id] = session

        # Create pane with placeholder content
        pane = SessionPane(
            session,
            Vertical(
                Static(f"Session: {session.title}", classes="session-content"),
                id=f"content-{session.id}",
            ),
        )

        if self._tabbed_content:
            self._tabbed_content.add_pane(pane)
            self._tabbed_content.active = pane.id

        self.active_session_id = session.id
        self.post_message(self.SessionCreated(session))
        return session

    def close_session(self, session_id: Optional[str] = None) -> bool:
        """Close a session tab."""
        session_id = session_id or self.active_session_id

        if not session_id or session_id not in self._sessions:
            return False

        # Don't close last session
        if len(self._sessions) <= 1:
            try:
                self.app.notify("Cannot close last session", severity="warning")
            except Exception:
                pass
            return False

        # Remove from tabs
        if self._tabbed_content:
            try:
                self._tabbed_content.remove_pane(f"session-{session_id}")
            except Exception:
                pass

        # Remove from sessions
        del self._sessions[session_id]
        self.post_message(self.SessionClosed(session_id))

        return True

    def rename_session(self, session_id: str, new_title: str) -> bool:
        """Rename a session."""
        if session_id not in self._sessions:
            return False

        session = self._sessions[session_id]
        session.title = new_title

        # Update tab title
        if self._tabbed_content:
            try:
                tab = self._tabbed_content.get_tab(f"session-{session_id}")
                tab.label = session.display_title
            except Exception:
                pass

        return True

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session by ID."""
        return self._sessions.get(session_id)

    def get_all_sessions(self) -> List[SessionData]:
        """Get all sessions."""
        return list(self._sessions.values())

    def action_new_session(self) -> None:
        """Create new session action."""
        count = len(self._sessions) + 1
        self.create_session(f"Chat {count}")

    def action_close_session(self) -> None:
        """Close current session action."""
        self.close_session()

    def action_next_session(self) -> None:
        """Switch to next session."""
        if not self._tabbed_content:
            return

        sessions = list(self._sessions.keys())
        if len(sessions) <= 1:
            return

        try:
            current_idx = sessions.index(self.active_session_id)
            next_idx = (current_idx + 1) % len(sessions)
            next_id = sessions[next_idx]
            self._tabbed_content.active = f"session-{next_id}"
        except (ValueError, IndexError):
            pass

    def action_prev_session(self) -> None:
        """Switch to previous session."""
        if not self._tabbed_content:
            return

        sessions = list(self._sessions.keys())
        if len(sessions) <= 1:
            return

        try:
            current_idx = sessions.index(self.active_session_id)
            prev_idx = (current_idx - 1) % len(sessions)
            prev_id = sessions[prev_idx]
            self._tabbed_content.active = f"session-{prev_id}"
        except (ValueError, IndexError):
            pass

    def add_message_to_session(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """Add message to session history."""
        if session_id in self._sessions:
            self._sessions[session_id].messages.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            })

    def get_session_messages(self, session_id: str) -> List[Dict]:
        """Get messages for a session."""
        if session_id in self._sessions:
            return self._sessions[session_id].messages
        return []

    def export_sessions(self) -> Dict:
        """Export all sessions data."""
        return {
            session_id: {
                "id": session.id,
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "messages": session.messages,
                "context": session.context,
            }
            for session_id, session in self._sessions.items()
        }
