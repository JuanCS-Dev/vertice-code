"""
Color Palette & Icons - JuanCS Dev-Code Brand.

Centralized color definitions for consistent UI styling.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations


class Colors:
    """JuanCS Dev-Code brand colors - centralized for consistency."""

    # Primary accent - Orange theme
    PRIMARY: str = "#ff8c00"        # Dark Orange - Main accent
    SECONDARY: str = "#b8860b"      # Dark Goldenrod - Secondary
    ACTION: str = "#ff6600"         # Orange - Tool actions

    # Status colors (universal conventions - DO NOT CHANGE)
    SUCCESS: str = "#1DB954"        # Green - Success
    ERROR: str = "#DC3545"          # Red - Errors
    WARNING: str = "#f5a623"        # Amber - Warnings
    INFO: str = "#3498db"           # Blue - Info

    # Text colors
    MUTED: str = "#6b6b6b"          # Gray - Muted/dim text
    DIM: str = "#888888"            # Light gray - Very dim

    # Tool-specific
    TOOL_EXEC: str = "#ff8c00"      # Tool execution indicator
    TOOL_SUCCESS: str = "#1DB954"   # Tool success
    TOOL_ERROR: str = "#DC3545"     # Tool failure

    # Agent-specific
    AGENT: str = "#ff6600"          # Agent indicator
    ROUTING: str = "#ff8c00"        # Auto-routing indicator


class Icons:
    """Consistent icons for different output types."""

    # Status icons
    SUCCESS: str = "✓"
    ERROR: str = "✗"
    WARNING: str = "⚠"
    INFO: str = "ℹ"

    # Action icons
    EXECUTING: str = "●"
    THINKING: str = "●"
    ROUTING: str = "🎯"

    # Tool icons
    TOOL: str = "⚡"
    FILE: str = "📄"
    CODE: str = "💻"
    SEARCH: str = "🔍"
    GIT: str = "📦"
    WEB: str = "🌐"
    BASH: str = "💲"

    # Agent icons
    AGENT: str = "🤖"
    PLAN: str = "📋"
    REVIEW: str = "👁"
    SECURITY: str = "🔒"

    # Truncation icons
    EXPAND: str = "▼"
    COLLAPSE: str = "▲"
    TRUNCATED: str = "···"
