"""
App Styles - CSS for VERTICE Agent Agency TUI.

Phase 9 Visual Refresh:
- Input area floating with auto-resize
- Focus states enhanced
- Slate/Blue professional palette

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from typing import Dict

# =============================================================================
# PALETA DE CORES - VERTICE Slate/Blue Theme
# =============================================================================
# Primary: Blue (#3B82F6) - Main accent, actions
# Accent: Cyan (#22D3EE) - Highlights, cursor
# Secondary: Slate (#64748B) - Muted elements
# Success: Green (#22C55E) - Confirmations
# Warning: Amber (#F59E0B) - Caution
# Error: Red (#EF4444) - Failures
# Background: Slate-900 (#0F172A) - Soft black
# Surface: Slate-800 (#1E293B) - Cards, panels
# =============================================================================

APP_CSS: str = """
Screen {
    background: $background;
    layers: base autocomplete;
}

Header {
    background: $surface;
    color: $foreground;
    height: 1;
}

Footer {
    background: $surface;
    height: 1;
}

#main {
    height: 1fr;
    padding: 1 2;
    layer: base;
}

/* =============================================================================
   INPUT AREA - Floating Design with Auto-resize
   ============================================================================= */

#input-area {
    height: auto;
    min-height: 3;
    max-height: 10;
    border: round $primary;
    background: $background;
    padding: 0 1;
    margin: 0 1;
    transition: border 150ms;
}

#input-area:focus-within {
    border: double $accent;
}

#prompt-icon {
    width: 2;
    padding: 1 0;
    color: $accent;
    text-style: bold;
}

#prompt {
    background: transparent;
    border: none;
    color: $foreground;
    padding: 1 0;
}

#prompt:focus {
    border: none;
}

#prompt.-cursor-line {
    background: transparent;
}

/* =============================================================================
   RESPONSE VIEW - Clean minimal with hidden scrollbar
   ============================================================================= */

ResponseView {
    scrollbar-size: 0 0;
    background: $background;
    color: $foreground;
    padding: 0 1;
}

VerticalScroll {
    scrollbar-size: 0 0;
}

StreamingResponseWidget {
    scrollbar-size: 0 0;
}

/* =============================================================================
   SYSTEM MESSAGE PANELS - Premium 2026 Styling
   ============================================================================= */

.system-message {
    margin: 1 0;
    background: $surface;
    border: round $border;
    padding: 1 2;
}

.info-panel {
    margin: 1 0;
    background: $surface;
    border: round $primary;
    padding: 1 2;
}

.info-panel-header {
    color: $text-primary;
    text-style: bold;
    padding-bottom: 1;
    border-bottom: solid $border;
}


/* =============================================================================
   AUTOCOMPLETE DROPDOWN
   ============================================================================= */

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

#autocomplete:focus-within {
    border: double $accent;
}

/* =============================================================================
   CODE BLOCKS & SYNTAX
   ============================================================================= */

.code-block {
    background: $surface;
    border: round $border;
    padding: 1;
    margin: 1 0;
}

.code-header {
    color: $secondary;
    text-style: bold;
    padding: 0 0 1 0;
    border-bottom: solid $border;
}

.diff-add {
    color: $success;
    background: #22C55E20;
}

.diff-del {
    color: $error;
    background: #EF444420;
}

/* =============================================================================
   STATUS INDICATORS
   ============================================================================= */

.thinking {
    color: $accent;
}

.success {
    color: $success;
}

.error {
    color: $error;
}

.warning {
    color: $warning;
}

.muted {
    color: $secondary;
}

/* =============================================================================
   PANELS & CONTAINERS
   ============================================================================= */

.panel {
    background: $surface;
    border: round $border;
    padding: 1;
}

.panel:focus {
    border: double $primary;
}

.elevated {
    background: $panel-lighten-1;
}

/* =============================================================================
   TOKEN DASHBOARD - Context Usage Visualization
   ============================================================================= */

#token-dashboard {
    dock: top;
    height: auto;
    max-height: 8;
    margin: 0 1;
    padding: 0 1;
    background: $surface;
}

#token-dashboard.collapsed {
    height: 1;
    overflow: hidden;
}

/* Token Meter Progress Bar */
TokenMeter {
    height: 1;
    margin: 0 1;
}

TokenMeter > .progress-bar {
    color: $success;
}

TokenMeter > .progress-bar.warning {
    color: $warning;
}

TokenMeter > .progress-bar.danger {
    color: $error;
}

/* Breakdown Section */
TokenBreakdownWidget {
    height: auto;
    padding: 0 1;
}

/* Compression Indicator */
CompressionIndicator {
    height: 1;
    padding: 0 1;
}

/* Thinking Level Indicator */
ThinkingLevelIndicator {
    height: 1;
    padding: 0 1;
}

/* Mini Token Meter (for StatusBar) */
MiniTokenMeter {
    width: auto;
    min-width: 12;
}

/* =============================================================================
   MARKDOWN STYLING - Beautiful Typography
   Based on 2026 Textual best practices
   Using theme-adaptive $variables for light/dark compatibility
   ============================================================================= */

/* Headings - Bold, theme-adaptive hierarchy */
MarkdownH1 {
    color: $text-primary;
    text-style: bold;
    padding: 1 0;
    border-bottom: solid $border;
    margin-bottom: 1;
}

MarkdownH2 {
    color: $text-secondary;
    text-style: bold;
    padding: 1 0 0 0;
    margin-top: 1;
}

MarkdownH3 {
    color: $text;
    text-style: bold;
    margin-top: 1;
}

MarkdownH4, MarkdownH5, MarkdownH6 {
    color: $text-muted;
    text-style: bold;
}

/* Paragraphs */
MarkdownParagraph {
    margin: 0 0 1 0;
    color: $text;
}

/* Lists - Clean bullet/numbered styling */
MarkdownBulletList {
    margin: 0 0 1 2;
    padding-left: 2;
    color: $text;
}

MarkdownOrderedList {
    margin: 0 0 1 2;
    padding-left: 2;
    color: $text;
}

MarkdownListItem {
    margin: 0;
    padding: 0;
}

/* Code blocks - Beautiful panels */
MarkdownFence {
    background: $surface;
    border: round $border;
    margin: 1 0;
    padding: 1;
}

/* Inline code */
MarkdownCode {
    background: $surface;
    color: $text-accent;
}

/* Blockquotes - Styled with border */
MarkdownBlockQuote {
    border-left: thick $primary;
    padding-left: 2;
    margin: 1 0;
    color: $text-muted;
    text-style: italic;
}

/* Tables */
MarkdownTable {
    margin: 1 0;
}

MarkdownTH {
    text-style: bold;
    color: $text-primary;
    padding: 0 1;
}

MarkdownTD {
    padding: 0 1;
    color: $text;
}

/* Horizontal rule */
MarkdownHorizontalRule {
    color: $border;
    margin: 1 0;
}

/* Links */
MarkdownLink {
    color: $text-accent;
    text-style: underline;
}

/* Bold and Italic in text */
.bold {
    text-style: bold;
}

.italic {
    text-style: italic;
}

/* AI Response specific styling */
.ai-response {
    padding: 1 0;
    margin: 0;
    color: $text;
}

.ai-response MarkdownH1 {
    color: $text-primary;
}

.ai-response MarkdownBulletList {
    color: $text;
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
