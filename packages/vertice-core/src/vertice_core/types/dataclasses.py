# Immutable dataclasses - Domain level

from __future__ import annotations

from typing import List
from dataclasses import dataclass
from .files import FilePath


@dataclass(frozen=True)
class CodeSpan:
    """A span of code with location information."""

    file: FilePath
    start_line: int
    end_line: int
    content: str


@dataclass(frozen=True)
class DiffHunk:
    """A single hunk in a diff."""

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[str]
