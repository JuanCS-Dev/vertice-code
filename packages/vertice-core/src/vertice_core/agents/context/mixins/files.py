"""
File Context Mixin - Manages file context (Claude Code pattern).
"""

from typing import Dict, List, Optional

from ..types import FileContext


class FileContextMixin:
    """Mixin for managing file context."""

    def __init__(self) -> None:
        self._files: Dict[str, FileContext] = {}

    def add_file(
        self,
        filepath: str,
        content: str,
        language: Optional[str] = None,
        start_line: int = 1,
        end_line: int = 0,
        added_by: str = "",
    ) -> bool:
        """
        Add a file to context.

        Args:
            filepath: Path to the file
            content: File content
            language: Programming language
            start_line: Start line number
            end_line: End line number
            added_by: Agent or user who added it

        Returns:
            True if added, False if already exists
        """
        if filepath in self._files:
            return False

        # Estimate tokens (rough approximation)
        tokens = len(content) // 4

        self._files[filepath] = FileContext(
            filepath=filepath,
            content=content,
            language=language or "",
            start_line=start_line,
            end_line=end_line or len(content.split("\n")),
            tokens=tokens,
            added_by=added_by,
        )

        # Update token usage
        if hasattr(self, "_token_usage"):
            self._token_usage += tokens

        return True

    def remove_file(self, filepath: str) -> bool:
        """Remove a file from context."""
        if filepath in self._files:
            # Update token usage
            if hasattr(self, "_token_usage"):
                self._token_usage -= self._files[filepath].tokens
            del self._files[filepath]
            return True
        return False

    def get_file(self, filepath: str) -> Optional[FileContext]:
        """Get a file from context."""
        return self._files.get(filepath)

    def list_files(self) -> List[str]:
        """List all files in context."""
        return list(self._files.keys())

    def files(self) -> Dict[str, FileContext]:
        """Get all files in context."""
        return self._files.copy()
