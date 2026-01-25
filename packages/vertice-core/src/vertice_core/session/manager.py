"""Session manager for persistence and resumption.

Deprecated: Use vertice_core.core.session_manager instead.
This module will be removed in v2.0.
"""

import warnings

warnings.warn(
    "vertice_core.session.manager is deprecated. "
    "Use vertice_core.core.session_manager instead. "
    "This module will be removed in v2.0.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from canonical location
from vertice_core.core.session_manager import (
    SessionManager,
    SessionState,
    SessionSnapshot,
)

# Re-export SessionState from .state for compatibility
from .state import SessionState as LegacySessionState


def get_session_manager() -> SessionManager:
    """Get the default session manager singleton."""
    from vertice_core.core.session_manager import get_session_manager as _get

    return _get()


__all__ = [
    "SessionManager",
    "SessionState",
    "SessionSnapshot",
    "LegacySessionState",
    "get_session_manager",
]
