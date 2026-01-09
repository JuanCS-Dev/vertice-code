"""
Topology Selection

Optimal coordination topology selection based on task characteristics.

Reference:
- arXiv:2512.08296 (Scaling Agent Systems)
"""

from __future__ import annotations

import logging
from typing import Dict

from .types import CoordinationTopology, TaskCharacteristic

logger = logging.getLogger(__name__)


class TopologySelector:
    """
    Select optimal coordination topology based on task characteristics.

    Based on arXiv:2512.08296 findings:
    - Parallelizable → Centralized (+80.8%)
    - Exploratory → Decentralized (+9.2%)
    - Sequential → Single-agent (MAS degrades -39% to -70%)
    - Complex → Hybrid
    """

    TOPOLOGY_PERFORMANCE: Dict[CoordinationTopology, Dict[TaskCharacteristic, float]] = {
        CoordinationTopology.CENTRALIZED: {
            TaskCharacteristic.PARALLELIZABLE: 0.808,
            TaskCharacteristic.SEQUENTIAL: -0.39,
            TaskCharacteristic.EXPLORATORY: 0.002,
            TaskCharacteristic.COMPLEX: 0.40,
        },
        CoordinationTopology.DECENTRALIZED: {
            TaskCharacteristic.PARALLELIZABLE: 0.30,
            TaskCharacteristic.SEQUENTIAL: -0.50,
            TaskCharacteristic.EXPLORATORY: 0.092,
            TaskCharacteristic.COMPLEX: 0.25,
        },
        CoordinationTopology.HYBRID: {
            TaskCharacteristic.PARALLELIZABLE: 0.70,
            TaskCharacteristic.SEQUENTIAL: -0.20,
            TaskCharacteristic.EXPLORATORY: 0.06,
            TaskCharacteristic.COMPLEX: 0.55,
        },
    }

    ERROR_FACTORS: Dict[CoordinationTopology, float] = {
        CoordinationTopology.INDEPENDENT: 17.2,
        CoordinationTopology.CENTRALIZED: 4.4,
        CoordinationTopology.DECENTRALIZED: 8.0,
        CoordinationTopology.HYBRID: 5.0,
    }

    SATURATION_THRESHOLD = 0.45

    def select(
        self,
        task_characteristic: TaskCharacteristic,
        agent_baseline_performance: float = 0.0,
        prefer_error_containment: bool = True,
    ) -> CoordinationTopology:
        """
        Select optimal topology for a task.

        Args:
            task_characteristic: Type of task
            agent_baseline_performance: Single-agent performance (0-1)
            prefer_error_containment: Prefer lower error amplification

        Returns:
            Recommended coordination topology
        """
        if agent_baseline_performance > self.SATURATION_THRESHOLD:
            logger.info(
                f"[TopologySelector] Agent baseline {agent_baseline_performance:.2f} "
                f"> saturation threshold {self.SATURATION_THRESHOLD}. "
                "Coordination may have diminishing returns."
            )

        if task_characteristic == TaskCharacteristic.SEQUENTIAL:
            logger.info("[TopologySelector] Sequential task → Independent (avoid MAS)")
            return CoordinationTopology.INDEPENDENT

        scores: Dict[CoordinationTopology, float] = {}

        for topology in [
            CoordinationTopology.CENTRALIZED,
            CoordinationTopology.DECENTRALIZED,
            CoordinationTopology.HYBRID,
        ]:
            performance = self.TOPOLOGY_PERFORMANCE[topology].get(
                task_characteristic, 0.0
            )
            error_factor = self.ERROR_FACTORS[topology]
            error_penalty = (error_factor - 4.4) * 0.05 if prefer_error_containment else 0
            scores[topology] = performance - error_penalty

        best = max(scores, key=lambda t: scores[t])
        logger.info(
            f"[TopologySelector] {task_characteristic.value} → "
            f"{best.value} (score: {scores[best]:.3f})"
        )

        return best

    def get_error_factor(self, topology: CoordinationTopology) -> float:
        """Get error amplification factor for a topology."""
        return self.ERROR_FACTORS.get(topology, 10.0)
