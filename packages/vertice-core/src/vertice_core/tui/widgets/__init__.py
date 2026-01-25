"""
Widgets module for JuanCS Dev-Code TUI.

Lazy-loaded to improve startup time.
Use:
    from vertice_core.tui.widgets import AutocompleteDropdown, ResponseView, StatusBar

PERFORMANCE OPTIMIZATION (Jan 2026):
- Converted from eager imports to lazy loading via __getattr__
- Reduces startup time from ~2.5s to ~100ms
- Widgets are loaded on first access

Soli Deo Gloria
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # Type hints only - no runtime cost
    from vertice_core.tui.widgets.autocomplete import AutocompleteDropdown
    from vertice_core.tui.widgets.selectable import SelectableStatic
    from vertice_core.tui.widgets.response_view import ResponseView
    from vertice_core.tui.widgets.status_bar import StatusBar
    from vertice_core.tui.widgets.token_meter import (
        TokenBreakdown,
        TokenMeter,
        TokenBreakdownWidget,
        CompressionIndicator,
        ThinkingLevelIndicator,
        TokenDashboard,
        MiniTokenMeter,
    )
    from vertice_core.tui.widgets.performance_hud import PerformanceHUD
    from vertice_core.tui.widgets.fuzzy_search_modal import FuzzySearchModal
    from vertice_core.tui.widgets.export_modal import ExportModal
    from vertice_core.tui.widgets.modal import (
        ConfirmDialog,
        AlertDialog,
        InputDialog,
        FilePickerDialog,
        ProgressDialog,
        confirm,
        alert,
        prompt,
    )
    from vertice_core.tui.widgets.toast import (
        toast_success,
        toast_error,
        toast_warning,
        toast_info,
        toast_copied,
        ToastMixin,
    )
    from vertice_core.tui.widgets.diff_view import DiffView, InlineDiff, create_diff_text
    from vertice_core.tui.widgets.tool_call import (
        ToolStatus,
        ToolCallData,
        ToolCallWidget,
        ToolCallStack,
    )
    from vertice_core.tui.widgets.input_area import InputArea
    from vertice_core.tui.widgets.loading import (
        SkeletonLine,
        SkeletonBlock,
        SpinnerWidget,
        LoadingCard,
        ThinkingIndicator,
        ReasoningStream,
        PulseIndicator,
    )
    from vertice_core.tui.widgets.sidebar import Sidebar, FilteredDirectoryTree
    from vertice_core.tui.widgets.session_tabs import SessionTabs, SessionPane, SessionData
    from vertice_core.tui.widgets.split_view import SplitView, SplitPane, DualPane
    from vertice_core.tui.widgets.breadcrumb import Breadcrumb, ContextBreadcrumb
    from vertice_core.tui.widgets.token_sparkline import (
        TokenSparkline,
        CompactSparkline,
        MultiSparkline,
    )
    from vertice_core.tui.widgets.image_preview import (
        ImagePreview,
        ImageGallery,
        check_image_support,
    )


# Mapping of names to their (module, attribute) for lazy loading
_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    # Core widgets
    "AutocompleteDropdown": ("vertice_core.tui.widgets.autocomplete", "AutocompleteDropdown"),
    "SelectableStatic": ("vertice_core.tui.widgets.selectable", "SelectableStatic"),
    "ResponseView": ("vertice_core.tui.widgets.response_view", "ResponseView"),
    "StatusBar": ("vertice_core.tui.widgets.status_bar", "StatusBar"),
    # Token Dashboard
    "TokenBreakdown": ("vertice_core.tui.widgets.token_meter", "TokenBreakdown"),
    "TokenMeter": ("vertice_core.tui.widgets.token_meter", "TokenMeter"),
    "TokenBreakdownWidget": ("vertice_core.tui.widgets.token_meter", "TokenBreakdownWidget"),
    "CompressionIndicator": ("vertice_core.tui.widgets.token_meter", "CompressionIndicator"),
    "ThinkingLevelIndicator": ("vertice_core.tui.widgets.token_meter", "ThinkingLevelIndicator"),
    "TokenDashboard": ("vertice_core.tui.widgets.token_meter", "TokenDashboard"),
    "MiniTokenMeter": ("vertice_core.tui.widgets.token_meter", "MiniTokenMeter"),
    # Performance HUD
    "PerformanceHUD": ("vertice_core.tui.widgets.performance_hud", "PerformanceHUD"),
    "FuzzySearchModal": ("vertice_core.tui.widgets.fuzzy_search_modal", "FuzzySearchModal"),
    "ExportModal": ("vertice_core.tui.widgets.export_modal", "ExportModal"),
    # Modal System
    "ConfirmDialog": ("vertice_core.tui.widgets.modal", "ConfirmDialog"),
    "AlertDialog": ("vertice_core.tui.widgets.modal", "AlertDialog"),
    "InputDialog": ("vertice_core.tui.widgets.modal", "InputDialog"),
    "FilePickerDialog": ("vertice_core.tui.widgets.modal", "FilePickerDialog"),
    "ProgressDialog": ("vertice_core.tui.widgets.modal", "ProgressDialog"),
    "confirm": ("vertice_core.tui.widgets.modal", "confirm"),
    "alert": ("vertice_core.tui.widgets.modal", "alert"),
    "prompt": ("vertice_core.tui.widgets.modal", "prompt"),
    # Toast Helpers
    "toast_success": ("vertice_core.tui.widgets.toast", "toast_success"),
    "toast_error": ("vertice_core.tui.widgets.toast", "toast_error"),
    "toast_warning": ("vertice_core.tui.widgets.toast", "toast_warning"),
    "toast_info": ("vertice_core.tui.widgets.toast", "toast_info"),
    "toast_copied": ("vertice_core.tui.widgets.toast", "toast_copied"),
    "ToastMixin": ("vertice_core.tui.widgets.toast", "ToastMixin"),
    # Diff View
    "DiffView": ("vertice_core.tui.widgets.diff_view", "DiffView"),
    "InlineDiff": ("vertice_core.tui.widgets.diff_view", "InlineDiff"),
    "create_diff_text": ("vertice_core.tui.widgets.diff_view", "create_diff_text"),
    # Tool Call Visualization
    "ToolStatus": ("vertice_core.tui.widgets.tool_call", "ToolStatus"),
    "ToolCallData": ("vertice_core.tui.widgets.tool_call", "ToolCallData"),
    "ToolCallWidget": ("vertice_core.tui.widgets.tool_call", "ToolCallWidget"),
    "ToolCallStack": ("vertice_core.tui.widgets.tool_call", "ToolCallStack"),
    # Enhanced Input
    "InputArea": ("vertice_core.tui.widgets.input_area", "InputArea"),
    # Loading Animations
    "SkeletonLine": ("vertice_core.tui.widgets.loading", "SkeletonLine"),
    "SkeletonBlock": ("vertice_core.tui.widgets.loading", "SkeletonBlock"),
    "SpinnerWidget": ("vertice_core.tui.widgets.loading", "SpinnerWidget"),
    "LoadingCard": ("vertice_core.tui.widgets.loading", "LoadingCard"),
    "ThinkingIndicator": ("vertice_core.tui.widgets.loading", "ThinkingIndicator"),
    "ReasoningStream": ("vertice_core.tui.widgets.loading", "ReasoningStream"),
    "PulseIndicator": ("vertice_core.tui.widgets.loading", "PulseIndicator"),
    # Layout & Navigation
    "Sidebar": ("vertice_core.tui.widgets.sidebar", "Sidebar"),
    "FilteredDirectoryTree": ("vertice_core.tui.widgets.sidebar", "FilteredDirectoryTree"),
    "SessionTabs": ("vertice_core.tui.widgets.session_tabs", "SessionTabs"),
    "SessionPane": ("vertice_core.tui.widgets.session_tabs", "SessionPane"),
    "SessionData": ("vertice_core.tui.widgets.session_tabs", "SessionData"),
    "SplitView": ("vertice_core.tui.widgets.split_view", "SplitView"),
    "SplitPane": ("vertice_core.tui.widgets.split_view", "SplitPane"),
    "DualPane": ("vertice_core.tui.widgets.split_view", "DualPane"),
    "Breadcrumb": ("vertice_core.tui.widgets.breadcrumb", "Breadcrumb"),
    "ContextBreadcrumb": ("vertice_core.tui.widgets.breadcrumb", "ContextBreadcrumb"),
    "TokenSparkline": ("vertice_core.tui.widgets.token_sparkline", "TokenSparkline"),
    "CompactSparkline": ("vertice_core.tui.widgets.token_sparkline", "CompactSparkline"),
    "MultiSparkline": ("vertice_core.tui.widgets.token_sparkline", "MultiSparkline"),
    # Image Preview
    "ImagePreview": ("vertice_core.tui.widgets.image_preview", "ImagePreview"),
    "ImageGallery": ("vertice_core.tui.widgets.image_preview", "ImageGallery"),
    "check_image_support": ("vertice_core.tui.widgets.image_preview", "check_image_support"),
}

# Cache for loaded modules
_LOADED: dict[str, Any] = {}


def __getattr__(name: str) -> Any:
    """Lazy import widgets on first access."""
    if name in _LOADED:
        return _LOADED[name]

    if name in _LAZY_IMPORTS:
        module_path, attr_name = _LAZY_IMPORTS[name]
        import importlib

        module = importlib.import_module(module_path)
        value = getattr(module, attr_name)
        _LOADED[name] = value
        return value

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Return available names for autocomplete."""
    return list(_LAZY_IMPORTS.keys())


__all__ = list(_LAZY_IMPORTS.keys()) + [
    # TYPE_CHECKING imports (for type hints only)
    "AutocompleteDropdown",
    "SelectableStatic",
    "ResponseView",
    "StatusBar",
    "TokenBreakdown",
    "TokenMeter",
    "TokenBreakdownWidget",
    "CompressionIndicator",
    "ThinkingLevelIndicator",
    "TokenDashboard",
    "MiniTokenMeter",
    "PerformanceHUD",
    "FuzzySearchModal",
    "ExportModal",
    "ConfirmDialog",
    "AlertDialog",
    "InputDialog",
    "FilePickerDialog",
    "ProgressDialog",
    "confirm",
    "alert",
    "prompt",
    "toast_success",
    "toast_error",
    "toast_warning",
    "toast_info",
    "toast_copied",
    "ToastMixin",
    "DiffView",
    "InlineDiff",
    "create_diff_text",
    "ToolStatus",
    "ToolCallData",
    "ToolCallWidget",
    "ToolCallStack",
    "InputArea",
    "SkeletonLine",
    "SkeletonBlock",
    "SpinnerWidget",
    "LoadingCard",
    "ThinkingIndicator",
    "ReasoningStream",
    "PulseIndicator",
    "Sidebar",
    "FilteredDirectoryTree",
    "SessionTabs",
    "SessionPane",
    "SessionData",
    "SplitView",
    "SplitPane",
    "DualPane",
    "Breadcrumb",
    "ContextBreadcrumb",
    "TokenSparkline",
    "CompactSparkline",
    "MultiSparkline",
    "ImagePreview",
    "ImageGallery",
    "check_image_support",
]
