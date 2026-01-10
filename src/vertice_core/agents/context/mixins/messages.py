"""
Message Management Mixin - Handles conversation messages.
"""

import time
from typing import Any, Dict, List


class MessageMixin:
    """Mixin for managing conversation messages."""

    def __init__(self) -> None:
        self._messages: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        message = {
            "role": role,
            "content": content,
            "timestamp": str(time.time()),
        }
        self._messages.append(message)

        # Update token usage
        if hasattr(self, "_token_usage"):
            self._token_usage += len(content) // 4

    def get_messages(self, limit: int = 0) -> List[Dict[str, Any]]:
        """Get conversation messages."""
        if limit <= 0:
            return self._messages.copy()
        return self._messages[-limit:]
