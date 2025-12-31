"""
Theme Manager for VERTICE Agent Agency.

Provides quad theme system with:
- Vertice Dark (DEFAULT): Slate/Professional with Blue accent
- Vertice Light: Clean minimal with Blue accent
- Claude Light (Legacy): Warm Orange palette
- Matrix Dark (Legacy): Cyberpunk Green palette

Research sources (Phase 9 Visual Refresh - Dec 2025):
- Textual Themes: https://textual.textualize.io/guide/design/
- Dark Mode Best Practices 2025: https://cuibit.com/dark-mode-design-best-practices-for-2025/
- WCAG Accessibility: 7:1 contrast ratio (AAA)
- Tailwind CSS Slate Palette: https://tailwindcss.com/docs/customizing-colors
"""

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Optional, Tuple
import json

from textual.theme import Theme


class ThemeMode(Enum):
    """Available theme modes."""
    # New defaults (Phase 9)
    VERTICE_DARK = "vertice-dark"
    VERTICE_LIGHT = "vertice-light"
    # Legacy themes
    LIGHT = "claude-light"
    DARK = "matrix-dark"


# =============================================================================
# THEME VERTICE DARK (DEFAULT) - Professional Slate/Blue
# =============================================================================
# Modern professional aesthetic with Tailwind Slate palette
# WCAG AAA compliant (7:1 contrast ratio)
# Inspired by: Claude Code, Cursor, Windsurf (Dec 2025 research)

THEME_VERTICE_DARK = Theme(
    name="vertice-dark",
    primary="#3B82F6",          # Blue-500 (clean, professional)
    secondary="#64748B",        # Slate-500
    accent="#22D3EE",           # Cyan-400 (highlights, cursor)
    background="#0F172A",       # Slate-900 (soft black, not pure #000)
    surface="#1E293B",          # Slate-800 (cards, panels)
    foreground="#F1F5F9",       # Slate-100 (soft white)
    success="#22C55E",          # Green-500
    error="#EF4444",            # Red-500
    warning="#F59E0B",          # Amber-500
    dark=True,
    variables={
        "text-muted": "#94A3B8",             # Slate-400
        "text-disabled": "#64748B",          # Slate-500
        "border": "#334155",                 # Slate-700
        "border-hover": "#3B82F6",           # Blue-500
        "input-cursor-foreground": "#22D3EE",  # Cyan-400
        "input-cursor-background": "#22D3EE",
        "input-selection-background": "#3B82F633",
        "scrollbar": "#334155",              # Slate-700
        "scrollbar-hover": "#3B82F6",
        "footer-key-foreground": "#3B82F6",
        "footer-description-foreground": "#94A3B8",
        "button-foreground": "#FFFFFF",
        "button-background": "#3B82F6",
        "panel": "#1E293B",                  # Slate-800
        "panel-lighten-1": "#334155",        # Slate-700
        "panel-darken-1": "#0F172A",         # Slate-900
        "code-background": "#1E293B",
        "code-foreground": "#E2E8F0",
        "link": "#3B82F6",
        "link-hover": "#60A5FA",             # Blue-400
    }
)


# =============================================================================
# THEME VERTICE LIGHT - Clean Minimal Blue
# =============================================================================
# Clean minimal aesthetic with Blue accent
# WCAG AAA compliant

THEME_VERTICE_LIGHT = Theme(
    name="vertice-light",
    primary="#2563EB",          # Blue-600
    secondary="#64748B",        # Slate-500
    accent="#0891B2",           # Cyan-600
    background="#FFFFFF",       # Pure white
    surface="#F8FAFC",          # Slate-50
    foreground="#0F172A",       # Slate-900
    success="#16A34A",          # Green-600
    error="#DC2626",            # Red-600
    warning="#D97706",          # Amber-600
    dark=False,
    variables={
        "text-muted": "#64748B",             # Slate-500
        "text-disabled": "#94A3B8",          # Slate-400
        "border": "#E2E8F0",                 # Slate-200
        "border-hover": "#2563EB",           # Blue-600
        "input-cursor-foreground": "#2563EB",
        "input-selection-background": "#2563EB33",
        "scrollbar": "#E2E8F0",
        "scrollbar-hover": "#2563EB",
        "footer-key-foreground": "#2563EB",
        "footer-description-foreground": "#64748B",
        "button-foreground": "#FFFFFF",
        "button-background": "#2563EB",
        "panel": "#FFFFFF",
        "panel-lighten-1": "#FAFAFA",
        "panel-darken-1": "#F8FAFC",
        "code-background": "#F1F5F9",        # Slate-100
        "code-foreground": "#1E293B",        # Slate-800
        "link": "#2563EB",
        "link-hover": "#1D4ED8",             # Blue-700
    }
)


# =============================================================================
# THEME LIGHT (Legacy) - Orange Theme
# =============================================================================
# Warm, professional aesthetic with orange/brown palette
# Primary: Dark Orange (#ff8c00)

THEME_LIGHT = Theme(
    name="claude-light",
    primary="#ff8c00",
    secondary="#b8860b",
    accent="#ff6600",
    background="#F4F3EE",
    surface="#FFFFFF",
    foreground="#1A1A1A",
    success="#1DB954",
    error="#DC3545",
    warning="#F5A623",
    dark=False,
    variables={
        "text-muted": "#6B6B6B",
        "text-disabled": "#9CA3AF",
        "border": "#E5E4E0",
        "border-hover": "#ff8c00",
        "input-cursor-foreground": "#ff8c00",
        "input-selection-background": "#ff8c0033",
        "scrollbar": "#E5E4E0",
        "scrollbar-hover": "#ff8c00",
        "footer-key-foreground": "#ff8c00",
        "footer-description-foreground": "#6B6B6B",
        "button-foreground": "#FFFFFF",
        "panel": "#FFFFFF",
        "panel-lighten-1": "#FAFAF9",
        "panel-darken-1": "#F5F5F4",
        "code-background": "#fff3e0",
        "code-foreground": "#cc4a0a",
    }
)


# =============================================================================
# THEME DARK (Legacy) - Matrix Cinematic
# =============================================================================
# Cyberpunk aesthetic with layered green hierarchy
# Keep for backwards compatibility

THEME_DARK = Theme(
    name="matrix-dark",
    primary="#00FF41",
    secondary="#1CA152",
    accent="#39FF14",
    background="#000000",
    surface="#050505",
    foreground="#1CA152",
    success="#39FF14",
    error="#FF3131",
    warning="#FFD700",
    dark=True,
    variables={
        "text": "#1CA152",
        "text-muted": "#0D5C2E",
        "text-disabled": "#0A3D1F",
        "border": "#0D5C2E",
        "border-hover": "#00FF41",
        "input-cursor-foreground": "#39FF14",
        "input-cursor-background": "#39FF14",
        "input-selection-background": "#00FF4133",
        "scrollbar": "#0A3D1F",
        "scrollbar-hover": "#1CA152",
        "footer-key-foreground": "#00FF41",
        "footer-description-foreground": "#0D5C2E",
        "button-foreground": "#000000",
        "button-background": "#00FF41",
        "panel": "#050505",
        "panel-lighten-1": "#0A0A0A",
        "panel-darken-1": "#000000",
        "link": "#00FF41",
        "link-hover": "#39FF14",
    }
)


# =============================================================================
# THEME MANAGER
# =============================================================================

class ThemeManager:
    """
    Manages theme preferences with persistence.

    Stores preference in ~/.vertice_tui/config.json

    Available themes:
        - vertice-dark: Professional Slate/Blue (DEFAULT)
        - vertice-light: Clean minimal Blue
        - claude-light: Legacy Orange theme
        - matrix-dark: Legacy Cyberpunk Green theme
    """

    CONFIG_DIR = Path.home() / ".vertice_tui"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    DEFAULT_THEME = ThemeMode.VERTICE_DARK

    _THEME_MAP = {
        ThemeMode.VERTICE_DARK.value: "THEME_VERTICE_DARK",
        ThemeMode.VERTICE_LIGHT.value: "THEME_VERTICE_LIGHT",
        ThemeMode.LIGHT.value: "THEME_LIGHT",
        ThemeMode.DARK.value: "THEME_DARK",
    }

    @classmethod
    def get_theme_preference(cls) -> str:
        """Load saved theme preference or return default."""
        try:
            if cls.CONFIG_FILE.exists():
                config = json.loads(cls.CONFIG_FILE.read_text())
                theme = config.get("theme", cls.DEFAULT_THEME.value)
                if theme in cls._THEME_MAP:
                    return theme
        except (json.JSONDecodeError, IOError):
            pass
        return cls.DEFAULT_THEME.value

    @classmethod
    def save_theme_preference(cls, theme_name: str) -> None:
        """Save theme preference to config file."""
        try:
            cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            config = {}
            if cls.CONFIG_FILE.exists():
                try:
                    config = json.loads(cls.CONFIG_FILE.read_text())
                except json.JSONDecodeError as e:
                    import logging
                    logging.warning(f"Corrupted theme config, using defaults: {e}")
            config["theme"] = theme_name
            cls.CONFIG_FILE.write_text(json.dumps(config, indent=2))
        except IOError:
            pass

    @classmethod
    def toggle_theme(cls, current_theme: str) -> str:
        """
        Toggle between light and dark Vertice themes.

        Args:
            current_theme: Current theme name.

        Returns:
            New theme name (vertice-dark or vertice-light).
        """
        if current_theme in (ThemeMode.VERTICE_LIGHT.value, ThemeMode.LIGHT.value):
            new_theme = ThemeMode.VERTICE_DARK.value
        else:
            new_theme = ThemeMode.VERTICE_LIGHT.value
        cls.save_theme_preference(new_theme)
        return new_theme

    @classmethod
    @lru_cache(maxsize=1)
    def get_available_themes(cls) -> Tuple[Theme, ...]:
        """Return tuple of all available themes (cached)."""
        return (THEME_VERTICE_DARK, THEME_VERTICE_LIGHT, THEME_LIGHT, THEME_DARK)

    @classmethod
    @lru_cache(maxsize=8)
    def get_theme_by_name(cls, name: str) -> Optional[Theme]:
        """
        Get theme object by name (cached).

        Args:
            name: Theme name string.

        Returns:
            Theme object or None if not found.
        """
        themes = {
            ThemeMode.VERTICE_DARK.value: THEME_VERTICE_DARK,
            ThemeMode.VERTICE_LIGHT.value: THEME_VERTICE_LIGHT,
            ThemeMode.LIGHT.value: THEME_LIGHT,
            ThemeMode.DARK.value: THEME_DARK,
        }
        return themes.get(name)
