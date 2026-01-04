"""
SessionManager - Session Persistence and Crash Recovery

Core session management class.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .types import (
    ConversationMessage,
    SessionInfo,
    SessionSnapshot,
    SessionState,
)
from .storage import (
    get_session_path,
    load_index,
    load_session,
    save_session,
    update_index,
)

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Session persistence and crash recovery manager.

    Features:
    - Auto-save at configurable intervals
    - Checksum verification for corruption detection
    - Automatic crash recovery
    - Session history with search
    - Compression for storage efficiency

    Usage:
        manager = SessionManager()
        session = manager.start_session()
        manager.add_message("user", "Hello")
        manager.save()
    """

    SESSION_DIR = ".vertice/sessions"
    CURRENT_SESSION_FILE = "current_session.json"
    INDEX_FILE = "sessions_index.json"
    AUTO_SAVE_INTERVAL = 30  # seconds
    MAX_SESSIONS = 50  # Keep last N sessions
    COMPRESSION_THRESHOLD = 10 * 1024  # Compress if > 10KB

    def __init__(
        self,
        session_dir: Optional[str] = None,
        auto_save_interval: float = AUTO_SAVE_INTERVAL,
        enable_compression: bool = True,
        max_sessions: int = MAX_SESSIONS,
    ):
        """Initialize SessionManager."""
        self.session_dir = Path(session_dir or self.SESSION_DIR)
        self.auto_save_interval = auto_save_interval
        self.enable_compression = enable_compression
        self.max_sessions = max_sessions

        self._current_session: Optional[SessionSnapshot] = None
        self._dirty = False
        self._last_save = time.time()
        self._auto_save_thread: Optional[threading.Thread] = None
        self._stop_auto_save = threading.Event()

        # Ensure session directory exists
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = hashlib.md5(str(time.time()).encode()).hexdigest()[:6]
        return f"session_{timestamp}_{random_suffix}"

    def _get_session_path(self, session_id: str) -> Path:
        """Get path for session file."""
        return get_session_path(self.session_dir, session_id, self.enable_compression)

    def _auto_save_loop(self) -> None:
        """Background thread for auto-saving."""
        while not self._stop_auto_save.wait(self.auto_save_interval):
            if self._dirty and self._current_session:
                self.save()

    def _start_auto_save(self) -> None:
        """Start auto-save background thread."""
        if self._auto_save_thread is None or not self._auto_save_thread.is_alive():
            self._stop_auto_save.clear()
            self._auto_save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)
            self._auto_save_thread.start()

    def _stop_auto_save_thread(self) -> None:
        """Stop auto-save background thread."""
        self._stop_auto_save.set()
        if self._auto_save_thread:
            self._auto_save_thread.join(timeout=1)

    def _generate_summary(self) -> str:
        """Generate brief summary of session."""
        if not self._current_session:
            return ""

        messages = self._current_session.messages
        if not messages:
            return "Empty session"

        # Get first user message as summary
        for msg in messages:
            if msg.role == "user":
                content = msg.content.strip()
                if len(content) > 100:
                    return content[:97] + "..."
                return content

        return f"{len(messages)} messages"

    def start_session(
        self,
        working_directory: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> SessionSnapshot:
        """Start a new session."""
        session_id = self._generate_session_id()
        now = time.time()

        self._current_session = SessionSnapshot(
            session_id=session_id,
            state=SessionState.ACTIVE,
            created_at=now,
            updated_at=now,
            checksum="",
            messages=[],
            context=context or {},
            working_directory=working_directory or os.getcwd(),
            open_files=[],
            pending_operations=[],
        )

        self._dirty = True
        self.save()
        self._start_auto_save()

        logger.info(f"Started new session: {session_id}")
        return self._current_session

    def resume_session(self, session_id: str) -> Optional[SessionSnapshot]:
        """Resume an existing session."""
        path = self._get_session_path(session_id)
        session = load_session(path)

        if session:
            session.state = SessionState.RECOVERED
            session.updated_at = time.time()
            self._current_session = session
            self._dirty = True
            self._start_auto_save()

            logger.info(f"Resumed session: {session_id}")
            return session

        return None

    def resume_latest(self) -> Optional[SessionSnapshot]:
        """Resume the most recent session."""
        sessions = self.list_sessions()
        if sessions:
            latest = max(sessions, key=lambda s: s.updated_at)
            return self.resume_session(latest.session_id)
        return None

    def check_for_crash_recovery(self) -> Optional[SessionSnapshot]:
        """Check for crashed session and offer recovery."""
        current_path = self.session_dir / self.CURRENT_SESSION_FILE

        if current_path.exists():
            try:
                data = json.loads(current_path.read_text())
                session_id = data.get("session_id")

                if session_id:
                    path = self._get_session_path(session_id)
                    session = load_session(path)

                    if session and session.state == SessionState.ACTIVE:
                        session.state = SessionState.CRASHED
                        logger.warning(f"Found crashed session: {session_id}")
                        return session

            except Exception as e:
                logger.debug(f"No crash recovery needed: {e}")

        return None

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a message to the current session."""
        if not self._current_session:
            raise RuntimeError("No active session")

        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {},
        )

        self._current_session.messages.append(message)
        self._current_session.updated_at = time.time()
        self._dirty = True

    def update_context(self, key: str, value: Any) -> None:
        """Update session context."""
        if not self._current_session:
            raise RuntimeError("No active session")

        self._current_session.context[key] = value
        self._current_session.updated_at = time.time()
        self._dirty = True

    def add_pending_operation(self, operation: Dict[str, Any]) -> None:
        """Add a pending operation (for crash recovery)."""
        if not self._current_session:
            return

        self._current_session.pending_operations.append(operation)
        self._dirty = True

    def clear_pending_operations(self) -> List[Dict[str, Any]]:
        """Clear and return pending operations."""
        if not self._current_session:
            return []

        operations = self._current_session.pending_operations
        self._current_session.pending_operations = []
        self._dirty = True

        return operations

    def _mark_dirty(self) -> None:
        """Mark session as dirty (needs save)."""
        self._current_session.updated_at = time.time()
        self._dirty = True

    def track_file_operation(self, operation: str, path: str) -> None:
        """Track file operations for session history.

        Args:
            operation: One of 'read', 'modify', 'delete'
            path: Absolute path to the file
        """
        if not self._current_session:
            return

        if operation == "read":
            self._current_session.read_files.add(path)
        elif operation == "modify":
            self._current_session.modified_files.add(path)
        elif operation == "delete":
            self._current_session.deleted_files.add(path)

        self._mark_dirty()

    def capture_environment(self) -> None:
        """Capture current environment variables."""
        if self._current_session:
            self._current_session.environment_snapshot = dict(os.environ)

    def get_file_stats(self) -> Dict[str, int]:
        """Get file operation statistics."""
        if not self._current_session:
            return {"read": 0, "modified": 0, "deleted": 0}
        return {
            "read": len(self._current_session.read_files),
            "modified": len(self._current_session.modified_files),
            "deleted": len(self._current_session.deleted_files),
        }

    def save(self) -> bool:
        """Save current session to disk."""
        if not self._current_session:
            return False

        self._current_session.updated_at = time.time()

        # Save session file
        path = self._get_session_path(self._current_session.session_id)
        if not save_session(
            self._current_session,
            path,
            self.enable_compression,
            self.COMPRESSION_THRESHOLD,
        ):
            return False

        # Update current session marker
        current_path = self.session_dir / self.CURRENT_SESSION_FILE
        current_data = {
            "session_id": self._current_session.session_id,
            "updated_at": self._current_session.updated_at,
        }
        current_path.write_text(json.dumps(current_data))

        # Update index
        summary = self._generate_summary()
        info = SessionInfo(
            session_id=self._current_session.session_id,
            state=self._current_session.state,
            created_at=self._current_session.created_at,
            updated_at=self._current_session.updated_at,
            message_count=len(self._current_session.messages),
            working_directory=self._current_session.working_directory,
            summary=summary,
        )
        update_index(self.session_dir, self.INDEX_FILE, info, self.max_sessions)

        self._dirty = False
        self._last_save = time.time()

        return True

    def end_session(self) -> None:
        """End the current session gracefully."""
        if self._current_session:
            self._current_session.state = SessionState.COMPLETED
            self._current_session.updated_at = time.time()
            self.save()

            # Remove current session marker
            current_path = self.session_dir / self.CURRENT_SESSION_FILE
            if current_path.exists():
                current_path.unlink()

            self._stop_auto_save_thread()
            self._current_session = None

    def list_sessions(self, limit: int = 20) -> List[SessionInfo]:
        """List recent sessions."""
        index = load_index(self.session_dir, self.INDEX_FILE)

        if not index:
            return []

        sessions = [
            SessionInfo(
                session_id=sid,
                state=SessionState(data["state"]),
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                message_count=data["message_count"],
                working_directory=data["working_directory"],
                summary=data["summary"],
            )
            for sid, data in index.items()
        ]

        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions[:limit]

    def search_sessions(self, query: str, limit: int = 10) -> List[SessionInfo]:
        """Search sessions by content."""
        query_lower = query.lower()
        results = []

        for session_info in self.list_sessions(limit=100):
            # Check summary
            if query_lower in session_info.summary.lower():
                results.append(session_info)
                continue

            # Load full session and search messages
            path = self._get_session_path(session_info.session_id)
            session = load_session(path)

            if session:
                for msg in session.messages:
                    if query_lower in msg.content.lower():
                        results.append(session_info)
                        break

            if len(results) >= limit:
                break

        return results

    def get_messages(
        self,
        limit: Optional[int] = None,
        since: Optional[float] = None,
    ) -> List[ConversationMessage]:
        """Get messages from current session."""
        if not self._current_session:
            return []

        messages = self._current_session.messages

        if since:
            messages = [m for m in messages if m.timestamp >= since]

        if limit:
            messages = messages[-limit:]

        return messages

    @property
    def current_session(self) -> Optional[SessionSnapshot]:
        """Get current session."""
        return self._current_session

    @property
    def is_active(self) -> bool:
        """Check if there's an active session."""
        return self._current_session is not None


__all__ = ["SessionManager"]
