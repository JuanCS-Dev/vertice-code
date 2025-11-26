"""
Widgets module for JuanCS Dev-Code TUI.

Re-exports all widgets for easy import:
    from jdev_tui.widgets import AutocompleteDropdown, ResponseView, StatusBar
"""

from jdev_tui.widgets.autocomplete import AutocompleteDropdown
from jdev_tui.widgets.selectable import SelectableStatic
from jdev_tui.widgets.response_view import ResponseView
from jdev_tui.widgets.status_bar import StatusBar

__all__ = [
    "AutocompleteDropdown",
    "SelectableStatic",
    "ResponseView",
    "StatusBar",
]
