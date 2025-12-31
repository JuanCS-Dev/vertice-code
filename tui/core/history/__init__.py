"""
History Module - Command and Session History Management.

Components:
- compaction.py: Context compaction mixin

Following CODE_CONSTITUTION: <500 lines per file, 100% type hints
"""

from __future__ import annotations

from .compaction import CompactionMixin

__all__ = [
    "CompactionMixin",
]
