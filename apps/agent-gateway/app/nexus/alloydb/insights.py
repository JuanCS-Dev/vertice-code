"""
AlloyDB Insights Operations.

Store and search metacognitive insights.
"""

from __future__ import annotations

import json
import logging
from typing import List, Tuple

from nexus.types import MetacognitiveInsight

logger = logging.getLogger(__name__)


class InsightOperations:
    """Mixin for insight operations on AlloyDB."""

    async def store_insight(self, insight: MetacognitiveInsight) -> bool:
        """Store a metacognitive insight."""
        if not self._initialized:
            return False

        try:
            embedding = None
            if self._embeddings:
                text = f"{insight.observation} {insight.learning} {insight.action}"
                embedding = await self._embeddings.aembed_query(text)

            query = """
                INSERT INTO nexus_insights
                (id, timestamp, context, observation, causal_analysis, learning, action, confidence, category, applied, embedding, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (id) DO UPDATE SET
                    confidence = EXCLUDED.confidence,
                    applied = EXCLUDED.applied
            """

            await self.execute(
                query,
                insight.insight_id,
                insight.timestamp,
                insight.context,
                insight.observation,
                insight.causal_analysis,
                insight.learning,
                insight.action,
                insight.confidence,
                insight.category,
                insight.applied,
                embedding,
                json.dumps(insight.metadata if hasattr(insight, "metadata") else {}),
            )
            return True

        except Exception as e:
            logger.error(f"Failed to store insight: {e}")
            return False

    async def search_insights(
        self,
        query: str,
        limit: int = 10,
        min_confidence: float = 0.0,
    ) -> List[Tuple[MetacognitiveInsight, float]]:
        """Semantic search across insights."""
        if not self._initialized:
            return []

        try:
            if self._embeddings:
                query_embedding = await self._embeddings.aembed_query(query)
                return await self._search_insights_vector(query_embedding, limit, min_confidence)
            else:
                return await self._search_insights_keyword(query, limit, min_confidence)

        except Exception as e:
            logger.error(f"Insight search failed: {e}")
            return []

    async def _search_insights_vector(
        self,
        embedding: List[float],
        limit: int,
        min_confidence: float,
    ) -> List[Tuple[MetacognitiveInsight, float]]:
        """Vector similarity search for insights."""
        sql = """
            SELECT id, timestamp, context, observation, causal_analysis, learning,
                   action, confidence, category, applied,
                   1 - (embedding <=> $1::vector) as similarity
            FROM nexus_insights
            WHERE embedding IS NOT NULL AND confidence >= $2
            ORDER BY embedding <=> $1::vector
            LIMIT $3
        """

        rows = await self.fetch(sql, str(embedding), min_confidence, limit)

        results = []
        for row in rows:
            insight = MetacognitiveInsight(
                insight_id=row["id"],
                timestamp=row["timestamp"],
                context=row["context"],
                observation=row["observation"],
                causal_analysis=row["causal_analysis"],
                learning=row["learning"],
                action=row["action"],
                confidence=row["confidence"],
                category=row["category"],
                applied=row["applied"],
            )
            results.append((insight, float(row["similarity"])))

        return results

    async def _search_insights_keyword(
        self,
        query: str,
        limit: int,
        min_confidence: float,
    ) -> List[Tuple[MetacognitiveInsight, float]]:
        """Keyword search fallback for insights."""
        sql = """
            SELECT id, timestamp, context, observation, causal_analysis, learning,
                   action, confidence, category, applied
            FROM nexus_insights
            WHERE (observation ILIKE $1 OR learning ILIKE $1) AND confidence >= $2
            ORDER BY confidence DESC
            LIMIT $3
        """

        rows = await self.fetch(sql, f"%{query}%", min_confidence, limit)

        return [
            (
                MetacognitiveInsight(
                    insight_id=row["id"],
                    timestamp=row["timestamp"],
                    context=row["context"],
                    observation=row["observation"],
                    causal_analysis=row["causal_analysis"],
                    learning=row["learning"],
                    action=row["action"],
                    confidence=row["confidence"],
                    category=row["category"],
                    applied=row["applied"],
                ),
                0.5,
            )
            for row in rows
        ]
