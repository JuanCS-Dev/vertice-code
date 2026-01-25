"""
Output Formatter - Backward Compatibility Shim.

DEPRECATED: Use vertice_core.tui.core.formatting module directly.

This module re-exports from the new formatting/ package for
backward compatibility. All functionality has been moved to:

- vertice_core.tui.core.formatting.colors     → Colors, Icons
- vertice_core.tui.core.formatting.truncation → SmartTruncator, TruncationConfig
- vertice_core.tui.core.formatting.formatter  → OutputFormatter
- vertice_core.tui.core.formatting.helpers    → Convenience functions

Migration:
    # Old:
    from vertice_core.tui.core.output_formatter import OutputFormatter, Colors

    # New:
    from vertice_core.tui.core.formatting import OutputFormatter, Colors
"""

from __future__ import annotations

import warnings

# Re-export everything from the new module
from .formatting import (
    # Colors and icons
    Colors,
    Icons,
    # Truncation
    TruncationConfig,
    TruncatedContent,
    SmartTruncator,
    TRUNCATION_CONFIG,
    TRUNCATOR,
    # Main formatter
    OutputFormatter,
    # Convenience helpers
    response_panel,
    tool_panel,
    code_panel,
    # Stream-safe markup
    tool_executing_markup,
    tool_success_markup,
    tool_error_markup,
    agent_routing_markup,
)

# Emit deprecation warning on import
warnings.warn(
    "vertice_core.tui.core.output_formatter is deprecated. Use vertice_core.tui.core.formatting instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    # Colors and icons
    "Colors",
    "Icons",
    # Truncation
    "TruncationConfig",
    "TruncatedContent",
    "SmartTruncator",
    "TRUNCATION_CONFIG",
    "TRUNCATOR",
    # Main formatter
    "OutputFormatter",
    # Convenience helpers
    "response_panel",
    "tool_panel",
    "code_panel",
    # Stream-safe markup
    "tool_executing_markup",
    "tool_success_markup",
    "tool_error_markup",
    "agent_routing_markup",
]
