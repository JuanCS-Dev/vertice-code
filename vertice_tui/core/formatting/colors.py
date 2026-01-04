"""
Color Palette & Icons - VERTICE Agent Agency.

Phase 9 Visual Refresh:
- Slate/Blue professional palette
- Unicode minimalista (no emojis)
- WCAG AAA compliant

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations


class Colors:
    """VERTICE brand colors - Slate/Blue professional palette."""

    # Primary - Blue theme (Tailwind)
    PRIMARY: str = "#3B82F6"  # Blue-500
    SECONDARY: str = "#64748B"  # Slate-500
    ACCENT: str = "#22D3EE"  # Cyan-400

    # Status colors (universal)
    SUCCESS: str = "#22C55E"  # Green-500
    ERROR: str = "#EF4444"  # Red-500
    WARNING: str = "#F59E0B"  # Amber-500
    INFO: str = "#3B82F6"  # Blue-500

    # Text colors (Slate)
    FOREGROUND: str = "#F1F5F9"  # Slate-100
    MUTED: str = "#94A3B8"  # Slate-400
    DIM: str = "#64748B"  # Slate-500
    DISABLED: str = "#475569"  # Slate-600

    # Background (Slate)
    BACKGROUND: str = "#0F172A"  # Slate-900
    SURFACE: str = "#1E293B"  # Slate-800
    BORDER: str = "#334155"  # Slate-700

    # Tool-specific
    TOOL_EXEC: str = "#3B82F6"  # Blue-500
    TOOL_SUCCESS: str = "#22C55E"  # Green-500
    TOOL_ERROR: str = "#EF4444"  # Red-500

    # Agent-specific
    AGENT: str = "#22D3EE"  # Cyan-400
    ROUTING: str = "#3B82F6"  # Blue-500
    ACTION: str = "#F59E0B"  # Amber-500 (action indicators)


class Icons:
    """
    Unicode minimalista icons for consistent UI.

    No emojis - pure Unicode symbols for:
    - Better font compatibility
    - Professional appearance
    - Faster rendering
    """

    # Status
    SUCCESS: str = "✓"  # Checkmark
    ERROR: str = "✗"  # X mark
    WARNING: str = "⚠"  # Warning triangle
    INFO: str = "ℹ"  # Info circle

    # Actions
    THINKING: str = "◐"  # Quarter circle (animated)
    EXECUTING: str = "▸"  # Play
    LOADING: str = "⠋"  # Braille (spinner)
    WAITING: str = "◌"  # Circle outline

    # Files
    FILE: str = "▪"  # Small square
    FOLDER: str = "▸"  # Chevron right
    FOLDER_OPEN: str = "▾"  # Chevron down
    CODE_FILE: str = "▫"  # White square

    # Code
    CODE: str = "❯"  # Prompt
    GIT: str = "⎇"  # Branch
    DIFF_ADD: str = "+"  # Addition
    DIFF_DEL: str = "-"  # Deletion

    # Agents
    AGENT: str = "◆"  # Diamond
    TOOL: str = "⚡"  # Lightning
    PLAN: str = "▤"  # Grid
    REVIEW: str = "◎"  # Target
    ROUTING: str = "⇢"  # Right arrow for routing

    # Search
    SEARCH: str = "○"  # Circle
    WEB: str = "◯"  # Large circle

    # Terminal
    BASH: str = "$"  # Dollar sign
    PROMPT: str = "❯"  # Prompt

    # Navigation
    EXPAND: str = "▼"  # Down
    COLLAPSE: str = "▲"  # Up
    TRUNCATED: str = "···"  # Ellipsis
    ARROW_RIGHT: str = "→"  # Right arrow
    ARROW_LEFT: str = "←"  # Left arrow

    # Security
    SECURITY: str = "⊡"  # Square with dot
    LOCK: str = "⊞"  # Crossed square

    # Misc
    BULLET: str = "•"  # Bullet
    DOT: str = "·"  # Middle dot
    SEPARATOR: str = "│"  # Vertical bar
