"""
Session Manager Module - Session Persistence and Crash Recovery.

This package provides session management for qwen-dev-cli.

Submodules:
    - types: Domain models (SessionState, SessionSnapshot, etc.)
    - storage: I/O operations for session files
    - manager: SessionManager class

Usage:
    from vertice_core.core.session_manager import SessionManager, start_session
    from vertice_core.core.session_manager import SessionState, SessionSnapshot
"""

from __future__ import annotations

from typing import Optional

from .types import (
    SessionState,
    ConversationMessage,
    SessionSnapshot,
    SessionInfo,
)
from .manager import SessionManager


# Global instance
_default_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the default session manager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = SessionManager()
    return _default_manager


# Convenience functions


def start_session(**kwargs) -> SessionSnapshot:
    """Start a new session."""
    return get_session_manager().start_session(**kwargs)


def resume_session(session_id: str) -> Optional[SessionSnapshot]:
    """Resume an existing session."""
    return get_session_manager().resume_session(session_id)


def add_message(role: str, content: str, **kwargs) -> None:
    """Add a message to the current session."""
    get_session_manager().add_message(role, content, **kwargs)


def save_session() -> bool:
    """Save the current session."""
    return get_session_manager().save()


def end_session() -> None:
    """End the current session."""
    get_session_manager().end_session()


# Export all public symbols
__all__ = [
    # Types
    "SessionState",
    "ConversationMessage",
    "SessionSnapshot",
    "SessionInfo",
    # Manager
    "SessionManager",
    # Singleton
    "get_session_manager",
    # Convenience functions
    "start_session",
    "resume_session",
    "add_message",
    "save_session",
    "end_session",
]
