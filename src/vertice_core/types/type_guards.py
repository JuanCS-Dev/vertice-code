# Type guards for runtime type checking - Domain level

from __future__ import annotations

from typing import Any
from pathlib import Path


def is_message(obj: Any) -> bool:
    """Check if object is a valid Message."""
    if not isinstance(obj, dict):
        return False
    return (
        "role" in obj
        and "content" in obj
        and isinstance(obj["role"], str)
        and isinstance(obj["content"], str)
    )


def is_message_list(obj: Any) -> bool:
    """Check if object is a valid MessageList."""
    if not isinstance(obj, list):
        return False
    return all(is_message(msg) for msg in obj)


def is_file_path(obj: Any) -> bool:
    """Check if object is a valid FilePath."""
    return isinstance(obj, (str, Path))
