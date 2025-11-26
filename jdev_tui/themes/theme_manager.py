"""
Theme Manager for JuanCS Dev-Code.

Provides dual theme system with:
- Claude Light: Inspired by Anthropic's warm design language
- Matrix Dark: Minimal cyberpunk with soft green (#1CA152)

Research sources:
- Textual Themes: https://textual.textualize.io/guide/design/
- Claude Brand: https://mobbin.com/colors/brand/claude
- Matrix Palette: https://www.schemecolor.com/matrix-code-green.php
"""

from enum import Enum
from pathlib import Path
from typing import Optional
import json

from textual.theme import Theme


class ThemeMode(Enum):
    """Available theme modes."""
    LIGHT = "claude-light"
    DARK = "matrix-dark"


# =============================================================================
# THEME LIGHT - Claude-Inspired
# =============================================================================
# Warm, professional aesthetic inspired by Anthropic's design language
# Primary: Crail Orange (#C15F3C) - Claude's signature color
# Background: Pampas (#F4F3EE) - Soft, warm off-white

THEME_LIGHT = Theme(
    name="claude-light",
    primary="#C15F3C",      # Crail - Claude Orange
    secondary="#B1ADA1",    # Cloudy - Muted accent
    background="#F4F3EE",   # Pampas - Warm off-white
    surface="#FFFFFF",      # Pure white for cards/panels
    foreground="#1A1A1A",   # Near black for text
    success="#1DB954",      # Spotify green
    error="#DC3545",        # Bootstrap red
    warning="#F5A623",      # Amber
    dark=False,
    variables={
        # Text variations
        "text-muted": "#6B6B6B",
        "text-disabled": "#9CA3AF",

        # Border
        "border": "#E5E4E0",
        "border-hover": "#C15F3C",

        # Input styling
        "input-cursor-foreground": "#C15F3C",
        "input-selection-background": "#C15F3C33",

        # Scrollbar
        "scrollbar": "#E5E4E0",
        "scrollbar-hover": "#C15F3C",

        # Footer
        "footer-key-foreground": "#C15F3C",
        "footer-description-foreground": "#6B6B6B",

        # Button
        "button-foreground": "#FFFFFF",

        # Panel/Surface
        "panel": "#FFFFFF",
        "panel-lighten-1": "#FAFAF9",
        "panel-darken-1": "#F5F5F4",
    }
)


# =============================================================================
# THEME DARK - Matrix Minimal
# =============================================================================
# Cyberpunk aesthetic with soft cinematic green
# Primary: Pigment Green (#1CA152) - Softer Matrix green
# Background: Pure Black (#000000) - Maximum contrast

THEME_DARK = Theme(
    name="matrix-dark",
    primary="#1CA152",      # Pigment Green - Soft Matrix
    secondary="#0D5C2E",    # Dark Forest
    background="#000000",   # Pure Black
    surface="#0A0A0A",      # Near Black
    foreground="#1CA152",   # Green text
    success="#1CA152",      # Same green for consistency
    error="#C62828",        # Dark Red (less aggressive)
    warning="#B8860B",      # Dark Goldenrod
    dark=True,
    variables={
        # Text variations
        "text-muted": "#0D5C2E",
        "text-disabled": "#0A3D1F",

        # Border
        "border": "#0D5C2E",
        "border-hover": "#1CA152",

        # Input styling
        "input-cursor-foreground": "#1CA152",
        "input-selection-background": "#1CA15233",

        # Scrollbar
        "scrollbar": "#0D5C2E",
        "scrollbar-hover": "#1CA152",

        # Footer
        "footer-key-foreground": "#1CA152",
        "footer-description-foreground": "#0D5C2E",

        # Button
        "button-foreground": "#000000",

        # Panel/Surface
        "panel": "#0A0A0A",
        "panel-lighten-1": "#111111",
        "panel-darken-1": "#050505",
    }
)


# =============================================================================
# THEME MANAGER
# =============================================================================

class ThemeManager:
    """
    Manages theme preferences with persistence.

    Stores preference in ~/.jdev_tui/config.json
    """

    CONFIG_DIR = Path.home() / ".jdev_tui"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    DEFAULT_THEME = ThemeMode.LIGHT

    @classmethod
    def get_theme_preference(cls) -> str:
        """Load saved theme preference or return default."""
        try:
            if cls.CONFIG_FILE.exists():
                config = json.loads(cls.CONFIG_FILE.read_text())
                return config.get("theme", cls.DEFAULT_THEME.value)
        except (json.JSONDecodeError, IOError):
            pass
        return cls.DEFAULT_THEME.value

    @classmethod
    def save_theme_preference(cls, theme_name: str) -> None:
        """Save theme preference to config file."""
        try:
            cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

            # Load existing config or create new
            config = {}
            if cls.CONFIG_FILE.exists():
                try:
                    config = json.loads(cls.CONFIG_FILE.read_text())
                except json.JSONDecodeError:
                    pass

            config["theme"] = theme_name
            cls.CONFIG_FILE.write_text(json.dumps(config, indent=2))
        except IOError:
            pass  # Silent fail - theme preference is non-critical

    @classmethod
    def toggle_theme(cls, current_theme: str) -> str:
        """
        Toggle between light and dark themes.

        Returns the new theme name.
        """
        if current_theme == ThemeMode.LIGHT.value:
            new_theme = ThemeMode.DARK.value
        else:
            new_theme = ThemeMode.LIGHT.value

        cls.save_theme_preference(new_theme)
        return new_theme

    @classmethod
    def get_available_themes(cls) -> list[Theme]:
        """Return list of all available themes."""
        return [THEME_LIGHT, THEME_DARK]

    @classmethod
    def get_theme_by_name(cls, name: str) -> Optional[Theme]:
        """Get theme object by name."""
        themes = {
            ThemeMode.LIGHT.value: THEME_LIGHT,
            ThemeMode.DARK.value: THEME_DARK,
        }
        return themes.get(name)
