"""
Context Commands Handler.

Handles: /add, /remove, /files, /context-files

Phase 10: Refinement Sprint 1 - File Context Window
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from vertice_tui.core.context import get_file_context_window

if TYPE_CHECKING:
    from vertice_tui.app import QwenApp
    from vertice_tui.widgets.response_view import ResponseView


class ContextCommandHandler:
    """Handler for file context commands (Claude Code parity)."""

    def __init__(self, app: "QwenApp"):
        self.app = app

    @property
    def bridge(self):
        return self.app.bridge

    @property
    def file_window(self):
        return get_file_context_window()

    async def handle(
        self,
        command: str,
        args: str,
        view: "ResponseView"
    ) -> None:
        """Route to specific handler method."""
        handlers = {
            "/add": self._handle_add,
            "/remove": self._handle_remove,
            "/files": self._handle_files,
            "/context-files": self._handle_files,
        }

        handler = handlers.get(command)
        if handler:
            await handler(args, view)

    async def _handle_add(self, args: str, view: "ResponseView") -> None:
        """
        Handle /add command - Add file to context.

        Usage:
            /add file.py           - Add entire file
            /add file.py:10-50     - Add lines 10-50
            /add src/*.py          - Add multiple files (glob)
        """
        if not args:
            view.add_system_message(
                "## 📎 /add - Add file to context\n\n"
                "**Usage:**\n"
                "- `/add file.py` - Add entire file\n"
                "- `/add file.py:10-50` - Add lines 10-50\n"
                "- `/add src/main.py src/utils.py` - Add multiple files\n\n"
                "**Current context:**\n"
                f"{self.file_window.get_summary()}"
            )
            return

        # Parse arguments - could be multiple files or file:line-line
        added = []
        errors = []

        for file_spec in args.split():
            # Parse file:start-end format
            lines = None
            filepath = file_spec

            # Check for line range syntax (file.py:10-50)
            match = re.match(r'^(.+):(\d+)-(\d+)$', file_spec)
            if match:
                filepath = match.group(1)
                lines = (int(match.group(2)), int(match.group(3)))

            # Resolve path
            path = Path(filepath).expanduser()

            # Handle glob patterns
            if '*' in filepath:
                cwd = Path.cwd()
                matched_files = list(cwd.glob(filepath))
                if not matched_files:
                    errors.append(f"No files match: {filepath}")
                    continue

                for matched in matched_files[:10]:  # Limit to 10 files
                    success, msg = self.file_window.add(str(matched))
                    if success:
                        added.append(matched.name)
                    else:
                        errors.append(f"{matched.name}: {msg}")
            else:
                # Single file
                success, msg = self.file_window.add(str(path), lines=lines)
                if success:
                    added.append(path.name if lines is None else f"{path.name}:{lines[0]}-{lines[1]}")
                else:
                    errors.append(msg)

        # Report results
        if added:
            view.add_success(f"Added to context: {', '.join(added)}")

        if errors:
            for error in errors:
                view.add_error(error)

        # Show updated summary
        summary = self.file_window.get_summary()
        view.add_system_message(f"```\n{summary}\n```")

    async def _handle_remove(self, args: str, view: "ResponseView") -> None:
        """
        Handle /remove command - Remove file from context.

        Usage:
            /remove file.py     - Remove specific file
            /remove all         - Remove all files
        """
        if not args:
            view.add_system_message(
                "## 🗑️ /remove - Remove file from context\n\n"
                "**Usage:**\n"
                "- `/remove file.py` - Remove specific file\n"
                "- `/remove all` - Remove all files\n\n"
                "**Files in context:**\n"
                f"{self.file_window.get_summary()}"
            )
            return

        if args.strip().lower() == "all":
            count = self.file_window.clear()
            view.add_success(f"Removed all {count} files from context.")
            return

        # Remove specific files
        removed = []
        errors = []

        for filepath in args.split():
            success, msg = self.file_window.remove(filepath)
            if success:
                removed.append(filepath)
            else:
                errors.append(msg)

        if removed:
            view.add_success(f"Removed: {', '.join(removed)}")

        if errors:
            for error in errors:
                view.add_error(error)

        # Show updated summary
        summary = self.file_window.get_summary()
        view.add_system_message(f"```\n{summary}\n```")

    async def _handle_files(self, args: str, view: "ResponseView") -> None:
        """
        Handle /files command - Show files in context.

        Usage:
            /files          - Show all files in context
            /files verbose  - Show with more details
        """
        entries = self.file_window.list_entries()

        if not entries:
            view.add_system_message(
                "## 📁 File Context (Empty)\n\n"
                "No files in context. Use `/add <file>` to add files.\n\n"
                "**Examples:**\n"
                "- `/add src/main.py`\n"
                "- `/add config.yaml:1-50`\n"
                "- `/add src/*.py`"
            )
            return

        verbose = "verbose" in args.lower()
        used, max_tok = self.file_window.get_token_usage()
        pct = (used / max_tok * 100) if max_tok > 0 else 0

        lines = [
            f"## 📁 File Context ({len(entries)} files)\n",
            f"**Tokens:** {used:,} / {max_tok:,} ({pct:.1f}%)\n",
            "",
            "| File | Lines | Tokens | Priority |",
            "|------|-------|--------|----------|",
        ]

        for entry in entries:
            name = Path(entry.filepath).name
            line_range = f"{entry.start_line}-{entry.end_line}"
            priority = f"{entry.priority:.1f}"
            lines.append(f"| `{name}` | {line_range} | {entry.tokens} | {priority} |")

        if verbose:
            lines.append("")
            lines.append("### Preview")
            for entry in entries[:3]:  # Show preview of first 3
                preview = entry.content[:200] + "..." if len(entry.content) > 200 else entry.content
                lines.append(f"\n**{Path(entry.filepath).name}:**")
                lines.append(f"```{entry.language}")
                lines.append(preview)
                lines.append("```")

        view.add_system_message("\n".join(lines))


# Export for handler registration
__all__ = ["ContextCommandHandler"]
