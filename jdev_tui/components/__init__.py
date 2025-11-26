"""
jdev_tui.components - Bridge components for streaming markdown.

This module provides adapters that connect jdev_tui (main entry point)
to jdev_cli.tui.components (streaming markdown widgets).

CORRIGE AIR GAP:
- Entry point usa jdev_tui.app, não jdev_cli.tui
- Componentes streaming estavam órfãos em jdev_cli/tui/components/
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
