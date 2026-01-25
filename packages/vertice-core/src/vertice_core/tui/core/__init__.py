"""
QWEN CLI Core - Integration Bridge
===================================

Minimal bridge connecting the beautiful TUI to the powerful agent system.

PERFORMANCE OPTIMIZATION (Jan 2026):
- Lazy loading to reduce startup time from ~2500ms to <100ms
- Use explicit imports like `from vertice_core.tui.core.bridge import get_bridge`

Components:
- GeminiClient: Streaming LLM via Gemini API (optimized Nov 2025)
- AgentManager: Lazy loading of 20 agents
- GovernanceObserver: ELP alerts without blocking
- ToolBridge: 47 tools via registry
- CommandPaletteBridge: Fuzzy search commands
- AutocompleteBridge: Context-aware fuzzy matching
- HistoryManager: Persistent command & context history
- OutputFormatter: Rich Panel formatting for responses
- ToolCallParser: Extract and execute tool calls from LLM
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

# Lazy import mapping
_LAZY_IMPORTS = {
    # Bridge components
    "Bridge": (".bridge", "Bridge"),
    "GeminiClient": (".bridge", "GeminiClient"),
    "AgentManager": (".bridge", "AgentManager"),
    "GovernanceObserver": (".bridge", "GovernanceObserver"),
    "RiskLevel": (".bridge", "RiskLevel"),
    "ToolBridge": (".bridge", "ToolBridge"),
    "CommandPaletteBridge": (".bridge", "CommandPaletteBridge"),
    "AutocompleteBridge": (".bridge", "AutocompleteBridge"),
    "HistoryManager": (".bridge", "HistoryManager"),
    "ToolCallParser": (".bridge", "ToolCallParser"),
    "get_bridge": (".bridge", "get_bridge"),
    # Formatting
    "OutputFormatter": (".formatting", "OutputFormatter"),
    # Maximus client
    "MaximusClient": (".maximus_client", "MaximusClient"),
    "MaximusStreamConfig": (".maximus_client", "MaximusStreamConfig"),
}

_cache: dict[str, Any] = {}


def __getattr__(name: str) -> Any:
    """Lazy import on first access."""
    if name in _cache:
        return _cache[name]

    if name in _LAZY_IMPORTS:
        module_path, attr_name = _LAZY_IMPORTS[name]
        import importlib

        module = importlib.import_module(module_path, __name__)
        value = getattr(module, attr_name)
        _cache[name] = value
        return value

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Return available names."""
    return list(_LAZY_IMPORTS.keys())


__all__ = list(_LAZY_IMPORTS.keys())
