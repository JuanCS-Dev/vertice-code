"""
Darwin Gödel Machine Evolution System

Implements the Darwin Gödel evolution loop for agent self-improvement.

Pattern (Sakana AI, arXiv:2505.22954):
1. Sample parent from diverse archive
2. Propose modifications (prompts, strategies, tools)
3. Evaluate on benchmarks
4. If improvement > threshold, add to archive
5. Repeat (open-ended evolution)

Reference:
- Darwin Gödel Machine (arXiv:2505.22954, Sakana AI)
- https://sakana.ai/dgm/
"""

from __future__ import annotations

import json
import hashlib
import random
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Any
import logging

from .types import (
    AgentVariant,
    BenchmarkTask,
    CodeGenerationRequest,
    EvolutionResult,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class DarwinGodelMixin:
    """
    Mixin providing Darwin Gödel evolution capabilities.

    Add to CoderAgent via multiple inheritance.
    """

    _archive: List[AgentVariant]
    _current_variant: Optional[AgentVariant]
    _archive_path: Path
    _evolution_history: List[EvolutionResult]

    def _init_evolution(self, archive_path: Optional[Path] = None) -> None:
        """Initialize the Darwin Gödel evolution system."""
        self._archive_path = archive_path or Path(".vertice/coder_evolution.json")
        self._archive = []
        self._current_variant = None
        self._evolution_history = []

        if self._archive_path.exists():
            self._load_archive()
        else:
            self._create_initial_variant()

    def _create_initial_variant(self) -> AgentVariant:
        """Create the initial agent variant (generation 0)."""
        variant = AgentVariant(
            id=self._generate_variant_id(),
            parent_id=None,
            generation=0,
            system_prompt=getattr(self, "SYSTEM_PROMPT", ""),
            tools=["generate", "refactor", "complete", "evaluate"],
            strategies={
                "max_corrections": 2,
                "quality_threshold": 0.6,
                "include_tests": False,
                "review_before_submit": False,
            },
        )
        self._archive.append(variant)
        self._current_variant = variant
        self._save_archive()
        return variant

    def _generate_variant_id(self) -> str:
        """Generate unique variant ID."""
        timestamp = datetime.now().isoformat()
        return hashlib.sha256(timestamp.encode()).hexdigest()[:12]

    def _load_archive(self) -> None:
        """Load the evolution archive from disk."""
        try:
            with open(self._archive_path, "r") as f:
                data = json.load(f)
            self._archive = [
                AgentVariant(
                    id=v["id"],
                    parent_id=v.get("parent_id"),
                    generation=v["generation"],
                    system_prompt=v["system_prompt"],
                    tools=v["tools"],
                    strategies=v["strategies"],
                    benchmark_scores=v.get("benchmark_scores", {}),
                    created_at=v.get("created_at", ""),
                    modification_description=v.get("modification_description", ""),
                )
                for v in data.get("variants", [])
            ]
            if self._archive:
                self._current_variant = max(self._archive, key=lambda v: v.fitness)
            logger.info(f"Loaded {len(self._archive)} variants from archive")
        except Exception as e:
            logger.warning(f"Failed to load archive: {e}")
            self._create_initial_variant()

    def _save_archive(self) -> None:
        """Save the evolution archive to disk."""
        self._archive_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "variants": [v.to_dict() for v in self._archive],
            "current_variant_id": self._current_variant.id if self._current_variant else None,
            "updated_at": datetime.now().isoformat(),
        }
        with open(self._archive_path, "w") as f:
            json.dump(data, f, indent=2)

    def get_archive(self) -> List[AgentVariant]:
        """Get the evolution archive."""
        if not hasattr(self, "_archive"):
            self._init_evolution()
        return self._archive

    def get_current_variant(self) -> AgentVariant:
        """Get the current best variant."""
        if not hasattr(self, "_current_variant") or self._current_variant is None:
            self._init_evolution()
        return self._current_variant  # type: ignore

    async def evolve(
        self,
        benchmark_tasks: List[BenchmarkTask],
        improvement_threshold: float = 0.05,
    ) -> EvolutionResult:
        """
        Run one Darwin Gödel evolution cycle.

        Args:
            benchmark_tasks: Tasks to evaluate performance.
            improvement_threshold: Minimum improvement to accept variant.

        Returns:
            EvolutionResult with new variant and scores.
        """
        if not hasattr(self, "_archive"):
            self._init_evolution()

        parent = self._sample_parent()
        logger.info(f"[DGM] Selected parent: {parent.id} (gen {parent.generation})")

        modifications = await self._propose_modifications(parent)
        logger.info(f"[DGM] Proposed modifications: {modifications}")

        new_variant = AgentVariant(
            id=self._generate_variant_id(),
            parent_id=parent.id,
            generation=parent.generation + 1,
            system_prompt=modifications.get("system_prompt", parent.system_prompt),
            tools=modifications.get("tools", parent.tools),
            strategies=modifications.get("strategies", parent.strategies),
            modification_description=modifications.get("description", ""),
        )

        scores = await self._run_benchmarks(new_variant, benchmark_tasks)
        new_variant.benchmark_scores = scores

        improvement = 0.0
        if parent.fitness > 0:
            improvement = (new_variant.fitness - parent.fitness) / parent.fitness
        elif new_variant.fitness > 0:
            improvement = 1.0

        success = improvement >= improvement_threshold

        if success:
            self._archive.append(new_variant)
            logger.info(f"[DGM] New variant added: {new_variant.id} (+{improvement*100:.1f}%)")

            if self._current_variant and new_variant.fitness > self._current_variant.fitness:
                self._current_variant = new_variant
                logger.info(f"[DGM] New best variant: {new_variant.id}")

            self._save_archive()
        else:
            logger.info(
                f"[DGM] Variant rejected: {improvement*100:.1f}% < {improvement_threshold*100:.1f}%"
            )

        result = EvolutionResult(
            new_variant=new_variant,
            improvement=improvement,
            modifications_made=list(modifications.keys()),
            benchmark_results=scores,
            success=success,
        )

        self._evolution_history.append(result)
        return result

    def _sample_parent(self) -> AgentVariant:
        """Sample parent with diversity-preserving selection."""
        if len(self._archive) == 1:
            return self._archive[0]

        if random.random() < 0.7:
            sorted_archive = sorted(self._archive, key=lambda v: v.fitness, reverse=True)
            top_half = sorted_archive[: max(1, len(sorted_archive) // 2)]
            return random.choice(top_half)
        else:
            return random.choice(self._archive)

    async def _propose_modifications(
        self,
        parent: AgentVariant,
    ) -> Dict[str, Any]:
        """Propose modifications to create a new variant."""
        modifications: Dict[str, Any] = {"description": ""}

        mod_types = ["prompt_enhancement", "strategy_tuning", "tool_addition"]
        selected = random.sample(mod_types, k=min(2, len(mod_types)))

        for mod_type in selected:
            if mod_type == "prompt_enhancement":
                enhancements = [
                    "\n\nBefore submitting code, validate the patch compiles and passes basic tests.",
                    "\n\nGenerate multiple solutions, then rank by quality and pick the best.",
                    "\n\nTrack what you've tried before and why it failed.",
                    "\n\nUse structured debugging: reproduce → isolate → fix → verify.",
                ]
                enhancement = random.choice(enhancements)
                if enhancement not in parent.system_prompt:
                    modifications["system_prompt"] = parent.system_prompt + enhancement
                    modifications["description"] += f"Added: {enhancement[:50]}... "

            elif mod_type == "strategy_tuning":
                new_strategies = parent.strategies.copy()
                tuning_options = [
                    ("max_corrections", lambda x: min(5, x + 1)),
                    (
                        "quality_threshold",
                        lambda x: max(0.5, min(0.9, x + random.uniform(-0.1, 0.1))),
                    ),
                    ("review_before_submit", lambda x: not x),
                ]
                option = random.choice(tuning_options)
                key, transform = option
                if key in new_strategies:
                    new_strategies[key] = transform(new_strategies[key])
                else:
                    new_strategies[key] = transform(0.6 if key == "quality_threshold" else 2)
                modifications["strategies"] = new_strategies
                modifications["description"] += f"Tuned {key}. "

            elif mod_type == "tool_addition":
                new_tools = [
                    "patch_validator",
                    "multi_solution_ranker",
                    "attempt_history",
                    "test_generator",
                ]
                for tool in new_tools:
                    if tool not in parent.tools:
                        modifications["tools"] = parent.tools + [tool]
                        modifications["description"] += f"Added tool: {tool}. "
                        break

        return modifications

    async def _run_benchmarks(
        self,
        variant: AgentVariant,
        tasks: List[BenchmarkTask],
    ) -> Dict[str, float]:
        """Run benchmark tasks and return scores."""
        scores: Dict[str, float] = {}

        for task in tasks:
            try:
                request = CodeGenerationRequest(
                    description=task.description,
                    language=task.language,
                    include_tests=variant.strategies.get("include_tests", False),
                )

                original_prompt = getattr(self, "SYSTEM_PROMPT", "")
                setattr(self, "SYSTEM_PROMPT", variant.system_prompt)

                result = await self.generate_with_evaluation(  # type: ignore
                    request,
                    max_corrections=variant.strategies.get("max_corrections", 2),
                )

                setattr(self, "SYSTEM_PROMPT", original_prompt)

                if result.evaluation:
                    base_score = result.evaluation.quality_score
                    if task.test_code and result.evaluation.valid_syntax:
                        test_passed = self._run_test_code(result.code, task.test_code)
                        if test_passed:
                            base_score = min(1.0, base_score + 0.2)
                    scores[task.id] = base_score
                else:
                    scores[task.id] = 0.0

            except Exception as e:
                logger.error(f"Benchmark {task.id} failed: {e}")
                scores[task.id] = 0.0

        return scores

    def _run_test_code(self, code: str, test_code: str) -> bool:
        """Run test code against generated code."""
        try:
            full_code = f"{code}\n\n{test_code}"
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(full_code)
                temp_path = f.name

            result = subprocess.run(
                ["python3", temp_path],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0

        except Exception as e:
            logger.warning(f"Test execution failed: {e}")
            return False
        finally:
            try:
                Path(temp_path).unlink()
            except (FileNotFoundError, PermissionError, OSError):
                pass

    def get_evolution_stats(self) -> Dict[str, Any]:
        """Get statistics about the evolution process."""
        if not hasattr(self, "_archive"):
            self._init_evolution()

        return {
            "total_variants": len(self._archive),
            "current_generation": self._current_variant.generation if self._current_variant else 0,
            "best_fitness": self._current_variant.fitness if self._current_variant else 0.0,
            "evolution_cycles": len(self._evolution_history),
            "successful_evolutions": sum(1 for r in self._evolution_history if r.success),
        }

    def get_lineage(self, variant_id: str) -> List[AgentVariant]:
        """Get the evolutionary lineage of a variant."""
        if not hasattr(self, "_archive"):
            self._init_evolution()

        lineage = []
        current_id: Optional[str] = variant_id

        while current_id:
            variant = next((v for v in self._archive if v.id == current_id), None)
            if variant:
                lineage.append(variant)
                current_id = variant.parent_id
            else:
                break

        return list(reversed(lineage))
