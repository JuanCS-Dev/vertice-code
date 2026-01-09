"""
vertice_tui.components - Bridge components for streaming markdown.

This module provides adapters that connect vertice_tui (main entry point)
to vertice_cli.tui.components (streaming markdown widgets).

CORRIGE AIR GAP:
- Entry point usa vertice_tui.app, não vertice_cli.tui
- Componentes streaming estavam órfãos em vertice_cli/tui/components/
- Este adapter faz a ponte entre os dois mundos

Created: 2025-11-25
"""

from .streaming_adapter import (
    StreamingResponseWidget,
    StreamingMarkdownAdapter,
)

__all__ = [
    "StreamingResponseWidget",
    "StreamingMarkdownAdapter",
]
