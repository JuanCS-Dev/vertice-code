"""
TUI Components - Reusable UI building blocks.

Component library for consistent, beautiful terminal UI.

Philosophy:
- Composable and reusable
- Consistent styling
- Accessible by default
- Performant (60 FPS target)

Components Implemented:
✅ message.py - Message boxes with typing effect
✅ status.py - Status badges and spinners
✅ progress.py - Animated progress bars
✅ code.py - Enhanced code blocks
✅ diff.py - Diff viewer (GitHub style)
✅ file_tree.py - Collapsible file tree (Cursor-style)
✅ pills.py - Context pills (Cursor @ mentions)
✅ toast.py - Notification toasts (VSCode-style)
✅ autocomplete.py - Context-aware autocomplete

Created: 2025-11-18 20:05 UTC
Updated: 2025-11-19 00:45 UTC
Status: Phase 3 Complete - Advanced Components
"""

__version__ = "3.0.0"
__status__ = "Phase 3 Complete - Advanced Components"

# Core components
from .message import MessageBox, Message, MessageRole, create_assistant_message, create_user_message
from .status import StatusBadge, StatusLevel, Spinner, SpinnerStyle, create_processing_indicator
from .progress import ProgressBar, ProgressState, ProgressStyle, create_progress_bar
from .code import CodeBlock, CodeSnippet, InlineCode, create_code_block
from .diff import DiffViewer, DiffMode, DiffLine

# Advanced components (Cursor-inspired)
from .file_tree import FileTree, FileNode, FileType, create_file_tree
from .pills import ContextPill, PillContainer, PillType, create_pill_from_file
from .toasts import (
    Toast, ToastManager, ToastType,
    show_success, show_error, show_info, show_warning, show_wisdom,
    create_toast_manager
)
from .autocomplete import (
    ContextAwareCompleter, SmartAutoSuggest, CompletionItem, CompletionType,
    create_completer
)

__all__ = [
    # Core
    "MessageBox", "Message", "MessageRole", "create_assistant_message", "create_user_message",
    "StatusBadge", "StatusLevel", "Spinner", "SpinnerStyle", "create_processing_indicator",
    "ProgressBar", "ProgressState", "ProgressStyle", "create_progress_bar",
    "CodeBlock", "CodeSnippet", "InlineCode", "create_code_block",
    "DiffViewer", "DiffMode", "DiffLine",
    
    # Advanced
    "FileTree", "FileNode", "FileType", "create_file_tree",
    "ContextPill", "PillContainer", "PillType", "create_pill_from_file",
    "Toast", "ToastManager", "ToastType",
    "show_success", "show_error", "show_info", "show_warning", "show_wisdom",
    "create_toast_manager",
    "ContextAwareCompleter", "SmartAutoSuggest", "CompletionItem", "CompletionType",
    "create_completer"
]
