"""
Memory Cortex Types - Core data structures.

Dataclasses for memory entries and contributions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Memory:
    """A single memory entry."""

    id: str
    content: str
    memory_type: str  # working, episodic, semantic, procedural, meta, social
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    embedding: Optional[List[float]] = None


@dataclass
class Contribution:
    """Track agent contributions for economy system."""

    id: str
    agent_id: str
    contribution_type: str  # code_commit, code_review, task_completion, etc.
    value: float
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
