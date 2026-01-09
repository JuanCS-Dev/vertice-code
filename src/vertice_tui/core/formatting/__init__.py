"""
Formatting Module - Rich Panel formatting for LLM responses.

Semantic extraction from output_formatter.py for CODE_CONSTITUTION compliance.

Components:
- colors.py: Colors, Icons classes (brand palette)
- truncation.py: SmartTruncator, TruncationConfig
- formatter.py: OutputFormatter class
- helpers.py: Convenience functions and stream-safe markup

Following CODE_CONSTITUTION: <500 lines per file, 100% type hints
"""

from __future__ import annotations

# Core formatting
from .colors import Colors, Icons
from .truncation import (
    TruncationConfig,
    TruncatedContent,
    SmartTruncator,
    TRUNCATION_CONFIG,
    TRUNCATOR,
)
from .formatter import OutputFormatter

# Convenience helpers
from .helpers import (
    response_panel,
    tool_panel,
    code_panel,
    tool_executing_markup,
    tool_success_markup,
    tool_error_markup,
    agent_routing_markup,
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
