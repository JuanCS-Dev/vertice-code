"""
Experience Memory

Memory system for learning from past experiences.

Reference:
- Reflexion (Shinn et al., 2023)
- MetaAgent (arXiv:2508.00271v2)
"""

from __future__ import annotations

import uuid
import logging
from typing import Any, Dict, List, Optional

from .types import ExperienceRecord

logger = logging.getLogger(__name__)


class ExperienceMemory:
    """
    Memory system for learning from past experiences.

    Implements Reflexion-style metacognitive learning:
    - Record outcomes of past decisions
    - Extract lessons learned
    - Apply learning to future decisions
    """

    def __init__(self, max_records: int = 500) -> None:
        self._records: List[ExperienceRecord] = []
        self._max_records = max_records
        self._lessons_index: Dict[str, List[str]] = {}  # task_type -> lessons

    def record_experience(
        self,
        task_type: str,
        strategy_used: str,
        outcome: str,
        confidence_before: float,
        confidence_after: float,
        lessons_learned: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> ExperienceRecord:
        """Record an experience for future learning."""
        record = ExperienceRecord(
            id=str(uuid.uuid4()),
            task_type=task_type,
            strategy_used=strategy_used,
            outcome=outcome,
            confidence_before=confidence_before,
            confidence_after=confidence_after,
            lessons_learned=lessons_learned,
            context=context or {},
        )

        self._records.append(record)

        # Index lessons by task type
        if task_type not in self._lessons_index:
            self._lessons_index[task_type] = []
        self._lessons_index[task_type].extend(lessons_learned)

        # Trim if needed
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records :]

        logger.info(f"[ExperienceMemory] Recorded: {task_type} - {outcome}")
        return record

    def get_relevant_lessons(
        self,
        task_type: str,
        limit: int = 5,
    ) -> List[str]:
        """Get lessons learned relevant to a task type."""
        lessons = self._lessons_index.get(task_type, [])
        # Return most recent lessons
        return lessons[-limit:] if lessons else []

    def get_strategy_performance(
        self,
        strategy: str,
    ) -> Dict[str, Any]:
        """Get performance statistics for a strategy."""
        relevant = [r for r in self._records if r.strategy_used == strategy]

        if not relevant:
            return {"strategy": strategy, "usage_count": 0, "success_rate": 0.0}

        successes = sum(1 for r in relevant if r.outcome == "success")

        return {
            "strategy": strategy,
            "usage_count": len(relevant),
            "success_rate": successes / len(relevant),
            "avg_confidence_before": sum(r.confidence_before for r in relevant) / len(relevant),
            "avg_confidence_after": sum(r.confidence_after for r in relevant) / len(relevant),
        }

    def suggest_strategy(
        self,
        task_type: str,
        context: Dict[str, Any],
    ) -> Optional[str]:
        """Suggest a strategy based on past experience."""
        relevant = [r for r in self._records if r.task_type == task_type]

        if not relevant:
            return None

        # Group by strategy and calculate success rates
        strategy_stats: Dict[str, Dict[str, float]] = {}
        for record in relevant:
            if record.strategy_used not in strategy_stats:
                strategy_stats[record.strategy_used] = {"successes": 0, "total": 0}
            strategy_stats[record.strategy_used]["total"] += 1
            if record.outcome == "success":
                strategy_stats[record.strategy_used]["successes"] += 1

        # Find best strategy
        best_strategy = None
        best_rate = 0.0

        for strategy, stats in strategy_stats.items():
            if stats["total"] >= 3:  # Minimum sample size
                rate = stats["successes"] / stats["total"]
                if rate > best_rate:
                    best_rate = rate
                    best_strategy = strategy

        return best_strategy

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "total_records": len(self._records),
            "task_types": list(self._lessons_index.keys()),
            "total_lessons": sum(len(lessons) for lessons in self._lessons_index.values()),
        }
