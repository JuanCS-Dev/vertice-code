"""Minimal tool registry for immediate fixes."""

from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from vertice_core.tools.base import Tool


class MinimalToolRegistry:
    """Minimal tool registry to avoid circular imports."""

    def __init__(self):
        self.tools: Dict[str, "Tool"] = {}

    def register(self, tool: "Tool") -> None:
        """Register a tool."""
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional["Tool"]:
        """Get tool by name."""
        return self.tools.get(name)

    def get_all(self) -> Dict[str, "Tool"]:
        """Get all tools."""
        return self.tools.copy()

    def __len__(self) -> int:
        return len(self.tools)
