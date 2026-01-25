"""
Context Variables Mixin - Manages context variables (Swarm pattern).
"""

from typing import Any, Dict


class ContextVariablesMixin:
    """Mixin for managing context variables."""

    def __init__(self) -> None:
        self._variables: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a context variable."""
        return self._variables.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a context variable."""
        self._variables[key] = value

    def update(self, variables: Dict[str, Any]) -> None:
        """Update multiple context variables."""
        self._variables.update(variables)

    def delete(self, key: str) -> bool:
        """Delete a context variable."""
        if key in self._variables:
            del self._variables[key]
            return True
        return False

    def variables(self) -> Dict[str, Any]:
        """Get all context variables."""
        return self._variables.copy()
