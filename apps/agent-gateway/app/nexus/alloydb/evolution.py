"""
AlloyDB Evolution Operations.

Store and retrieve evolutionary candidates.
"""

from __future__ import annotations

import json
import logging
from typing import List

from nexus.types import EvolutionaryCandidate

logger = logging.getLogger(__name__)


class EvolutionOperations:
    """Mixin for evolution operations on AlloyDB."""

    async def store_evolution_candidate(self, candidate: EvolutionaryCandidate) -> bool:
        """Store an evolutionary candidate."""
        if not self._initialized:
            return False

        try:
            query = """
                INSERT INTO nexus_evolution
                (id, code, prompt, ancestry, generation, island_id, fitness_scores, evaluation_count, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO UPDATE SET
                    fitness_scores = EXCLUDED.fitness_scores,
                    evaluation_count = nexus_evolution.evaluation_count + 1
            """

            await self.execute(
                query,
                candidate.candidate_id,
                candidate.code,
                candidate.prompt,
                candidate.ancestry,
                candidate.generation,
                candidate.island_id,
                json.dumps(candidate.fitness_scores),
                candidate.evaluation_count,
                json.dumps(candidate.metadata if hasattr(candidate, "metadata") else {}),
            )
            return True

        except Exception as e:
            logger.error(f"Failed to store evolution candidate: {e}")
            return False

    async def get_best_candidates(self, limit: int = 10) -> List[EvolutionaryCandidate]:
        """Get best evolutionary candidates by fitness."""
        if not self._initialized:
            return []

        try:
            sql = """
                SELECT id, code, prompt, ancestry, generation, island_id,
                       fitness_scores, evaluation_count, created_at, metadata
                FROM nexus_evolution
                ORDER BY (fitness_scores->>'overall')::float DESC NULLS LAST
                LIMIT $1
            """

            rows = await self.fetch(sql, limit)

            return [
                EvolutionaryCandidate(
                    candidate_id=row["id"],
                    code=row["code"],
                    prompt=row["prompt"],
                    ancestry=row["ancestry"] or [],
                    generation=row["generation"],
                    island_id=row["island_id"],
                    fitness_scores=json.loads(row["fitness_scores"])
                    if row["fitness_scores"]
                    else {},
                    evaluation_count=row["evaluation_count"],
                )
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Failed to get best candidates: {e}")
            return []
