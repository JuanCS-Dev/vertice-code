"""
MAESTRO v10.0 - File Operations Panel Component

Real-time file tree with diff visualization and status tracking.
"""

from typing import List
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich.console import Group
from rich.padding import Padding
from rich.style import Style
from rich.box import ROUNDED

from ..theme import COLORS
from .maestro_data_structures import FileOperation, FileStatus


class FileOperationsPanel:
    """
    Real-time file tree with diff visualization.

    Features:
    - Live file status tracking
    - Inline diff summaries (+/- lines)
    - Color-coded status indicators
    - Grouped by directory structure
    """

    def __init__(self, root_label: str = "📁 project/"):
        """
        Initialize file operations panel.

        Args:
            root_label: Label for root of file tree
        """
        self.operations: List[FileOperation] = []
        self.root_label = root_label

    def add_operation(self, operation: FileOperation):
        """
        Add file operation to tracker.

        Args:
            operation: FileOperation to add
        """
        # Check if path already exists
        existing_idx = None
        for i, op in enumerate(self.operations):
            if op.path == operation.path:
                existing_idx = i
                break

        if existing_idx is not None:
            # Update existing operation
            self.operations[existing_idx] = operation
        else:
            # Add new operation
            self.operations.append(operation)

        # Keep only recent operations (memory management)
        if len(self.operations) > 50:
            self.operations = self.operations[-50:]

    def clear_operations(self):
        """Clear all operations"""
        self.operations.clear()

    def render(self, max_display: int = 15) -> Panel:
        """
        Render file operations panel.

        Args:
            max_display: Maximum number of files to display

        Returns:
            Rich Panel ready for rendering
        """
        # Build header
        header = self._build_header()

        # Build file tree
        tree = self._build_file_tree(max_display)

        # Build diff summary
        diff_summary = self._build_diff_summary()

        # Combine tree + diff summary
        if diff_summary:
            content = Group(tree, Padding(diff_summary, (1, 0, 0, 0)))
        else:
            content = tree

        return Panel(
            content,
            title=header,
            border_style=COLORS["neon_blue"],
            box=ROUNDED,
            padding=(1, 2),
            style=Style(bgcolor=COLORS["bg_card"]),
        )

    def _build_header(self) -> Text:
        """
        Build panel header.

        Returns:
            Formatted Text object for header
        """
        header = Text()
        header.append("💾 ", style=f"bold {COLORS['neon_blue']}")
        header.append("FILE OPERATIONS", style=f"bold {COLORS['neon_blue']}")

        # File count
        if self.operations:
            count = len(set(op.path for op in self.operations))
            header.append(f" [{count} FILES]", style=f"dim {COLORS['text_secondary']}")

        return header

    def _build_file_tree(self, max_display: int) -> Tree:
        """
        Build file tree with recent operations.

        Args:
            max_display: Maximum files to display

        Returns:
            Rich Tree object
        """
        tree = Tree(self.root_label, style=COLORS["neon_blue"], guide_style=COLORS["border_muted"])

        # Get recent operations (sorted by timestamp)
        recent_ops = sorted(
            self.operations[-max_display:], key=lambda op: op.timestamp, reverse=True
        )

        for op in recent_ops:
            file_node = self._format_file_node(op)
            tree.add(file_node)

        # Add placeholder if empty
        if not recent_ops:
            empty_text = Text("No file operations yet", style=COLORS["text_tertiary"])
            tree.add(empty_text)

        return tree

    def _format_file_node(self, op: FileOperation) -> Text:
        """
        Format file node with status and styling.

        Args:
            op: FileOperation to format

        Returns:
            Formatted Text object
        """
        file_text = Text()

        # Status icon and color
        if op.status == FileStatus.MODIFIED:
            icon = "📝"
            status_style = COLORS["neon_yellow"]
            suffix = " (modified)"
        elif op.status == FileStatus.SAVED:
            icon = "✓"
            status_style = COLORS["neon_green"]
            suffix = " (saved)"
        elif op.status == FileStatus.CREATING:
            icon = "✨"
            status_style = COLORS["neon_cyan"]
            suffix = " (creating...)"
        elif op.status == FileStatus.ANALYZING:
            icon = "🔍"
            status_style = COLORS["neon_purple"]
            suffix = " (analyzing...)"
        elif op.status == FileStatus.ERROR:
            icon = "✗"
            status_style = COLORS["neon_red"]
            suffix = " (error)"
        else:
            icon = "📄"
            status_style = COLORS["text_secondary"]
            suffix = ""

        # Build node text
        file_text.append(f"{icon} ", style=status_style)
        file_text.append(op.path, style=status_style)
        file_text.append(suffix, style=f"dim {status_style}")

        # Add inline diff if available
        if op.has_diff:
            file_text.append(" ", style="")
            if op.lines_added > 0:
                file_text.append(f"+{op.lines_added}", style=f"bold {COLORS['diff_add_text']}")
            if op.lines_removed > 0:
                if op.lines_added > 0:
                    file_text.append(" ", style="")
                file_text.append(f"-{op.lines_removed}", style=f"bold {COLORS['diff_remove_text']}")

        return file_text

    def _build_diff_summary(self) -> Text | None:
        """
        Build diff summary panel.

        Returns:
            Text with diff summary or None if no diffs
        """
        # Calculate total diff
        total_added = sum(op.lines_added for op in self.operations)
        total_removed = sum(op.lines_removed for op in self.operations)

        if total_added == 0 and total_removed == 0:
            return None

        diff_text = Text()

        # Added lines
        if total_added > 0:
            # Visual bar (scale down for display)
            bar_length = min(15, total_added // 10)
            added_bar = "█" * bar_length if bar_length > 0 else "▏"

            diff_text.append(f"+{total_added} lines ", style=f"bold {COLORS['diff_add_text']}")
            diff_text.append(added_bar, style=COLORS["diff_add_text"])
            diff_text.append("\n")

        # Removed lines
        if total_removed > 0:
            # Visual bar (scale down for display)
            bar_length = min(10, total_removed // 10)
            removed_bar = "█" * bar_length if bar_length > 0 else "▏"

            diff_text.append(f"-{total_removed} lines ", style=f"bold {COLORS['diff_remove_text']}")
            diff_text.append(removed_bar, style=COLORS["diff_remove_text"])

        return diff_text

    def get_operation_by_path(self, path: str) -> FileOperation | None:
        """
        Get operation by file path.

        Args:
            path: File path to search for

        Returns:
            FileOperation if found, None otherwise
        """
        for op in reversed(self.operations):
            if op.path == path:
                return op
        return None

    def get_total_changes(self) -> tuple[int, int]:
        """
        Get total changes across all operations.

        Returns:
            Tuple of (total_added, total_removed)
        """
        total_added = sum(op.lines_added for op in self.operations)
        total_removed = sum(op.lines_removed for op in self.operations)
        return (total_added, total_removed)

    def get_files_by_status(self, status: FileStatus) -> List[FileOperation]:
        """
        Get all files with specific status.

        Args:
            status: FileStatus to filter by

        Returns:
            List of FileOperations matching status
        """
        return [op for op in self.operations if op.status == status]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def create_file_operation_from_event(
    path: str, event_type: str, lines_added: int = 0, lines_removed: int = 0
) -> FileOperation:
    """
    Create FileOperation from event data.

    Args:
        path: File path
        event_type: Event type string ("read", "write", "create", "analyze")
        lines_added: Number of lines added
        lines_removed: Number of lines removed

    Returns:
        FileOperation instance
    """
    # Map event type to FileStatus
    status_map = {
        "read": FileStatus.ANALYZING,
        "analyze": FileStatus.ANALYZING,
        "write": FileStatus.MODIFIED,
        "modify": FileStatus.MODIFIED,
        "create": FileStatus.CREATING,
        "save": FileStatus.SAVED,
        "error": FileStatus.ERROR,
    }

    status = status_map.get(event_type.lower(), FileStatus.ANALYZING)

    return FileOperation(
        path=path, status=status, lines_added=lines_added, lines_removed=lines_removed
    )
