"""
VERTICE Agent Agency Theme System.

Quad theme support (Phase 9 Visual Refresh):
- vertice-dark: Professional Slate/Blue (DEFAULT)
- vertice-light: Clean minimal Blue
- claude-light: Legacy Orange theme
- matrix-dark: Legacy Cyberpunk Green theme
"""

from .theme_manager import (
    ThemeMode,
    THEME_VERTICE_DARK,
    THEME_VERTICE_LIGHT,
    THEME_LIGHT,
    THEME_DARK,
    ThemeManager,
)

__all__ = [
    "ThemeMode",
    "THEME_VERTICE_DARK",
    "THEME_VERTICE_LIGHT",
    "THEME_LIGHT",
    "THEME_DARK",
    "ThemeManager",
]
