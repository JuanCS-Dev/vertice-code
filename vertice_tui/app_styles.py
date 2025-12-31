"""
App Styles - CSS definitions for QwenApp.

Extracted from app.py (Dec 2025 Refactoring).

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from typing import Dict

# =============================================================================
# PALETA DE CORES COESA - JuanCS Dev-Code Theme
# =============================================================================
# Primary: Cyan (#00d4aa) - Main accent, user prompts, panels
# Secondary: Magenta (#ff79c6) - Highlights, agent indicators
# Success: Green (#50fa7b) - Success messages, confirmations
# Warning: Yellow (#f1fa8c) - Warnings, caution
# Error: Red (#ff5555) - Errors, failures
# Muted: Gray (#6272a4) - Dim text, hints
# Surface: Dark (#1e1e2e) - Background
# =============================================================================

APP_CSS: str = """
Screen {
    background: $background;
    layers: base autocomplete;
}

Header {
    background: $surface;
    color: $foreground;
}

Footer {
    background: $surface;
}

#main {
    height: 1fr;
    padding: 1 2;
    layer: base;
}

/* Input area - uses theme colors */
#input-area {
    height: 3;
    border: round $primary;
    background: $surface;
    padding: 0 1;
}

#prompt-icon {
    width: 3;
    padding: 1 0;
    color: $primary;
    text-style: bold;
}

#prompt {
    background: transparent;
    border: none;
    color: $foreground;
}

#prompt:focus {
    border: none;
}

/* ResponseView styling */
ResponseView {
    scrollbar-size: 0 0;
    background: $background;
    color: $foreground;
}

VerticalScroll {
    scrollbar-size: 0 0;
}

/* Autocomplete dropdown - uses theme colors */
#autocomplete {
    layer: autocomplete;
    dock: bottom;
    offset: 0 -4;
    margin: 0 3;
    background: $surface;
    border: round $primary;
    padding: 0 1;
    max-height: 18;
    display: none;
    color: $foreground;
}

#autocomplete.visible {
    display: block;
}
"""


# =============================================================================
# LANGUAGE DETECTION
# =============================================================================

LANGUAGE_MAP: Dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".toml": "toml",
    ".ini": "ini",
    ".xml": "xml",
}


def detect_language(suffix: str) -> str:
    """
    Detect programming language from file extension.

    Args:
        suffix: File extension (e.g., ".py", ".js")

    Returns:
        Language identifier for syntax highlighting
    """
    return LANGUAGE_MAP.get(suffix.lower(), "text")
