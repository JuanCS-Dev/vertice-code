"""
Contribution Ledger - Agent economy and reputation tracking.

Records agent contributions and calculates reputation scores
for the multi-agent coordination economy system.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class ContributionLedger:
    """
    Agent contribution and reputation tracking.

    Maintains ledger of contributions (code commits, reviews, task completions)
    and calculates reputation scores for economy-based agent coordination.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_ledger()

    def _init_ledger(self) -> None:
        """Initialize contribution and reputation tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS contributions (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    contribution_type TEXT,
                    value REAL,
                    task_id TEXT,
                    metadata TEXT,
                    timestamp TEXT
                )
            """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reputation (
                    agent_id TEXT PRIMARY KEY,
                    total_contributions REAL DEFAULT 0,
                    successful_tasks INTEGER DEFAULT 0,
                    failed_tasks INTEGER DEFAULT 0,
                    quality_score REAL DEFAULT 0.5,
                    last_updated TEXT
                )
            """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_contrib_agent ON contributions(agent_id)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_contrib_type ON contributions(contribution_type)"
            )

    def record_contribution(
        self,
        agent_id: str,
        contribution_type: str,
        value: float,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Record an agent contribution.

        Args:
            agent_id: ID of the contributing agent.
            contribution_type: Type (code_commit, code_review, task_completion, etc.)
            value: Numeric value of contribution.
            task_id: Optional associated task ID.
            metadata: Optional additional metadata.

        Returns:
            ID of the recorded contribution.
        """
        contribution_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            # Record contribution
            conn.execute(
                """INSERT INTO contributions
                   (id, agent_id, contribution_type, value, task_id, metadata, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    contribution_id,
                    agent_id,
                    contribution_type,
                    value,
                    task_id,
                    json.dumps(metadata or {}),
                    timestamp,
                ),
            )

            # Update reputation
            conn.execute(
                """INSERT INTO reputation (agent_id, total_contributions, last_updated)
                   VALUES (?, ?, ?)
                   ON CONFLICT(agent_id) DO UPDATE SET
                   total_contributions = total_contributions + ?,
                   last_updated = ?""",
                (agent_id, value, timestamp, value, timestamp),
            )

        return contribution_id

    def get_agent_reputation(self, agent_id: str) -> Dict[str, Any]:
        """
        Get an agent's reputation score.

        Args:
            agent_id: ID of the agent.

        Returns:
            Dictionary with reputation metrics.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM reputation WHERE agent_id = ?", (agent_id,)
            ).fetchone()

            if row:
                return dict(row)
            return {
                "agent_id": agent_id,
                "total_contributions": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "quality_score": 0.5,
            }

    def get_contributions(
        self,
        agent_id: Optional[str] = None,
        contribution_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[Dict[str, Any]]:
        """
        Get contribution history with optional filters.

        Args:
            agent_id: Filter by agent ID.
            contribution_type: Filter by contribution type.
            limit: Maximum results to return.

        Returns:
            List of contribution records.
        """
        conditions = []
        params: list[Any] = []

        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)
        if contribution_type:
            conditions.append("contribution_type = ?")
            params.append(contribution_type)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM contributions WHERE {where_clause} ORDER BY timestamp DESC LIMIT ?",
                (*params, limit),
            ).fetchall()

            return [dict(row) for row in rows]

    def update_task_outcome(self, agent_id: str, success: bool) -> None:
        """
        Update agent reputation based on task outcome.

        Args:
            agent_id: ID of the agent.
            success: Whether the task was successful.
        """
        column = "successful_tasks" if success else "failed_tasks"
        timestamp = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"""INSERT INTO reputation (agent_id, {column}, last_updated)
                   VALUES (?, 1, ?)
                   ON CONFLICT(agent_id) DO UPDATE SET
                   {column} = {column} + 1,
                   last_updated = ?""",
                (agent_id, timestamp, timestamp),
            )

    def get_leaderboard(self, limit: int = 10) -> list[Dict[str, Any]]:
        """
        Get top agents by reputation.

        Args:
            limit: Number of top agents to return.

        Returns:
            List of agent reputation records sorted by total contributions.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM reputation ORDER BY total_contributions DESC LIMIT ?",
                (limit,),
            ).fetchall()

            return [dict(row) for row in rows]
