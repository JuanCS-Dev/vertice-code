# File and path types - Domain level

from __future__ import annotations

from typing import Literal, Optional, Tuple, TypedDict, Union
from pathlib import Path


FilePath = Union[str, Path]
FileContent = str
FileEncoding = Literal["utf-8", "ascii", "latin-1"]


class FileEdit(TypedDict):
    """Specification for a file edit operation."""

    path: FilePath
    old_text: str
    new_text: str
    line_range: Optional[Tuple[int, int]]


class FileOperation(TypedDict):
    """A file system operation."""

    operation: Literal["read", "write", "edit", "delete", "move", "copy"]
    path: FilePath
    content: Optional[FileContent]
    destination: Optional[FilePath]  # For move/copy
