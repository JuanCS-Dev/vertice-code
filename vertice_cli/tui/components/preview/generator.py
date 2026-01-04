"""
Diff Generator - Generate structured diffs from old/new content.

Uses Python's difflib for accurate line-by-line comparison.
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import List

from .types import ChangeType, DiffHunk, DiffLine, FileDiff


class DiffGenerator:
    """Generate structured diffs from old/new content.

    Uses Python's difflib for accurate line-by-line comparison.
    """

    @staticmethod
    def generate_diff(
        old_content: str,
        new_content: str,
        file_path: str,
        language: str = "python",
        context_lines: int = 3,
    ) -> FileDiff:
        """Generate a structured diff.

        Args:
            old_content: Original file content.
            new_content: Proposed new content.
            file_path: Path to file (for display).
            language: Language for syntax highlighting.
            context_lines: Number of context lines around changes.

        Returns:
            FileDiff object with hunks.
        """
        old_lines = old_content.splitlines(keepends=False)
        new_lines = new_content.splitlines(keepends=False)

        # Use SequenceMatcher for better diff detection
        matcher = SequenceMatcher(None, old_lines, new_lines)
        hunks = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                # Skip unchanged blocks (unless in context)
                continue

            # Build hunk with context
            context_start_old = max(0, i1 - context_lines)
            context_end_old = min(len(old_lines), i2 + context_lines)
            context_start_new = max(0, j1 - context_lines)
            context_end_new = min(len(new_lines), j2 + context_lines)

            hunk_lines = []

            # Add context before
            for i in range(context_start_old, i1):
                hunk_lines.append(
                    DiffLine(
                        line_num_old=i + 1,
                        line_num_new=context_start_new + (i - context_start_old) + 1,
                        content=old_lines[i],
                        change_type=ChangeType.UNCHANGED,
                    )
                )

            # Add changed lines
            if tag == "replace":
                # Modified lines
                for i in range(i1, i2):
                    hunk_lines.append(
                        DiffLine(
                            line_num_old=i + 1,
                            line_num_new=None,
                            content=old_lines[i],
                            change_type=ChangeType.REMOVED,
                        )
                    )
                for j in range(j1, j2):
                    hunk_lines.append(
                        DiffLine(
                            line_num_old=None,
                            line_num_new=j + 1,
                            content=new_lines[j],
                            change_type=ChangeType.ADDED,
                        )
                    )
            elif tag == "delete":
                # Deleted lines
                for i in range(i1, i2):
                    hunk_lines.append(
                        DiffLine(
                            line_num_old=i + 1,
                            line_num_new=None,
                            content=old_lines[i],
                            change_type=ChangeType.REMOVED,
                        )
                    )
            elif tag == "insert":
                # Added lines
                for j in range(j1, j2):
                    hunk_lines.append(
                        DiffLine(
                            line_num_old=None,
                            line_num_new=j + 1,
                            content=new_lines[j],
                            change_type=ChangeType.ADDED,
                        )
                    )

            # Add context after
            for i in range(i2, context_end_old):
                hunk_lines.append(
                    DiffLine(
                        line_num_old=i + 1,
                        line_num_new=j2 + (i - i2) + 1,
                        content=old_lines[i],
                        change_type=ChangeType.UNCHANGED,
                    )
                )

            # Create hunk
            hunk = DiffHunk(
                old_start=context_start_old + 1,
                old_count=context_end_old - context_start_old,
                new_start=context_start_new + 1,
                new_count=context_end_new - context_start_new,
                lines=hunk_lines,
                context=DiffGenerator._extract_context(old_lines, i1),
            )
            hunks.append(hunk)

        return FileDiff(
            file_path=file_path,
            language=language,
            old_content=old_content,
            new_content=new_content,
            hunks=hunks,
        )

    @staticmethod
    def _extract_context(lines: List[str], line_num: int) -> str:
        """Extract function/class context for hunk header.

        Args:
            lines: All lines in the file.
            line_num: Current line number.

        Returns:
            Function/class name if found, empty string otherwise.
        """
        # Look backwards for function/class definition
        for i in range(line_num - 1, max(0, line_num - 20), -1):
            line = lines[i].strip()
            if line.startswith("def ") or line.startswith("class "):
                # Extract function/class name
                name = (
                    line.split("(")[0]
                    .split(":")[0]
                    .replace("def ", "")
                    .replace("class ", "")
                    .strip()
                )
                return name
        return ""


def preview_file_change(
    old_content: str,
    new_content: str,
    file_path: str,
    language: str = "python",
) -> FileDiff:
    """Generate a preview for file changes.

    Args:
        old_content: Original file content.
        new_content: Proposed new content.
        file_path: Path to file.
        language: Language for syntax highlighting.

    Returns:
        FileDiff ready for display.
    """
    return DiffGenerator.generate_diff(
        old_content=old_content,
        new_content=new_content,
        file_path=file_path,
        language=language,
    )


__all__ = ["DiffGenerator", "preview_file_change"]
