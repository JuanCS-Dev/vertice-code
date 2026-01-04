"""
Working Memory - Ephemeral task context.

Active task context that is session-scoped and not persisted.
Stores current task state, active context, and intermediate results.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class WorkingMemory:
    """
    Active task context - ephemeral, session-scoped.

    Stores current task state, active context, and
    intermediate results during task execution.
    """

    def __init__(self) -> None:
        self._context: Dict[str, Any] = {}
        self._active_task: Optional[str] = None
        self._stack: List[Dict[str, Any]] = []

    def set_context(self, key: str, value: Any) -> None:
        """Set a context value."""
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a context value."""
        return self._context.get(key, default)

    def set_active_task(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """Set the currently active task."""
        self._active_task = task_id
        self._context["current_task"] = task_data

    def get_active_task(self) -> Optional[str]:
        """Get the currently active task ID."""
        return self._active_task

    def push(self, frame: Dict[str, Any]) -> None:
        """Push a context frame onto the stack."""
        self._stack.append(frame)

    def pop(self) -> Optional[Dict[str, Any]]:
        """Pop a context frame from the stack."""
        return self._stack.pop() if self._stack else None

    def peek(self) -> Optional[Dict[str, Any]]:
        """Peek at the top context frame without popping."""
        return self._stack[-1] if self._stack else None

    def clear(self) -> None:
        """Clear working memory."""
        self._context.clear()
        self._active_task = None
        self._stack.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Export working memory state."""
        return {
            "context": self._context.copy(),
            "active_task": self._active_task,
            "stack_depth": len(self._stack),
        }
