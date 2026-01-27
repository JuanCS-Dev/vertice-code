"""
AlloyDB State Operations.

Save and load system state, healing records.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from nexus.types import HealingRecord, SystemState

logger = logging.getLogger(__name__)


class StateOperations:
    """Mixin for state operations on AlloyDB."""

    async def store_healing_record(self, record: HealingRecord) -> bool:
        """Store a healing record."""
        if not self._initialized:
            return False

        try:
            query = """
                INSERT INTO nexus_healing
                (id, timestamp, anomaly_type, anomaly_severity, diagnosis, action, success, rollback_available, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """

            await self.execute(
                query,
                record.healing_id,
                record.timestamp,
                record.anomaly_type,
                record.anomaly_severity,
                record.diagnosis,
                record.action,
                record.success,
                record.rollback_available,
                json.dumps(record.metadata if hasattr(record, "metadata") else {}),
            )
            return True

        except Exception as e:
            logger.error(f"Failed to store healing record: {e}")
            return False

    async def save_state(self, state: SystemState) -> bool:
        """Save current system state."""
        if not self._initialized:
            return False

        try:
            query = "INSERT INTO nexus_state (state) VALUES ($1)"
            await self.execute(query, json.dumps(state.to_dict()))
            return True

        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False

    async def load_latest_state(self) -> Optional[SystemState]:
        """Load most recent system state."""
        if not self._initialized:
            return None

        try:
            sql = "SELECT state FROM nexus_state ORDER BY timestamp DESC LIMIT 1"
            row = await self.fetchrow(sql)

            if row:
                state_dict = json.loads(row["state"])
                return SystemState.from_dict(state_dict)
            return None

        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return None

    async def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        if not self._initialized:
            return {"initialized": False}

        try:
            stats = {"initialized": True}

            # Memory counts
            rows = await self.fetch(
                "SELECT level, COUNT(*) as cnt FROM nexus_memories GROUP BY level"
            )
            stats["memories"] = {row["level"]: row["cnt"] for row in rows}

            # Insight count
            row = await self.fetchrow("SELECT COUNT(*) as cnt FROM nexus_insights")
            stats["insights"] = row["cnt"] if row else 0

            # Evolution count
            row = await self.fetchrow("SELECT COUNT(*) as cnt FROM nexus_evolution")
            stats["evolution_candidates"] = row["cnt"] if row else 0

            # Healing count
            row = await self.fetchrow("SELECT COUNT(*) as cnt FROM nexus_healing")
            stats["healing_records"] = row["cnt"] if row else 0

            return stats

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"initialized": True, "error": str(e)}
