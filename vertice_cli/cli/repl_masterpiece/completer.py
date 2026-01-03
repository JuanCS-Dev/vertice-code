"""
REPL Masterpiece Completer - Fuzzy Completion VSCode Style.

This module provides SmartCompleter with fuzzy matching and
rich dropdown display.

Features:
- Fuzzy matching with scoring
- VSCode-style dropdown with icons
- Command and tool completion

Philosophy:
    "Autocomplete should anticipate, not frustrate."
"""

from __future__ import annotations

from typing import Dict

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML


class SmartCompleter(Completer):
    """Fuzzy completer with VSCode-style dropdown."""

    def __init__(self, commands: Dict[str, Dict]):
        """
        Initialize completer.

        Args:
            commands: Dictionary of commands with metadata
        """
        self.commands = commands
        self.tools = {
            '/read': {'icon': '📖', 'desc': 'Read file', 'example': '/read config.json'},
            '/write': {'icon': '✍️', 'desc': 'Write file', 'example': '/write test.txt "hello"'},
            '/edit': {'icon': '✏️', 'desc': 'Edit file', 'example': '/edit file.py'},
            '/run': {'icon': '⚡', 'desc': 'Execute', 'example': '/run ls -la'},
            '/git': {'icon': '🌿', 'desc': 'Git ops', 'example': '/git status'},
        }

    def _fuzzy_match(self, pattern: str, text: str) -> int:
        """
        Calculate fuzzy matching score (higher is better).

        Args:
            pattern: Search pattern
            text: Text to match against

        Returns:
            Match score (0 if no match)
        """
        pattern = pattern.lower()
        text = text.lower()

        # Exact prefix match (highest priority)
        if text.startswith(pattern):
            return 1000 + len(pattern)

        # Contains match
        if pattern in text:
            return 500 + len(pattern)

        # Fuzzy match (all chars present in order)
        score = 0
        pattern_idx = 0

        for i, char in enumerate(text):
            if pattern_idx < len(pattern) and char == pattern[pattern_idx]:
                score += (100 - i)  # Earlier matches score higher
                pattern_idx += 1

        # All chars matched?
        if pattern_idx == len(pattern):
            return score

        return 0

    def get_completions(self, document, complete_event):
        """Generate completions for current input."""
        text = document.text_before_cursor
        words = text.split()
        if not words:
            return

        word = words[-1]
        if not word.startswith('/'):
            return

        # Remove leading '/'
        query = word[1:].lower()
        all_items = {**self.commands, **self.tools}

        # Score all commands
        matches = []
        for cmd_name, cmd_meta in all_items.items():
            cmd_key = cmd_name[1:]  # Remove '/'
            score = self._fuzzy_match(query, cmd_key)

            if score > 0:
                desc = cmd_meta.get('description') or cmd_meta.get('desc', '')
                example = cmd_meta.get('example', '')

                # Rich display with icon and description
                display_text = f"{cmd_meta['icon']} {cmd_name:14} {desc}"
                if example:
                    display_text += f" • [dim]{example}[/dim]"

                matches.append((score, cmd_name, display_text))

        # Sort by score (descending)
        matches.sort(reverse=True, key=lambda x: x[0])

        # Yield top 10 matches
        for score, cmd_name, display_text in matches[:10]:
            yield Completion(
                cmd_name,
                start_position=-len(word),
                display=display_text,
                display_meta=HTML(f"<ansicyan>score: {score}</ansicyan>")
            )


__all__ = ["SmartCompleter"]
