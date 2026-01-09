"""
Output Module - Result Formatting and Rendering.

This module provides formatting and rendering utilities for shell output.
Follows Single Responsibility Principle with clear separation:

- formatters.py: Data transformation (tool results → display strings)
- renderers.py: Visual presentation (display strings → Rich components)

Usage:
    from vertice_cli.shell.output import ToolResultFormatter, ResultRenderer

    formatter = ToolResultFormatter()
    renderer = ResultRenderer(console)

    formatted = formatter.format(tool_name, result, args)
    renderer.render(tool_name, result, args)
"""

from .formatters import ToolResultFormatter
from .renderers import ResultRenderer

__all__ = [
    "ToolResultFormatter",
    "ResultRenderer",
]
