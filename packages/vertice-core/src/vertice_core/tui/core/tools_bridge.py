"""
Tools Bridge Module - 47 Tools Integration
==========================================

Extracted from Bridge GOD CLASS (Nov 2025 Refactoring).

Features:
- Lazy loading tool registry
- File Operations (12), Terminal (9), Execution (2)
- Search (2), Git (2), Context (3), Web (6)
- Claude Code Parity Tools (7)
"""

from __future__ import annotations

from typing import Any, Dict, List


class ToolBridge:
    """
    Bridge to 47 tools from vertice_core.

    Lazy loading to keep startup fast.

    Categories:
    - File Operations (12): read, write, edit, list, delete, move, copy, mkdir, insert
    - Terminal (9): cd, ls, pwd, mkdir, rm, cp, mv, touch, cat
    - Execution (2): bash, bash_hardened
    - Search (2): search_files, get_directory_tree
    - Git (2): git_status, git_diff
    - Context (3): get_context, save_session, restore_backup
    - Web (6): web_search, fetch_url, download_file, http_request, package_search, search_docs
    """

    def __init__(self):
        self._registry = None
        self._load_errors: List[str] = []

    @property
    def registry(self):
        """Lazy load tool registry."""
        if self._registry is None:
            self._registry = self._create_registry()
        return self._registry

    def _create_registry(self):
        """Create and populate tool registry via ToolCatalog."""
        try:
            from vertice_core.tools.catalog import get_catalog

            # TUI: Defaults + Web + Parity.
            # Prometheus is NOT enabled by default here (might be loaded separately or on demand)
            # or maybe it SHOULD be enabled? The old code didn't have it.
            # I will stick to parity with old code for now: Defaults + Web + Parity.

            catalog = get_catalog(include_web=True, include_parity=True, include_prometheus=False)

            # Since catalog builder might catch errors internally, we check if we need to surface them
            # The catalog logs them, but we can also inspect if needed.
            # For ToolBridge compatibility, we return the built registry.

            return catalog

        except ImportError:
            # Return empty registry if vertice_core not available
            return MinimalRegistry()

    def get_tool(self, name: str):
        """Get tool by name."""
        return self.registry.get(name)

    def list_tools(self) -> List[str]:
        """List all available tool names."""
        return list(self.registry.get_all().keys())

    def get_tool_count(self) -> int:
        """Get number of loaded tools."""
        return len(self.registry.get_all())

    async def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name with given parameters."""
        tool = self.get_tool(name)
        if not tool:
            return {"success": False, "error": f"Tool not found: {name}"}

        try:
            result = await tool._execute_validated(**kwargs)
            return {
                "success": result.success,
                "data": result.data,
                "error": result.error,
                "metadata": result.metadata,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_schemas_for_llm(self) -> List[Dict]:
        """Get tool schemas formatted for LLM function calling."""
        return self.registry.get_schemas()


class MinimalRegistry:
    """Minimal fallback tool registry."""

    def __init__(self):
        self.tools: Dict[str, Any] = {}

    def get_all(self):
        return self.tools

    def get(self, name):
        return self.tools.get(name)

    def get_schemas(self):
        return []


__all__ = [
    "ToolBridge",
    "MinimalRegistry",
]
