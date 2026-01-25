"""Session manager for persistent shell state.

Deprecated: Use vertice_core.core.session_manager instead.
This module will be removed in v2.0.

Inspired by:
- Claude Code: Persistent Bash sessions with state
- GitHub Codex: PTY session management
- Cursor AI: Context preservation across interactions
"""

import warnings

warnings.warn(
    "vertice_core.integration.session is deprecated. "
    "Use vertice_core.core.session_manager instead. "
    "This module will be removed in v2.0.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from canonical location
from vertice_core.core.session_manager import (
    SessionManager,
    SessionSnapshot as Session,  # Session is now SessionSnapshot
    get_session_manager,
)


# Legacy singleton for backward compatibility
def _get_legacy_session_manager() -> SessionManager:
    """Get legacy session manager singleton."""
    return get_session_manager()


session_manager = _get_legacy_session_manager()


__all__ = [
    "Session",
    "SessionManager",
    "session_manager",
    "get_session_manager",
]
