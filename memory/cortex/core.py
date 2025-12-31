"""
Core Memory - Agent Identity and Persistent State

Based on MIRIX architecture (arXiv:2507.07957).
Stores persistent agent and user information:
- Persona block: Agent profile, tone, behavior
- Human block: User facts, preferences, relationships

Reference: https://arxiv.org/abs/2507.07957
"""

from __future__ import annotations

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class CoreBlockType(str, Enum):
    """Types of core memory blocks (MIRIX spec)."""
    PERSONA = "persona"  # Agent identity
    HUMAN = "human"      # User information


@dataclass
class CoreBlock:
    """
    A core memory block.

    Attributes:
        block_type: persona or human.
        data: Key-value data in this block.
        capacity: Maximum number of entries.
        created_at: When this block was created.
        updated_at: Last update timestamp.
    """
    block_type: CoreBlockType
    data: Dict[str, str]
    capacity: int = 100
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def usage(self) -> float:
        """Get usage percentage."""
        return len(self.data) / self.capacity

    @property
    def needs_rewrite(self) -> bool:
        """Check if block needs consolidation (90% full per MIRIX)."""
        return self.usage >= 0.9

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "block_type": self.block_type.value,
            "data": self.data,
            "capacity": self.capacity,
            "usage_percent": round(self.usage * 100, 1),
            "needs_rewrite": self.needs_rewrite,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class CoreMemory:
    """
    Core Memory System - Agent Identity.

    Manages persistent information about:
    - Persona: Agent's identity, tone, capabilities, behavior
    - Human: User's name, preferences, relationships

    Implements MIRIX capacity management: triggers consolidation
    when blocks reach 90% capacity.

    Based on MIRIX (arXiv:2507.07957) core memory component.
    """

    DEFAULT_PERSONA = {
        "name": "Vertice Agent",
        "role": "AI Development Assistant",
        "tone": "professional, helpful, precise",
        "capabilities": "code generation, review, architecture, research",
        "constraints": "follows CODE_CONSTITUTION, respects user intent",
    }

    def __init__(self, db_path: Path, agent_id: str = "default"):
        """
        Initialize core memory.

        Args:
            db_path: Path to SQLite database file.
            agent_id: Identifier for this agent instance.
        """
        self.db_path = db_path
        self.agent_id = agent_id
        self._init_db()
        self._ensure_defaults()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS core_blocks (
                    agent_id TEXT,
                    block_type TEXT,
                    key TEXT,
                    value TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    PRIMARY KEY (agent_id, block_type, key)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS core_metadata (
                    agent_id TEXT,
                    block_type TEXT,
                    capacity INTEGER DEFAULT 100,
                    created_at TEXT,
                    PRIMARY KEY (agent_id, block_type)
                )
            """)

    def _ensure_defaults(self) -> None:
        """Ensure default persona exists."""
        persona = self.get_block(CoreBlockType.PERSONA)
        if not persona.data:
            for key, value in self.DEFAULT_PERSONA.items():
                self.set(CoreBlockType.PERSONA, key, value)

    def set(
        self,
        block_type: CoreBlockType,
        key: str,
        value: str,
    ) -> None:
        """
        Set a value in a core block.

        Args:
            block_type: persona or human.
            key: Key for the value.
            value: Value to store.
        """
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO core_blocks
                   (agent_id, block_type, key, value, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (self.agent_id, block_type.value, key, value, now, now)
            )
            # Ensure metadata exists
            conn.execute(
                """INSERT OR IGNORE INTO core_metadata
                   (agent_id, block_type, capacity, created_at)
                   VALUES (?, ?, 100, ?)""",
                (self.agent_id, block_type.value, now)
            )

        logger.debug(f"Core memory set: {block_type.value}.{key}")

    def get(
        self,
        block_type: CoreBlockType,
        key: str,
        default: Optional[str] = None,
    ) -> Optional[str]:
        """
        Get a value from a core block.

        Args:
            block_type: persona or human.
            key: Key to retrieve.
            default: Default value if not found.

        Returns:
            Value if found, default otherwise.
        """
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """SELECT value FROM core_blocks
                   WHERE agent_id = ? AND block_type = ? AND key = ?""",
                (self.agent_id, block_type.value, key)
            ).fetchone()

            return row[0] if row else default

    def get_block(self, block_type: CoreBlockType) -> CoreBlock:
        """
        Get an entire core block.

        Args:
            block_type: persona or human.

        Returns:
            CoreBlock with all data.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get data
            rows = conn.execute(
                """SELECT key, value, created_at, updated_at
                   FROM core_blocks
                   WHERE agent_id = ? AND block_type = ?""",
                (self.agent_id, block_type.value)
            ).fetchall()

            data = {row["key"]: row["value"] for row in rows}
            updated_at = max((row["updated_at"] for row in rows), default=None)
            created_at = min((row["created_at"] for row in rows), default=None)

            # Get capacity
            meta = conn.execute(
                """SELECT capacity FROM core_metadata
                   WHERE agent_id = ? AND block_type = ?""",
                (self.agent_id, block_type.value)
            ).fetchone()
            capacity = meta["capacity"] if meta else 100

        return CoreBlock(
            block_type=block_type,
            data=data,
            capacity=capacity,
            created_at=created_at or datetime.now().isoformat(),
            updated_at=updated_at or datetime.now().isoformat(),
        )

    def delete(self, block_type: CoreBlockType, key: str) -> bool:
        """
        Delete a key from a core block.

        Args:
            block_type: persona or human.
            key: Key to delete.

        Returns:
            True if deleted, False if not found.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """DELETE FROM core_blocks
                   WHERE agent_id = ? AND block_type = ? AND key = ?""",
                (self.agent_id, block_type.value, key)
            )
            return cursor.rowcount > 0

    def get_persona(self) -> Dict[str, str]:
        """Get the persona block as dictionary."""
        return self.get_block(CoreBlockType.PERSONA).data

    def get_human(self) -> Dict[str, str]:
        """Get the human block as dictionary."""
        return self.get_block(CoreBlockType.HUMAN).data

    def set_user_preference(self, key: str, value: str) -> None:
        """Convenience method to set user preference."""
        self.set(CoreBlockType.HUMAN, key, value)

    def get_user_preference(
        self,
        key: str,
        default: Optional[str] = None,
    ) -> Optional[str]:
        """Convenience method to get user preference."""
        return self.get(CoreBlockType.HUMAN, key, default)

    def check_capacity(self) -> Dict[str, Any]:
        """
        Check capacity of all blocks.

        Returns:
            Status of each block with rewrite recommendations.
        """
        persona = self.get_block(CoreBlockType.PERSONA)
        human = self.get_block(CoreBlockType.HUMAN)

        return {
            "persona": persona.to_dict(),
            "human": human.to_dict(),
            "any_needs_rewrite": persona.needs_rewrite or human.needs_rewrite,
        }

    def consolidate_block(
        self,
        block_type: CoreBlockType,
        consolidation_fn: Optional[callable] = None,
    ) -> int:
        """
        Consolidate a block when at capacity.

        This is called when block reaches 90% capacity per MIRIX spec.
        Default behavior: remove oldest entries. Can be customized
        with a consolidation function that uses LLM to summarize.

        Args:
            block_type: Block to consolidate.
            consolidation_fn: Optional custom consolidation function.

        Returns:
            Number of entries removed.
        """
        block = self.get_block(block_type)

        if not block.needs_rewrite:
            return 0

        if consolidation_fn:
            # Custom consolidation (e.g., LLM-based summarization)
            return consolidation_fn(block)

        # Default: keep most recent 70% of entries
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """SELECT key FROM core_blocks
                   WHERE agent_id = ? AND block_type = ?
                   ORDER BY updated_at ASC""",
                (self.agent_id, block_type.value)
            ).fetchall()

            # Remove oldest 30%
            to_remove = int(len(rows) * 0.3)
            keys_to_remove = [row[0] for row in rows[:to_remove]]

            for key in keys_to_remove:
                conn.execute(
                    """DELETE FROM core_blocks
                       WHERE agent_id = ? AND block_type = ? AND key = ?""",
                    (self.agent_id, block_type.value, key)
                )

            logger.info(
                f"Consolidated {block_type.value}: removed {len(keys_to_remove)} entries"
            )
            return len(keys_to_remove)

    def to_context_string(self) -> str:
        """
        Convert core memory to string for LLM context injection.

        Returns:
            Formatted string for system prompt.
        """
        persona = self.get_persona()
        human = self.get_human()

        parts = ["<core_memory>"]

        if persona:
            parts.append("<persona>")
            for key, value in persona.items():
                parts.append(f"  {key}: {value}")
            parts.append("</persona>")

        if human:
            parts.append("<human>")
            for key, value in human.items():
                parts.append(f"  {key}: {value}")
            parts.append("</human>")

        parts.append("</core_memory>")

        return "\n".join(parts)
