"""
Sidebar - File Explorer with DirectoryTree.

Uses Textual's DirectoryTree with enhancements:
- Recent files section
- Bookmarks with Collapsible
- Toggle visibility (Ctrl+B)
- Filter hidden files

Phase 11: Visual Upgrade - Layout & Navigation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, List, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Static, DirectoryTree, Collapsible
from textual.reactive import reactive
from textual.widget import Widget
from textual.message import Message


class FilteredDirectoryTree(DirectoryTree):
    """DirectoryTree that filters hidden files and common ignore patterns."""

    IGNORE_PATTERNS = {
        ".git",
        ".svn",
        ".hg",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        ".venv",
        "venv",
        ".env",
        ".idea",
        ".vscode",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        "*.egg-info",
    }

    def filter_paths(self, paths: list[Path]) -> list[Path]:
        """Filter out hidden files and ignored directories."""
        return [
            path
            for path in paths
            if not path.name.startswith(".")
            and path.name not in self.IGNORE_PATTERNS
            and not any(
                path.name.endswith(p.replace("*", "")) for p in self.IGNORE_PATTERNS if "*" in p
            )
        ]


class RecentFileItem(Static):
    """Single recent file item."""

    DEFAULT_CSS = """
    RecentFileItem {
        width: 100%;
        height: 1;
        padding: 0 1;
    }

    RecentFileItem:hover {
        background: $accent 20%;
    }
    """

    def __init__(self, path: Path, id: Optional[str] = None) -> None:
        self.path = path
        display = f"📄 {path.name}"
        super().__init__(display, id=id)

    def on_click(self) -> None:
        self.post_message(Sidebar.FileSelected(self.path))


class BookmarkItem(Static):
    """Single bookmark item."""

    DEFAULT_CSS = """
    BookmarkItem {
        width: 100%;
        height: 1;
        padding: 0 1;
    }

    BookmarkItem:hover {
        background: $accent 20%;
    }

    BookmarkItem .bookmark-icon {
        color: $warning;
    }
    """

    def __init__(self, path: Path, id: Optional[str] = None) -> None:
        self.path = path
        icon = "📁" if path.is_dir() else "📄"
        display = f"⭐ {icon} {path.name}"
        super().__init__(display, id=id)

    def on_click(self) -> None:
        if self.path.is_dir():
            self.post_message(Sidebar.DirectorySelected(self.path))
        else:
            self.post_message(Sidebar.FileSelected(self.path))


class Sidebar(Widget):
    """
    File explorer sidebar with DirectoryTree.

    Features:
    - DirectoryTree with filtering
    - Recent files (Collapsible)
    - Bookmarks (Collapsible)
    - Toggle with Ctrl+B
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+b", "toggle_sidebar", "Toggle Sidebar", show=True),
    ]

    DEFAULT_CSS = """
    Sidebar {
        width: 35;
        height: 100%;
        dock: left;
        background: $surface;
        border-right: solid $border;
    }

    Sidebar.hidden {
        display: none;
    }

    Sidebar .sidebar-header {
        width: 100%;
        height: 1;
        background: $panel;
        padding: 0 1;
        text-style: bold;
    }

    Sidebar DirectoryTree {
        width: 100%;
        height: 1fr;
        padding: 0;
    }

    Sidebar Collapsible {
        width: 100%;
        padding: 0;
    }

    Sidebar .section-empty {
        color: $text-muted;
        padding: 0 2;
        height: 1;
    }
    """

    is_visible: reactive[bool] = reactive(True)

    class FileSelected(Message):
        """File was selected in sidebar."""

        def __init__(self, path: Path) -> None:
            self.path = path
            super().__init__()

    class DirectorySelected(Message):
        """Directory was selected in sidebar."""

        def __init__(self, path: Path) -> None:
            self.path = path
            super().__init__()

    def __init__(
        self,
        root: Path | str = ".",
        id: Optional[str] = None,
    ) -> None:
        super().__init__(id=id)
        self._root = Path(root).resolve()
        self._recent_files: List[Path] = []
        self._bookmarks: List[Path] = []

    def compose(self) -> ComposeResult:
        yield Static("📂 EXPLORER", classes="sidebar-header")

        with VerticalScroll():
            # Bookmarks section
            with Collapsible(title="⭐ Bookmarks", collapsed=True, id="bookmarks-section"):
                yield Vertical(id="bookmarks-list")

            # Recent files section
            with Collapsible(title="🕐 Recent", collapsed=True, id="recent-section"):
                yield Vertical(id="recent-list")

            # Directory tree
            yield FilteredDirectoryTree(self._root, id="dir-tree")

    def on_mount(self) -> None:
        self._update_bookmarks()
        self._update_recent()

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection from tree."""
        self.add_recent(event.path)
        self.post_message(self.FileSelected(event.path))

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        """Handle directory selection from tree."""
        self.post_message(self.DirectorySelected(event.path))

    def watch_is_visible(self, visible: bool) -> None:
        """Toggle sidebar visibility."""
        if visible:
            self.remove_class("hidden")
        else:
            self.add_class("hidden")

    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        self.is_visible = not self.is_visible

    def toggle(self) -> None:
        """Public method to toggle sidebar."""
        self.action_toggle_sidebar()

    def add_recent(self, path: Path) -> None:
        """Add file to recent list."""
        path = Path(path).resolve()
        if path in self._recent_files:
            self._recent_files.remove(path)
        self._recent_files.insert(0, path)
        self._recent_files = self._recent_files[:10]  # Keep last 10
        self._update_recent()

    def add_bookmark(self, path: Path) -> None:
        """Add path to bookmarks."""
        path = Path(path).resolve()
        if path not in self._bookmarks:
            self._bookmarks.append(path)
            self._update_bookmarks()

    def remove_bookmark(self, path: Path) -> None:
        """Remove path from bookmarks."""
        path = Path(path).resolve()
        if path in self._bookmarks:
            self._bookmarks.remove(path)
            self._update_bookmarks()

    def _update_recent(self) -> None:
        """Update recent files display."""
        try:
            container = self.query_one("#recent-list", Vertical)
            container.remove_children()

            if not self._recent_files:
                container.mount(Static("No recent files", classes="section-empty"))
            else:
                for path in self._recent_files[:5]:
                    container.mount(RecentFileItem(path))
        except (AttributeError, ValueError, RuntimeError):
            pass

    def _update_bookmarks(self) -> None:
        """Update bookmarks display."""
        try:
            container = self.query_one("#bookmarks-list", Vertical)
            container.remove_children()

            if not self._bookmarks:
                container.mount(Static("No bookmarks", classes="section-empty"))
            else:
                for path in self._bookmarks:
                    container.mount(BookmarkItem(path))
        except (AttributeError, ValueError, RuntimeError):
            pass

    def refresh_tree(self) -> None:
        """Refresh the directory tree."""
        try:
            tree = self.query_one("#dir-tree", FilteredDirectoryTree)
            tree.reload()
        except (AttributeError, ValueError):
            pass

    def set_root(self, path: Path | str) -> None:
        """Change the root directory."""
        self._root = Path(path).resolve()
        try:
            tree = self.query_one("#dir-tree", FilteredDirectoryTree)
            tree.path = self._root
            tree.reload()
        except (AttributeError, ValueError):
            pass
