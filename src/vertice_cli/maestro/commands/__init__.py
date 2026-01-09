"""
Maestro Commands - CLI command modules.

Exports sub-apps for registration with main app.
"""

from .agents import agent_app
from .config import config_app
from .root import info, main, version

__all__ = [
    "agent_app",
    "config_app",
    "info",
    "main",
    "version",
]
