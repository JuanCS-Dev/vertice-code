"""
Widgets module for JuanCS Dev-Code TUI.

Re-exports all widgets for easy import:
    from qwen_cli.widgets import AutocompleteDropdown, ResponseView, StatusBar
"""

from qwen_cli.widgets.autocomplete import AutocompleteDropdown
from qwen_cli.widgets.selectable import SelectableStatic
from qwen_cli.widgets.response_view import ResponseView
from qwen_cli.widgets.status_bar import StatusBar

__all__ = [
    "AutocompleteDropdown",
    "SelectableStatic",
    "ResponseView",
    "StatusBar",
]
