"""
Widgets module for JuanCS Dev-Code TUI.

Re-exports all widgets for easy import:
    from vertice_tui.widgets import AutocompleteDropdown, ResponseView, StatusBar

Phase 10: Sprint 4 adds TokenDashboard for context visualization.

Soli Deo Gloria
"""

from vertice_tui.widgets.autocomplete import AutocompleteDropdown
from vertice_tui.widgets.selectable import SelectableStatic
from vertice_tui.widgets.response_view import ResponseView
from vertice_tui.widgets.status_bar import StatusBar
from vertice_tui.widgets.token_meter import (
    TokenBreakdown,
    TokenMeter,
    TokenBreakdownWidget,
    CompressionIndicator,
    ThinkingLevelIndicator,
    TokenDashboard,
    MiniTokenMeter,
)

__all__ = [
    "AutocompleteDropdown",
    "SelectableStatic",
    "ResponseView",
    "StatusBar",
    # Token Dashboard (Sprint 4)
    "TokenBreakdown",
    "TokenMeter",
    "TokenBreakdownWidget",
    "CompressionIndicator",
    "ThinkingLevelIndicator",
    "TokenDashboard",
    "MiniTokenMeter",
]
