"""
Plugin System for vertice_cli.

This module provides a plugin architecture for extending vertice_cli functionality.

Usage:
    from vertice_cli.plugins import Plugin, PluginManager

    class MyPlugin(Plugin):
        name = "my-plugin"
        version = "1.0.0"

        def activate(self) -> None:
            print("Plugin activated")

        def deactivate(self) -> None:
            print("Plugin deactivated")

    manager = PluginManager()
    manager.register(MyPlugin())

Author: Boris Cherny style
Date: 2025-11-26
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Plugin(Protocol):
    """
    Base plugin protocol.

    All plugins must implement this interface.

    Attributes:
        name: Unique plugin identifier
        version: Plugin version string
    """
    name: str
    version: str

    def activate(self) -> None:
        """Activate the plugin."""
        ...

    def deactivate(self) -> None:
        """Deactivate the plugin."""
        ...


from .plugin_manager import PluginManager

__all__ = [
    'Plugin',
    'PluginManager',
]
