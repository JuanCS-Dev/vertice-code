"""
Evolution Mixin

Mixin providing Darwin-Gödel Machine evolution capabilities to agents.

References:
- arXiv:2505.22954 (Darwin Gödel Machine - Sakana AI)
- arXiv:2512.02731 (GVU Operator Framework)
- Quality-Diversity optimization (Mouret & Clune, 2015)
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .types import (
    AgentVariant,
    EvolutionConfig,
    EvolutionResult,
    EvolutionStatus,
    KappaMetrics,
)
from .archive import SolutionArchive
from .mutator import CompositeMutator, BaseMutator
from .evaluator import BenchmarkEvaluator

logger = logging.getLogger(__name__)


class EvolutionMixin:
    """
    Mixin providing self-improvement capabilities via Darwin-Gödel evolution.

    Implements the full GVU (Generator-Verifier-Updater) cycle:
    1. Generate: Propose mutations via mutators
    2. Verify: Evaluate mutations empirically via benchmarks
    3. Update: Archive successful mutations, update operator weights

    Add to agent for:
    - Maintaining diverse archive of discovered variants (QD optimization)
    - Proposing and evaluating mutations (GVU cycles)
    - Tracking lineage and κ coefficient (self-improvement rate)
    """

    def _init_evolution(
        self,
        config: Optional[EvolutionConfig] = None,
        persistence_path: Optional[Path] = None,
        benchmark_runner: Optional[Callable[[AgentVariant], Dict[str, float]]] = None,
        mutators: Optional[List[BaseMutator]] = None,
    ) -> None:
        """
        Initialize Darwin-Gödel evolution system.

        Args:
            config: Evolution configuration
            persistence_path: Path for archive persistence
            benchmark_runner: Custom benchmark function
            mutators: Custom list of mutators
        """
        self._evolution_config = config or EvolutionConfig()
        self._archive = SolutionArchive(
            config=self._evolution_config,
            persistence_path=persistence_path,
        )
        self._mutator = CompositeMutator(mutators)
        self._evaluator = BenchmarkEvaluator(
            config=self._evolution_config,
            benchmark_runner=benchmark_runner,
        )
        self._current_variant: Optional[AgentVariant] = None
        self._evolution_history: List[EvolutionResult] = []
        self._kappa_metrics = KappaMetrics()
        self._evolution_initialized = True

        logger.info("[Evolution] Initialized Darwin-Gödel Machine with GVU framework")

    def create_initial_variant(
        self,
        prompts: Optional[Dict[str, str]] = None,
        tools: Optional[List[str]] = None,
        workflow: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> AgentVariant:
        """
        Create initial agent variant (seed for evolution).

        Args:
            prompts: Initial system prompts
            tools: Initial tools
            workflow: Initial workflow config
            parameters: Initial parameters

        Returns:
            New AgentVariant archived as generation 0
        """
        if not hasattr(self, "_archive"):
            self._init_evolution()

        variant = AgentVariant(
            prompts=prompts or {},
            tools=tools or [],
            workflow=workflow or {},
            parameters=parameters or {},
        )

        # Compute initial behavior descriptor for QD
        variant.compute_behavior_descriptor()

        self._archive.add(variant)
        self._current_variant = variant

        logger.info(f"[Evolution] Created initial variant {variant.id}")
        return variant

    async def evolve(self) -> Optional[EvolutionResult]:
        """
        Run one full GVU evolution cycle.

        Phases:
        1. Generate: Sample parent, propose mutation
        2. Verify: Evaluate child against benchmarks
        3. Update: Archive if improved, update operator weights

        Returns:
            EvolutionResult if evolution occurred, None if no parent available
        """
        if not hasattr(self, "_archive"):
            self._init_evolution()

        # === GENERATE PHASE ===
        gen_start = time.perf_counter()

        parent = self._archive.sample_parent()
        if not parent:
            logger.warning("[Evolution] No parent available for evolution")
            return None

        proposal = self._mutator.propose(parent)
        if not proposal:
            logger.debug("[Evolution] No mutation proposed")
            return None

        # Apply mutation to create child
        child = self._mutator.apply(parent, proposal)
        child.compute_behavior_descriptor()

        gen_time = (time.perf_counter() - gen_start) * 1000

        # === VERIFY PHASE ===
        result = await self._evaluator.evaluate(child, baseline=parent)
        result.mutations_applied = [proposal]
        result.generation_time_ms = gen_time

        # === UPDATE PHASE ===
        update_start = time.perf_counter()

        if result.status == EvolutionStatus.IMPROVED:
            self._archive.add(child)
            self._current_variant = child

            # Update operator success for adaptive selection
            self._mutator.update_success(proposal.mutation_type, success=True)

            logger.info(
                f"[Evolution] GVU cycle success: {parent.id} → {child.id} "
                f"(Δfit={result.fitness_delta:.2%}, κ+={result.kappa_contribution:.4f})"
            )
        else:
            # Update operator failure
            self._mutator.update_success(proposal.mutation_type, success=False)

            logger.debug(f"[Evolution] GVU cycle rejected: {result.reasoning}")

        result.update_time_ms = (time.perf_counter() - update_start) * 1000

        # Update global κ metrics
        self._update_kappa_metrics(result)

        self._evolution_history.append(result)
        return result

    async def evolve_n(self, n: int) -> List[EvolutionResult]:
        """
        Run N GVU evolution cycles.

        Args:
            n: Number of cycles

        Returns:
            List of evolution results
        """
        results = []
        for i in range(n):
            result = await self.evolve()
            if result:
                results.append(result)
            logger.debug(f"[Evolution] Cycle {i + 1}/{n} complete")
        return results

    async def evolve_until_target(
        self,
        target_fitness: float,
        max_cycles: int = 100,
    ) -> List[EvolutionResult]:
        """
        Evolve until target fitness is reached or max cycles exceeded.

        Args:
            target_fitness: Target fitness score to achieve
            max_cycles: Maximum number of evolution cycles

        Returns:
            List of evolution results
        """
        results = []
        for i in range(max_cycles):
            result = await self.evolve()
            if result:
                results.append(result)

                # Check if target reached
                best = self.get_best_variant()
                if best and best.fitness_score >= target_fitness:
                    logger.info(
                        f"[Evolution] Target fitness {target_fitness} reached "
                        f"after {i + 1} cycles"
                    )
                    break

        return results

    def get_best_variant(self) -> Optional[AgentVariant]:
        """Get the best variant from archive by fitness."""
        if not hasattr(self, "_archive"):
            return None

        best = self._archive.get_best(1)
        return best[0] if best else None

    def get_most_novel_variant(self) -> Optional[AgentVariant]:
        """Get the most novel variant from archive."""
        if not hasattr(self, "_archive"):
            return None

        novel = self._archive.get_most_novel(1)
        return novel[0] if novel else None

    def get_current_variant(self) -> Optional[AgentVariant]:
        """Get the currently active variant."""
        if not hasattr(self, "_current_variant"):
            return None
        return self._current_variant

    def set_current_variant(self, variant_id: str) -> bool:
        """
        Set current variant by ID.

        Returns:
            True if variant found and set, False otherwise
        """
        if not hasattr(self, "_archive"):
            return False

        variant = self._archive.get_by_id(variant_id)
        if variant:
            self._current_variant = variant
            return True
        return False

    def get_lineage(self, variant_id: Optional[str] = None) -> List[AgentVariant]:
        """Get lineage of a variant (or current variant)."""
        if not hasattr(self, "_archive"):
            return []

        target_id = variant_id
        if not target_id and hasattr(self, "_current_variant") and self._current_variant:
            target_id = self._current_variant.id

        if not target_id:
            return []

        return self._archive.get_lineage(target_id)

    def get_evolution_status(self) -> Dict[str, Any]:
        """Get comprehensive evolution system status."""
        if not hasattr(self, "_evolution_initialized"):
            return {"initialized": False}

        archive_stats = self._archive.get_stats()
        evaluator_stats = self._evaluator.get_evaluation_stats()
        operator_stats = self._mutator.get_operator_stats()

        return {
            "initialized": True,
            "archive": archive_stats,
            "evaluator": evaluator_stats,
            "operators": operator_stats,
            "current_variant_id": (self._current_variant.id if self._current_variant else None),
            "evolution_cycles": len(self._evolution_history),
            "improvement_rate": (
                sum(1 for r in self._evolution_history if r.status == EvolutionStatus.IMPROVED)
                / len(self._evolution_history)
                if self._evolution_history
                else 0
            ),
            "kappa": self._kappa_metrics.kappa,
            "kappa_variance": self._kappa_metrics.kappa_variance,
            "improvement_velocity": self._kappa_metrics.improvement_velocity,
        }

    def get_kappa_metrics(self) -> KappaMetrics:
        """Get current κ coefficient metrics."""
        if not hasattr(self, "_kappa_metrics"):
            return KappaMetrics()
        return self._kappa_metrics

    def export_best_config(self) -> Dict[str, Any]:
        """Export best variant configuration for agent use."""
        best = self.get_best_variant()
        if not best:
            return {}

        return {
            "prompts": best.prompts,
            "tools": best.tools,
            "workflow": best.workflow,
            "parameters": best.parameters,
            "fitness_score": best.fitness_score,
            "generation": best.generation,
            "behavior_descriptor": best.behavior_descriptor,
            "novelty_score": best.novelty_score,
        }

    def _update_kappa_metrics(self, result: EvolutionResult) -> None:
        """Update global κ metrics after evolution cycle."""
        fitness_history = [
            r.child_variant.fitness_score
            for r in self._evolution_history
            if r.status == EvolutionStatus.IMPROVED
        ]

        if result.status == EvolutionStatus.IMPROVED:
            fitness_history.append(result.child_variant.fitness_score)

        if len(fitness_history) >= 2:
            self._kappa_metrics.compute_kappa(fitness_history)
