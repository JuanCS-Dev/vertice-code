"""
Widgets module for JuanCS Dev-Code TUI.

Re-exports all widgets for easy import:
    from vertice_tui.widgets import AutocompleteDropdown, ResponseView, StatusBar
"""

from vertice_tui.widgets.autocomplete import AutocompleteDropdown
from vertice_tui.widgets.selectable import SelectableStatic
from vertice_tui.widgets.response_view import ResponseView
from vertice_tui.widgets.status_bar import StatusBar

__all__ = [
    "AutocompleteDropdown",
    "SelectableStatic",
    "ResponseView",
    "StatusBar",
]
