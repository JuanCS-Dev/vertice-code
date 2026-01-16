"""
Solution Archive

Maintains diverse archive of discovered agent variants using Quality-Diversity optimization.

References:
- arXiv:2505.22954 (Darwin Gödel Machine)
- Mouret & Clune (2015) - Quality-Diversity optimization
- MAP-Elites algorithm (Mouret & Clune, 2015)
- Novelty Search (Lehman & Stanley, 2011)
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional
import random

from .types import AgentVariant, EvolutionConfig, KappaMetrics

logger = logging.getLogger(__name__)


class SolutionArchive:
    """
    Archive of agent variants discovered during evolution.

    Implements Quality-Diversity (QD) optimization combining:
    - Fitness-based selection (exploitation)
    - Novelty search (exploration)
    - Niche-based archival (diversity preservation)

    References:
    - MAP-Elites: Returns the highest-performing solution in each cell
    - Novelty Search: Rewards behavioral novelty over objective performance
    """

    def __init__(
        self,
        config: Optional[EvolutionConfig] = None,
        persistence_path: Optional[Path] = None,
    ):
        """
        Initialize solution archive.

        Args:
            config: Evolution configuration
            persistence_path: Optional path for JSON persistence
        """
        self._config = config or EvolutionConfig()
        self._persistence_path = persistence_path
        self._variants: Dict[str, AgentVariant] = {}
        self._fitness_history: List[float] = []
        self._generation_count = 0

        # Quality-Diversity structures
        self._niche_map: Dict[str, str] = {}  # niche_id -> best variant_id
        self._novelty_archive: List[List[float]] = []  # behavior descriptors

        # Kappa tracking
        self._kappa_metrics = KappaMetrics()

        if persistence_path and persistence_path.exists():
            self._load_from_disk()

    def add(self, variant: AgentVariant) -> bool:
        """
        Add variant to archive using QD selection.

        Combines fitness, novelty, and niche-based criteria.

        Returns:
            True if variant was added, False if rejected
        """
        # Compute behavior descriptor if not present
        if not variant.behavior_descriptor:
            variant.compute_behavior_descriptor()

        # Calculate novelty score
        variant.novelty_score = self._compute_novelty(variant.behavior_descriptor)

        # Determine niche
        variant.niche_id = self._compute_niche_id(variant.behavior_descriptor)

        # QD decision: add if novel enough or improves niche
        should_add = False
        reason = ""

        # Case 1: Archive not full
        if len(self._variants) < self._config.max_archive_size:
            should_add = True
            reason = "archive_space"

        # Case 2: High novelty (exploration)
        elif variant.novelty_score >= self._config.novelty_threshold:
            # Replace lowest fitness in archive
            worst = self._get_worst_variant()
            if worst and variant.fitness_score > worst.fitness_score:
                del self._variants[worst.id]
                should_add = True
                reason = f"novelty_replace:{worst.id}"

        # Case 3: Niche improvement (MAP-Elites style)
        elif variant.niche_id in self._niche_map:
            current_best_id = self._niche_map[variant.niche_id]
            current_best = self._variants.get(current_best_id)
            if current_best and variant.fitness_score > current_best.fitness_score:
                del self._variants[current_best_id]
                should_add = True
                reason = f"niche_improve:{variant.niche_id}"

        # Case 4: New niche
        elif variant.niche_id not in self._niche_map:
            worst = self._get_worst_variant()
            if worst:
                del self._variants[worst.id]
                should_add = True
                reason = f"new_niche:{variant.niche_id}"

        if should_add:
            self._variants[variant.id] = variant
            self._niche_map[variant.niche_id] = variant.id
            self._novelty_archive.append(variant.behavior_descriptor)
            self._fitness_history.append(variant.fitness_score)
            self._generation_count = max(self._generation_count, variant.generation)

            # Update kappa metrics
            self._kappa_metrics.compute_kappa(self._fitness_history)

            self._persist()
            logger.info(
                f"[Archive] Added {variant.id} (fitness={variant.fitness_score:.3f}, "
                f"novelty={variant.novelty_score:.3f}, niche={variant.niche_id}, "
                f"reason={reason})"
            )
            return True

        logger.debug(f"[Archive] Rejected {variant.id} (fitness={variant.fitness_score:.3f})")
        return False

    def sample_parent(self) -> Optional[AgentVariant]:
        """
        Sample a parent variant for mutation.

        Uses weighted selection balancing:
        - Exploitation (high fitness)
        - Exploration (novelty/diversity)
        - Curiosity (under-explored niches)
        """
        if not self._variants:
            return None

        variants = list(self._variants.values())

        # Calculate selection weights
        weights = []
        max_fitness = max(v.fitness_score for v in variants) or 1.0
        max_novelty = max(v.novelty_score for v in variants) or 1.0

        for v in variants:
            # Exploitation: prefer high fitness
            exploitation = v.fitness_score / max_fitness if max_fitness > 0 else 0.5

            # Exploration: prefer high novelty
            exploration = v.novelty_score / max_novelty if max_novelty > 0 else 0.5

            # Curiosity: prefer variants with fewer children
            children_count = sum(1 for other in variants if other.parent_id == v.id)
            curiosity = 1.0 / (1 + children_count)

            # Combined weight
            weight = (
                self._config.exploitation_weight * exploitation
                + self._config.diversity_weight * exploration
                + 0.1 * curiosity  # Small curiosity bonus
            )
            weights.append(max(0.01, weight))

        # Normalize and select
        total = sum(weights)
        weights = [w / total for w in weights]

        selected = random.choices(variants, weights=weights, k=1)[0]
        logger.debug(
            f"[Archive] Sampled parent {selected.id} "
            f"(fitness={selected.fitness_score:.3f}, novelty={selected.novelty_score:.3f})"
        )
        return selected

    def get_best(self, n: int = 1) -> List[AgentVariant]:
        """Get top N variants by fitness."""
        sorted_variants = sorted(
            self._variants.values(),
            key=lambda v: v.fitness_score,
            reverse=True,
        )
        return sorted_variants[:n]

    def get_most_novel(self, n: int = 1) -> List[AgentVariant]:
        """Get top N variants by novelty score."""
        sorted_variants = sorted(
            self._variants.values(),
            key=lambda v: v.novelty_score,
            reverse=True,
        )
        return sorted_variants[:n]

    def get_by_id(self, variant_id: str) -> Optional[AgentVariant]:
        """Get variant by ID."""
        return self._variants.get(variant_id)

    def get_by_niche(self, niche_id: str) -> Optional[AgentVariant]:
        """Get best variant in a specific niche."""
        variant_id = self._niche_map.get(niche_id)
        if variant_id:
            return self._variants.get(variant_id)
        return None

    def get_lineage(self, variant_id: str) -> List[AgentVariant]:
        """Get full lineage (ancestors) of a variant."""
        lineage = []
        current_id: Optional[str] = variant_id

        while current_id:
            variant = self._variants.get(current_id)
            if variant:
                lineage.append(variant)
                current_id = variant.parent_id
            else:
                break

        return lineage

    def get_stats(self) -> Dict[str, Any]:
        """Get archive statistics including QD metrics."""
        if not self._variants:
            return {
                "size": 0,
                "generations": 0,
                "best_fitness": 0.0,
                "avg_fitness": 0.0,
                "kappa": 0.0,
                "niches_occupied": 0,
            }

        fitness_values = [v.fitness_score for v in self._variants.values()]
        novelty_values = [v.novelty_score for v in self._variants.values()]

        return {
            "size": len(self._variants),
            "generations": self._generation_count,
            "best_fitness": max(fitness_values),
            "avg_fitness": sum(fitness_values) / len(fitness_values),
            "worst_fitness": min(fitness_values),
            "best_novelty": max(novelty_values) if novelty_values else 0.0,
            "avg_novelty": sum(novelty_values) / len(novelty_values) if novelty_values else 0.0,
            "kappa": self._kappa_metrics.kappa,
            "kappa_variance": self._kappa_metrics.kappa_variance,
            "improvement_velocity": self._kappa_metrics.improvement_velocity,
            "niches_occupied": len(self._niche_map),
            "fitness_history_length": len(self._fitness_history),
        }

    def _compute_novelty(self, behavior: List[float]) -> float:
        """
        Compute novelty score using k-nearest neighbors in behavior space.

        Based on Novelty Search (Lehman & Stanley, 2011).
        """
        if not self._novelty_archive:
            return 1.0  # First variant is maximally novel

        k = min(15, len(self._novelty_archive))  # k-NN parameter
        distances = []

        for archived_behavior in self._novelty_archive:
            dist = self._behavior_distance(behavior, archived_behavior)
            distances.append(dist)

        distances.sort()
        avg_distance = sum(distances[:k]) / k if k > 0 else 0.0

        return avg_distance

    def _behavior_distance(self, b1: List[float], b2: List[float]) -> float:
        """Compute Euclidean distance between behavior descriptors."""
        if len(b1) != len(b2):
            return float("inf")

        return math.sqrt(sum((a - b) ** 2 for a, b in zip(b1, b2)))

    def _compute_niche_id(self, behavior: List[float]) -> str:
        """
        Compute niche ID by discretizing behavior space.

        Creates a grid-based niche structure for MAP-Elites style archival.
        """
        # Discretize each dimension into bins
        bins_per_dimension = 10
        niche_coords = []

        for value in behavior:
            bin_idx = min(int(value * bins_per_dimension), bins_per_dimension - 1)
            niche_coords.append(str(bin_idx))

        return "_".join(niche_coords)

    def _get_worst_variant(self) -> Optional[AgentVariant]:
        """Get variant with lowest fitness."""
        if not self._variants:
            return None
        return min(self._variants.values(), key=lambda v: v.fitness_score)

    def _persist(self) -> None:
        """Persist archive to disk if path configured."""
        if not self._persistence_path:
            return

        data = {
            "variants": [v.to_dict() for v in self._variants.values()],
            "fitness_history": self._fitness_history,
            "generation_count": self._generation_count,
            "niche_map": self._niche_map,
            "novelty_archive": self._novelty_archive,
            "kappa_metrics": {
                "kappa": self._kappa_metrics.kappa,
                "kappa_variance": self._kappa_metrics.kappa_variance,
                "improvement_velocity": self._kappa_metrics.improvement_velocity,
            },
        }

        self._persistence_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._persistence_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load_from_disk(self) -> None:
        """Load archive from disk."""
        if not self._persistence_path or not self._persistence_path.exists():
            return

        with open(self._persistence_path) as f:
            data = json.load(f)

        for v_data in data.get("variants", []):
            variant = AgentVariant.from_dict(v_data)
            self._variants[variant.id] = variant

        self._fitness_history = data.get("fitness_history", [])
        self._generation_count = data.get("generation_count", 0)
        self._niche_map = data.get("niche_map", {})
        self._novelty_archive = data.get("novelty_archive", [])

        kappa_data = data.get("kappa_metrics", {})
        if kappa_data:
            self._kappa_metrics.kappa = kappa_data.get("kappa", 0.0)
            self._kappa_metrics.kappa_variance = kappa_data.get("kappa_variance", 0.0)
            self._kappa_metrics.improvement_velocity = kappa_data.get("improvement_velocity", 0.0)

        logger.info(f"[Archive] Loaded {len(self._variants)} variants from disk")
