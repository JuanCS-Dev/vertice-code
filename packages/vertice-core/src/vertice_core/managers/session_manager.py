"""
Session Manager - DEPRECATED.

Deprecated: Use vertice_core.core.session_manager instead.
This module will be removed in v2.0.

SCALE & SUSTAIN Phase 1.1.3 - Session Manager (Legacy Bridge).
"""

import warnings

warnings.warn(
    "vertice_core.managers.session_manager is deprecated. "
    "Use vertice_core.core.session_manager instead. "
    "This module will be removed in v2.0.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from canonical location for backward compatibility
from vertice_core.core.session_manager import (
    SessionManager,
    SessionState,
    SessionSnapshot,
    ConversationMessage,
)

# Legacy types kept for compatibility
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SessionConfig:
    """Session configuration (deprecated - use SessionSnapshot.metadata)."""

    auto_save: bool = True
    save_interval: int = 60
    history_limit: int = 100
    context_window: int = 8192
    persist_path: Optional[Path] = None


__all__ = [
    "SessionManager",
    "SessionState",
    "SessionConfig",
    "SessionSnapshot",
    "ConversationMessage",
]
