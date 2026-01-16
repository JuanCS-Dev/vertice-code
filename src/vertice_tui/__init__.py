"""
🎨 Vertice TUI - AI-Powered Text User Interface
🕐 Temporally Conscious TUI System

A beautiful, 60fps TUI for AI-powered development.
Temporal Awareness: ACTIVE

PERFORMANCE OPTIMIZATION (Jan 2026):
- Lazy loading of VerticeApp to reduce startup time
- Use `from vertice_tui.app import VerticeApp` for explicit import
- The package import alone does NOT load heavy dependencies now

Soli Deo Gloria
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

__version__ = "1.0.0"
__author__ = "JuanCS"

if TYPE_CHECKING:
    from .app import VerticeApp, main

# Lazy loading for backward compatibility
_LAZY_IMPORTS = {
    "VerticeApp": (".app", "VerticeApp"),
    "QwenApp": (".app", "VerticeApp"),  # Alias
    "main": (".app", "main"),
}

_cache: dict[str, Any] = {}


def __getattr__(name: str) -> Any:
    """Lazy import VerticeApp and main on first access."""
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
    return ["VerticeApp", "QwenApp", "main", "__version__", "__author__"]


__all__ = ["VerticeApp", "QwenApp", "main", "__version__"]
