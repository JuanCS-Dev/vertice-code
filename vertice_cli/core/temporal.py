"""Temporal utilities for time awareness."""

from datetime import datetime, timezone
from typing import Optional


def get_current_datetime() -> datetime:
    """Get current UTC datetime with timezone awareness."""
    return datetime.now(timezone.utc)


def get_current_timestamp() -> float:
    """Get current UTC timestamp."""
    return get_current_datetime().timestamp()


def format_datetime(dt: Optional[datetime] = None) -> str:
    """Format datetime to ISO string."""
    if dt is None:
        dt = get_current_datetime()
    return dt.isoformat()
