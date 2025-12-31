"""
FileContextWindow - Claude Code-style File Context Management.

Implements /add, /remove, /context commands for explicit file inclusion.
Tracks token usage and auto-prunes low-priority entries.

Phase 10: Refinement Sprint 1

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Token estimation (4 chars per token is a reasonable heuristic)
CHARS_PER_TOKEN = 4


@dataclass
class FileContextEntry:
    """A single file entry in the context window."""

    filepath: str
    content: str
    start_line: int
    end_line: int
    tokens: int
    priority: float = 1.0  # 1.0 = highest, 0.0 = lowest
    added_at: datetime = field(default_factory=datetime.now)
    language: str = "text"

    @classmethod
    def from_file(
        cls,
        filepath: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        priority: float = 1.0,
    ) -> "FileContextEntry":
        """Create entry from file path with optional line range."""
        path = Path(filepath).expanduser().resolve()

        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        if not path.is_file():
            raise ValueError(f"Not a file: {filepath}")

        # Read file
        full_content = path.read_text(encoding="utf-8", errors="replace")
        lines = full_content.splitlines(keepends=True)

        # Handle line range (1-indexed)
        actual_start = (start_line - 1) if start_line else 0
        actual_end = end_line if end_line else len(lines)

        # Clamp to valid range
        actual_start = max(0, min(actual_start, len(lines)))
        actual_end = max(actual_start, min(actual_end, len(lines)))

        content = "".join(lines[actual_start:actual_end])
        tokens = len(content) // CHARS_PER_TOKEN

        # Detect language from extension
        language = _detect_language(path.suffix)

        return cls(
            filepath=str(path),
            content=content,
            start_line=actual_start + 1,  # Back to 1-indexed
            end_line=actual_end,
            tokens=tokens,
            priority=priority,
            language=language,
        )

    def to_context_string(self) -> str:
        """Format entry for inclusion in LLM context."""
        header = f"### File: {self.filepath}"
        if self.start_line != 1 or self.end_line != self.content.count("\n") + 1:
            header += f" (lines {self.start_line}-{self.end_line})"

        return f"{header}\n```{self.language}\n{self.content}\n```\n"


class FileContextWindow:
    """
    Manages explicit file context for LLM conversations.

    Features:
    - Add/remove files to context
    - Line range support (/add file.py:10-50)
    - Token tracking and limits
    - Auto-prune low-priority entries
    - Priority-based ordering

    Usage:
        window = FileContextWindow(max_tokens=32000)
        window.add("src/main.py")
        window.add("config.yaml", lines=(1, 50))
        context = window.get_context_string()
    """

    DEFAULT_MAX_TOKENS = 32_000

    def __init__(self, max_tokens: int = DEFAULT_MAX_TOKENS) -> None:
        """Initialize context window with token limit."""
        self._entries: Dict[str, FileContextEntry] = {}
        self._max_tokens = max_tokens
        self._lock = threading.Lock()

    @property
    def max_tokens(self) -> int:
        """Maximum tokens allowed in context."""
        return self._max_tokens

    @max_tokens.setter
    def max_tokens(self, value: int) -> None:
        """Set maximum tokens (triggers auto-prune if needed)."""
        self._max_tokens = value
        self._auto_prune()

    @property
    def total_tokens(self) -> int:
        """Total tokens currently in context."""
        with self._lock:
            return sum(e.tokens for e in self._entries.values())

    @property
    def remaining_tokens(self) -> int:
        """Tokens available before hitting limit."""
        return max(0, self._max_tokens - self.total_tokens)

    @property
    def utilization(self) -> float:
        """Context utilization as percentage (0.0 to 1.0)."""
        if self._max_tokens == 0:
            return 1.0
        return self.total_tokens / self._max_tokens

    def add(
        self,
        filepath: str,
        lines: Optional[Tuple[int, int]] = None,
        priority: float = 1.0,
    ) -> Tuple[bool, str]:
        """
        Add a file to the context window.

        Args:
            filepath: Path to file (absolute or relative)
            lines: Optional (start, end) line range (1-indexed)
            priority: Priority for auto-pruning (1.0 = keep, 0.0 = remove first)

        Returns:
            (success: bool, message: str)
        """
        try:
            start_line = lines[0] if lines else None
            end_line = lines[1] if lines else None

            entry = FileContextEntry.from_file(
                filepath,
                start_line=start_line,
                end_line=end_line,
                priority=priority,
            )

            # Check if adding would exceed limit
            if entry.tokens > self.remaining_tokens:
                # Try auto-pruning
                self._auto_prune()
                if entry.tokens > self.remaining_tokens:
                    return (
                        False,
                        f"Not enough space. Need {entry.tokens} tokens, "
                        f"have {self.remaining_tokens} available.",
                    )

            with self._lock:
                # Use normalized path as key
                key = entry.filepath
                self._entries[key] = entry

            return (True, f"Added {entry.filepath} ({entry.tokens} tokens)")

        except FileNotFoundError as e:
            return (False, str(e))
        except ValueError as e:
            return (False, str(e))
        except Exception as e:
            return (False, f"Error adding file: {e}")

    def remove(self, filepath: str) -> Tuple[bool, str]:
        """
        Remove a file from the context window.

        Args:
            filepath: Path to file (can be partial match)

        Returns:
            (success: bool, message: str)
        """
        with self._lock:
            # Try exact match first
            resolved = str(Path(filepath).expanduser().resolve())
            if resolved in self._entries:
                entry = self._entries.pop(resolved)
                return (True, f"Removed {entry.filepath} ({entry.tokens} tokens freed)")

            # Try partial match (filename only)
            filename = Path(filepath).name
            for key, entry in list(self._entries.items()):
                if Path(key).name == filename:
                    self._entries.pop(key)
                    return (True, f"Removed {entry.filepath} ({entry.tokens} tokens freed)")

            return (False, f"File not in context: {filepath}")

    def clear(self) -> int:
        """Clear all entries. Returns number of entries removed."""
        with self._lock:
            count = len(self._entries)
            self._entries.clear()
            return count

    def get_entry(self, filepath: str) -> Optional[FileContextEntry]:
        """Get a specific entry by filepath."""
        with self._lock:
            resolved = str(Path(filepath).expanduser().resolve())
            return self._entries.get(resolved)

    def list_entries(self) -> List[FileContextEntry]:
        """Get all entries sorted by priority (highest first)."""
        with self._lock:
            return sorted(
                self._entries.values(),
                key=lambda e: (-e.priority, e.added_at),
            )

    def get_context_string(self) -> str:
        """
        Generate the full context string for LLM inclusion.

        Returns formatted text with all files.
        """
        entries = self.list_entries()
        if not entries:
            return ""

        parts = ["## Files in Context\n"]
        for entry in entries:
            parts.append(entry.to_context_string())

        return "\n".join(parts)

    def get_token_usage(self) -> Tuple[int, int]:
        """
        Get token usage.

        Returns:
            (used_tokens, max_tokens)
        """
        return (self.total_tokens, self._max_tokens)

    def get_summary(self) -> str:
        """Get a human-readable summary of context state."""
        entries = self.list_entries()
        used, max_tok = self.get_token_usage()
        pct = (used / max_tok * 100) if max_tok > 0 else 0

        lines = [
            f"Context: {used:,}/{max_tok:,} tokens ({pct:.1f}%)",
            f"Files: {len(entries)}",
        ]

        if entries:
            lines.append("")
            for entry in entries:
                line_info = ""
                if entry.start_line != 1 or entry.end_line > 1:
                    line_info = f":{entry.start_line}-{entry.end_line}"
                lines.append(f"  {Path(entry.filepath).name}{line_info} ({entry.tokens} tok)")

        return "\n".join(lines)

    def _auto_prune(self) -> List[str]:
        """
        Automatically remove low-priority entries if over limit.

        Returns list of removed filepaths.
        """
        removed = []

        with self._lock:
            while self.total_tokens > self._max_tokens and self._entries:
                # Find lowest priority entry
                lowest = min(
                    self._entries.values(),
                    key=lambda e: (e.priority, -e.added_at.timestamp()),
                )

                # Don't remove high-priority entries
                if lowest.priority >= 0.8:
                    break

                del self._entries[lowest.filepath]
                removed.append(lowest.filepath)

        return removed

    def update_priority(self, filepath: str, priority: float) -> bool:
        """Update priority for an existing entry."""
        with self._lock:
            resolved = str(Path(filepath).expanduser().resolve())
            if resolved in self._entries:
                entry = self._entries[resolved]
                # Create new entry with updated priority
                self._entries[resolved] = FileContextEntry(
                    filepath=entry.filepath,
                    content=entry.content,
                    start_line=entry.start_line,
                    end_line=entry.end_line,
                    tokens=entry.tokens,
                    priority=priority,
                    added_at=entry.added_at,
                    language=entry.language,
                )
                return True
            return False


def _detect_language(suffix: str) -> str:
    """Detect programming language from file extension."""
    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".html": "html",
        ".css": "css",
        ".sql": "sql",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".toml": "toml",
        ".ini": "ini",
        ".xml": "xml",
    }
    return language_map.get(suffix.lower(), "text")


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_file_context_window: Optional[FileContextWindow] = None
_window_lock = threading.Lock()


def get_file_context_window() -> FileContextWindow:
    """Get or create the singleton FileContextWindow instance."""
    global _file_context_window
    if _file_context_window is None:
        with _window_lock:
            if _file_context_window is None:
                _file_context_window = FileContextWindow()
    return _file_context_window


__all__ = [
    "FileContextEntry",
    "FileContextWindow",
    "get_file_context_window",
]
