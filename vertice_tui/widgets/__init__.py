"""
Widgets module for JuanCS Dev-Code TUI.

Re-exports all widgets for easy import:
    from vertice_tui.widgets import AutocompleteDropdown, ResponseView, StatusBar

Phase 10: Sprint 4 adds TokenDashboard for context visualization.
Phase 11: Visual Upgrade adds Modal and Toast systems.

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
# Phase 11: Visual Upgrade - Modal System
from vertice_tui.widgets.modal import (
    ConfirmDialog,
    AlertDialog,
    InputDialog,
    FilePickerDialog,
    ProgressDialog,
    confirm,
    alert,
    prompt,
)
# Phase 11: Visual Upgrade - Toast Helpers
from vertice_tui.widgets.toast import (
    toast_success,
    toast_error,
    toast_warning,
    toast_info,
    toast_copied,
    ToastMixin,
)
# Phase 11: Visual Upgrade - Diff View
from vertice_tui.widgets.diff_view import (
    DiffView,
    InlineDiff,
    create_diff_text,
)
# Phase 11: Visual Upgrade - Tool Call Visualization
from vertice_tui.widgets.tool_call import (
    ToolStatus,
    ToolCallData,
    ToolCallWidget,
    ToolCallStack,
)
# Phase 11: Visual Upgrade - Enhanced Input
from vertice_tui.widgets.input_area import InputArea
# Phase 11: Visual Upgrade - Loading Animations
from vertice_tui.widgets.loading import (
    SkeletonLine,
    SkeletonBlock,
    SpinnerWidget,
    LoadingCard,
    ThinkingIndicator,
    PulseIndicator,
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
    # Modal System (Phase 11)
    "ConfirmDialog",
    "AlertDialog",
    "InputDialog",
    "FilePickerDialog",
    "ProgressDialog",
    "confirm",
    "alert",
    "prompt",
    # Toast Helpers (Phase 11)
    "toast_success",
    "toast_error",
    "toast_warning",
    "toast_info",
    "toast_copied",
    "ToastMixin",
    # Diff View (Phase 11)
    "DiffView",
    "InlineDiff",
    "create_diff_text",
    # Tool Call Visualization (Phase 11)
    "ToolStatus",
    "ToolCallData",
    "ToolCallWidget",
    "ToolCallStack",
    # Enhanced Input (Phase 11)
    "InputArea",
    # Loading Animations (Phase 11)
    "SkeletonLine",
    "SkeletonBlock",
    "SpinnerWidget",
    "LoadingCard",
    "ThinkingIndicator",
    "PulseIndicator",
]
