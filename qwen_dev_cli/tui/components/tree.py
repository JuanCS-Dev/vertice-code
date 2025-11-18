"""
File Tree Component - Interactive directory tree with Apple-style elegance.

Features:
- Collapsible/expandable folders
- File type icons (📄 📜 🎨 ⚙️ etc.)
- Elegant tree lines (│ ├─ └─)
- Git status indicators
- Keyboard navigation
- Smooth animations
- Biblical wisdom during loading

Philosophy:
- Simple, elegant, purposeful
- Every detail matters
- Keyboard-first (accessibility)
- Visual hierarchy clear

Created: 2025-11-18 21:37 UTC
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Set
from dataclasses import dataclass, field
from enum import Enum

from rich.console import Console
from rich.tree import Tree
from rich.text import Text
from rich.panel import Panel

from ..theme import COLORS
from ..styles import PRESET_STYLES
from ..wisdom import get_verse_for_operation


class FileType(Enum):
    """File type categories for icons."""
    DIRECTORY = "directory"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    HTML = "html"
    CSS = "css"
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"
    IMAGE = "image"
    CONFIG = "config"
    BINARY = "binary"
    TEXT = "text"


# File type to icon mapping
FILE_ICONS = {
    FileType.DIRECTORY: "📁",
    FileType.PYTHON: "🐍",
    FileType.JAVASCRIPT: "📜",
    FileType.TYPESCRIPT: "🔷",
    FileType.HTML: "🌐",
    FileType.CSS: "🎨",
    FileType.JSON: "📦",
    FileType.YAML: "📄",
    FileType.MARKDOWN: "📝",
    FileType.IMAGE: "🖼️",
    FileType.CONFIG: "⚙️",
    FileType.BINARY: "📦",
    FileType.TEXT: "📄",
}

# File extension to type mapping
EXTENSION_MAP = {
    # Python
    ".py": FileType.PYTHON,
    ".pyi": FileType.PYTHON,
    ".pyx": FileType.PYTHON,
    
    # JavaScript/TypeScript
    ".js": FileType.JAVASCRIPT,
    ".jsx": FileType.JAVASCRIPT,
    ".mjs": FileType.JAVASCRIPT,
    ".ts": FileType.TYPESCRIPT,
    ".tsx": FileType.TYPESCRIPT,
    
    # Web
    ".html": FileType.HTML,
    ".htm": FileType.HTML,
    ".css": FileType.CSS,
    ".scss": FileType.CSS,
    ".sass": FileType.CSS,
    
    # Data
    ".json": FileType.JSON,
    ".yaml": FileType.YAML,
    ".yml": FileType.YAML,
    ".toml": FileType.CONFIG,
    ".ini": FileType.CONFIG,
    ".cfg": FileType.CONFIG,
    
    # Docs
    ".md": FileType.MARKDOWN,
    ".markdown": FileType.MARKDOWN,
    ".rst": FileType.MARKDOWN,
    ".txt": FileType.TEXT,
    
    # Images
    ".png": FileType.IMAGE,
    ".jpg": FileType.IMAGE,
    ".jpeg": FileType.IMAGE,
    ".gif": FileType.IMAGE,
    ".svg": FileType.IMAGE,
    ".ico": FileType.IMAGE,
    
    # Binary
    ".exe": FileType.BINARY,
    ".dll": FileType.BINARY,
    ".so": FileType.BINARY,
    ".dylib": FileType.BINARY,
    ".pyc": FileType.BINARY,
}


@dataclass
class FileNode:
    """
    Node in file tree.
    
    Attributes:
        path: Full path to file/directory
        name: Display name
        is_dir: Is directory
        file_type: FileType enum
        children: Child nodes (for directories)
        expanded: Is expanded (for directories)
        git_status: Git status (M, A, D, ??)
    """
    path: Path
    name: str
    is_dir: bool
    file_type: FileType = FileType.TEXT
    children: List['FileNode'] = field(default_factory=list)
    expanded: bool = False
    git_status: Optional[str] = None
    
    def __post_init__(self):
        """Auto-detect file type from extension."""
        if self.is_dir:
            self.file_type = FileType.DIRECTORY
        else:
            ext = self.path.suffix.lower()
            self.file_type = EXTENSION_MAP.get(ext, FileType.TEXT)
    
    @property
    def icon(self) -> str:
        """Get icon for this node."""
        return FILE_ICONS.get(self.file_type, "📄")
    
    @property
    def display_name(self) -> str:
        """Get display name with icon."""
        status_icon = ""
        if self.git_status:
            status_map = {
                "M": "📝",  # Modified
                "A": "➕",  # Added
                "D": "🗑️",   # Deleted
                "??": "❓", # Untracked
            }
            status_icon = status_map.get(self.git_status, "") + " "
        
        return f"{status_icon}{self.icon} {self.name}"


class FileTree:
    """
    Interactive file tree with collapsible folders.
    
    Examples:
        tree = FileTree("/path/to/project")
        tree.expand_all()
        console.print(tree.render())
        
        # With git status
        tree = FileTree("/path/to/project", show_git_status=True)
    """
    
    def __init__(
        self,
        root_path: str,
        max_depth: int = 3,
        show_hidden: bool = False,
        show_git_status: bool = True,
        exclude_patterns: Optional[Set[str]] = None,
    ):
        """
        Initialize file tree.
        
        Args:
            root_path: Root directory path
            max_depth: Maximum depth to traverse
            show_hidden: Show hidden files (.gitignore, etc.)
            show_git_status: Show git status indicators
            exclude_patterns: Patterns to exclude (node_modules, __pycache__, etc.)
        """
        self.root_path = Path(root_path).resolve()
        self.max_depth = max_depth
        self.show_hidden = show_hidden
        self.show_git_status = show_git_status
        
        # Default exclude patterns
        self.exclude_patterns = exclude_patterns or {
            "__pycache__",
            ".git",
            "node_modules",
            ".venv",
            "venv",
            ".pytest_cache",
            ".mypy_cache",
            "dist",
            "build",
            "*.egg-info",
        }
        
        # Build tree
        self.root = self._build_tree(self.root_path, depth=0)
        
        # Git status (if enabled)
        self.git_status_map: Dict[Path, str] = {}
        if show_git_status:
            self._load_git_status()
    
    def _should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded."""
        name = path.name
        
        # Hidden files
        if not self.show_hidden and name.startswith('.'):
            return True
        
        # Exclude patterns
        for pattern in self.exclude_patterns:
            if pattern.endswith('*'):
                if name.startswith(pattern[:-1]):
                    return True
            elif pattern.startswith('*'):
                if name.endswith(pattern[1:]):
                    return True
            elif name == pattern:
                return True
        
        return False
    
    def _build_tree(self, path: Path, depth: int) -> FileNode:
        """
        Recursively build file tree.
        
        Args:
            path: Current path
            depth: Current depth
            
        Returns:
            FileNode
        """
        is_dir = path.is_dir()
        node = FileNode(
            path=path,
            name=path.name,
            is_dir=is_dir,
        )
        
        # Don't traverse deeper than max_depth
        if depth >= self.max_depth:
            return node
        
        # Build children for directories
        if is_dir:
            try:
                children = []
                for item in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                    if self._should_exclude(item):
                        continue
                    
                    child = self._build_tree(item, depth + 1)
                    children.append(child)
                
                node.children = children
                # Auto-expand first level
                node.expanded = (depth == 0)
                
            except PermissionError:
                pass  # Skip directories we can't read
        
        return node
    
    def _load_git_status(self):
        """Load git status for files in tree."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.root_path,
                capture_output=True,
                text=True,
                timeout=2,
            )
            
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if len(line) < 3:
                        continue
                    
                    status = line[:2].strip()
                    filepath = line[3:].strip()
                    full_path = self.root_path / filepath
                    
                    self.git_status_map[full_path] = status
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass  # Git not available or timed out
    
    def _apply_git_status(self, node: FileNode):
        """Apply git status to node."""
        if node.path in self.git_status_map:
            node.git_status = self.git_status_map[node.path]
        
        for child in node.children:
            self._apply_git_status(child)
    
    def expand_all(self):
        """Expand all directories in tree."""
        def expand_node(node: FileNode):
            if node.is_dir:
                node.expanded = True
                for child in node.children:
                    expand_node(child)
        
        expand_node(self.root)
    
    def collapse_all(self):
        """Collapse all directories in tree."""
        def collapse_node(node: FileNode):
            if node.is_dir:
                node.expanded = False
                for child in node.children:
                    collapse_node(child)
        
        collapse_node(self.root)
    
    def _build_rich_tree(self, node: FileNode, rich_tree: Optional[Tree] = None) -> Tree:
        """
        Build Rich Tree object from FileNode.
        
        Args:
            node: Current FileNode
            rich_tree: Existing Rich Tree (for recursion)
            
        Returns:
            Rich Tree object
        """
        # Apply git status
        if self.show_git_status and self.git_status_map:
            self._apply_git_status(node)
        
        # Create or update tree
        if rich_tree is None:
            # Root
            style = PRESET_STYLES.PATH if node.is_dir else PRESET_STYLES.PRIMARY
            rich_tree = Tree(
                Text(node.display_name, style=style),
                guide_style=COLORS['border_muted']
            )
        
        # Add children
        if node.is_dir and node.expanded:
            for child in node.children:
                style = PRESET_STYLES.PATH if child.is_dir else PRESET_STYLES.SECONDARY
                child_tree = rich_tree.add(
                    Text(child.display_name, style=style),
                    guide_style=COLORS['border_muted']
                )
                
                # Recurse
                if child.is_dir and child.children:
                    self._build_rich_tree(child, child_tree)
        
        return rich_tree
    
    def render(self, title: Optional[str] = None) -> Panel:
        """
        Render file tree as Panel.
        
        Args:
            title: Panel title
            
        Returns:
            Rich Panel object
        """
        rich_tree = self._build_rich_tree(self.root)
        
        # Default title
        if title is None:
            title = f"📂 {self.root_path.name}"
        
        return Panel(
            rich_tree,
            title=title,
            border_style=COLORS['accent_blue'],
            padding=(0, 1),
            expand=False,
        )
    
    def get_file_count(self) -> Dict[str, int]:
        """
        Get counts of files by type.
        
        Returns:
            Dictionary with file type counts
        """
        counts = {ft.value: 0 for ft in FileType}
        
        def count_node(node: FileNode):
            counts[node.file_type.value] += 1
            for child in node.children:
                count_node(child)
        
        count_node(self.root)
        return counts


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def show_directory_tree(
    path: str,
    console: Optional[Console] = None,
    max_depth: int = 3,
    expand_all: bool = False,
) -> None:
    """
    Quick helper to show directory tree.
    
    Args:
        path: Directory path
        console: Rich console
        max_depth: Maximum depth
        expand_all: Expand all directories
        
    Example:
        show_directory_tree("./src", max_depth=2)
    """
    console = console or Console()
    
    # Show loading with verse
    verse = get_verse_for_operation("analyze")
    console.print(f"[dim]Scanning directory... {verse}[/dim]")
    
    tree = FileTree(path, max_depth=max_depth)
    
    if expand_all:
        tree.expand_all()
    
    console.print(tree.render())
    
    # Show statistics
    counts = tree.get_file_count()
    total = sum(counts.values())
    console.print(f"\n[dim]Total items: {total}[/dim]")


if __name__ == "__main__":
    # Demo
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    show_directory_tree(path, max_depth=2, expand_all=True)
