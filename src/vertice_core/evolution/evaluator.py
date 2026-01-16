"""
Benchmark Evaluator

GVU Verify phase implementation with empirical validation.

References:
- arXiv:2505.22954 (Darwin Gödel Machine - Sakana AI)
- arXiv:2512.02731 (GVU Operator Framework)
- arXiv:2310.06770 (SWE-bench)
- arXiv:2402.12874 (AgentBench)
- arXiv:2305.14314 (HumanEval+)
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from .types import (
    AgentVariant,
    EvolutionConfig,
    EvolutionResult,
    EvolutionStatus,
    VerificationResult,
)

logger = logging.getLogger(__name__)


class BenchmarkEvaluator:
    """
    GVU Verify phase: Evaluates agent variants using benchmark suites.

    Provides empirical grounding for self-improvement through:
    - Multi-benchmark validation (SWE-bench, AgentBench, HumanEval+)
    - Statistical significance testing
    - Confidence calibration

    References:
    - SWE-bench (arXiv:2310.06770): Real-world GitHub issues
    - AgentBench (arXiv:2402.12874): Multi-dimensional agent capabilities
    - HumanEval+ (arXiv:2305.14314): Rigorous code evaluation
    """

    # Benchmark weight schema following AgentBench dimensions
    BENCHMARK_WEIGHTS = {
        "overall": 0.25,
        "code_generation": 0.20,  # HumanEval+
        "debugging": 0.15,  # SWE-bench style
        "refactoring": 0.10,
        "reasoning": 0.15,  # AgentBench
        "tool_use": 0.10,  # AgentBench
        "instruction_following": 0.05,
    }

    def __init__(
        self,
        config: Optional[EvolutionConfig] = None,
        benchmark_runner: Optional[Callable[[AgentVariant], Dict[str, float]]] = None,
    ):
        """
        Initialize evaluator.

        Args:
            config: Evolution configuration
            benchmark_runner: Custom benchmark runner function
        """
        self._config = config or EvolutionConfig()
        self._benchmark_runner = benchmark_runner or self._default_benchmark
        self._evaluation_history: List[EvolutionResult] = []

        # Calibration data for confidence adjustment
        self._calibration_data: List[Dict[str, float]] = []

    async def evaluate(
        self,
        variant: AgentVariant,
        baseline: Optional[AgentVariant] = None,
    ) -> EvolutionResult:
        """
        GVU Verify phase: Evaluate a variant against benchmarks.

        Implements empirical validation from Darwin-Gödel Machine:
        1. Run benchmark suite
        2. Compare with baseline (if provided)
        3. Apply statistical tests
        4. Update confidence calibration

        Args:
            variant: Variant to evaluate
            baseline: Optional baseline variant for comparison

        Returns:
            EvolutionResult with fitness scores and verification
        """
        start_time = time.perf_counter()

        result = EvolutionResult(
            child_variant=variant,
            parent_variant=baseline or AgentVariant(),
            status=EvolutionStatus.VERIFYING,
        )

        verification = VerificationResult(proposal_id=variant.id)

        try:
            # Run benchmarks with timeout
            benchmark_results = await asyncio.wait_for(
                self._run_benchmarks(variant),
                timeout=self._config.benchmark_timeout_seconds,
            )

            # Calculate fitness score
            variant.benchmark_results = benchmark_results
            variant.fitness_score = self._calculate_fitness(benchmark_results)

            # Verification metrics
            verification.benchmark_total = len(benchmark_results)
            verification.benchmark_passed = sum(
                1 for score in benchmark_results.values() if score >= 0.5
            )
            verification.benchmark_failed = (
                verification.benchmark_total - verification.benchmark_passed
            )
            verification.verification_score = (
                verification.benchmark_passed / verification.benchmark_total
                if verification.benchmark_total > 0
                else 0.0
            )

            # Compare with baseline using statistical tests
            if baseline:
                result.fitness_delta = variant.fitness_score - baseline.fitness_score

                # Statistical significance check (simplified t-test approximation)
                is_significant = self._check_significance(
                    variant.benchmark_results,
                    baseline.benchmark_results,
                )

                if (
                    result.fitness_delta >= self._config.improvement_threshold
                    and is_significant
                    and verification.verification_score >= self._config.verification_threshold
                ):
                    result.status = EvolutionStatus.IMPROVED
                    verification.verified = True
                    result.reasoning = (
                        f"Verified improvement: {result.fitness_delta:.2%} "
                        f"(threshold: {self._config.improvement_threshold:.2%}), "
                        f"verification: {verification.verification_score:.2%}"
                    )

                    # Calculate kappa contribution
                    result.kappa_contribution = self._estimate_kappa_contribution(
                        result.fitness_delta,
                        verification.verification_score,
                    )
                else:
                    result.status = EvolutionStatus.REJECTED
                    verification.verified = False
                    reasons = []
                    if result.fitness_delta < self._config.improvement_threshold:
                        reasons.append(f"delta={result.fitness_delta:.2%}")
                    if not is_significant:
                        reasons.append("not_significant")
                    if verification.verification_score < self._config.verification_threshold:
                        reasons.append(f"verification={verification.verification_score:.2%}")
                    result.reasoning = f"Rejected: {', '.join(reasons)}"
            else:
                # No baseline, archive as initial variant
                result.status = EvolutionStatus.ARCHIVED
                verification.verified = True
                result.reasoning = "Initial variant, no baseline for comparison"

            # Update confidence calibration
            self._update_calibration(variant.fitness_score, verification.verification_score)

            # Estimate false positive risk
            verification.false_positive_risk = self._estimate_false_positive_risk(
                verification.verification_score,
                verification.benchmark_total,
            )
            verification.verification_confidence = 1.0 - verification.false_positive_risk

        except asyncio.TimeoutError:
            result.status = EvolutionStatus.REJECTED
            result.reasoning = f"Benchmark timeout after {self._config.benchmark_timeout_seconds}s"
            verification.reasoning = "timeout"
            logger.warning(f"[Evaluator] Timeout evaluating variant {variant.id}")

        except Exception as e:
            result.status = EvolutionStatus.REJECTED
            result.reasoning = f"Evaluation error: {str(e)}"
            verification.reasoning = f"error: {str(e)}"
            logger.error(f"[Evaluator] Error evaluating variant {variant.id}: {e}")

        result.verification_result = verification
        result.verification_time_ms = (time.perf_counter() - start_time) * 1000
        result.evaluation_time_ms = result.verification_time_ms
        self._evaluation_history.append(result)

        logger.info(
            f"[Evaluator] Variant {variant.id}: "
            f"fitness={variant.fitness_score:.3f}, "
            f"status={result.status.value}, "
            f"verified={verification.verified}, "
            f"time={result.verification_time_ms:.0f}ms"
        )

        return result

    async def compare(
        self,
        variant_a: AgentVariant,
        variant_b: AgentVariant,
    ) -> int:
        """
        Compare two variants with statistical rigor.

        Returns:
            1 if A is better, -1 if B is better, 0 if statistically equivalent
        """
        # Ensure both have been evaluated
        if not variant_a.benchmark_results:
            await self.evaluate(variant_a)
        if not variant_b.benchmark_results:
            await self.evaluate(variant_b)

        diff = variant_a.fitness_score - variant_b.fitness_score

        # Check statistical significance
        is_significant = self._check_significance(
            variant_a.benchmark_results,
            variant_b.benchmark_results,
        )

        if not is_significant or abs(diff) < self._config.improvement_threshold:
            return 0
        return 1 if diff > 0 else -1

    def get_evaluation_stats(self) -> Dict[str, Any]:
        """Get evaluation statistics."""
        if not self._evaluation_history:
            return {
                "total_evaluations": 0,
                "improved_count": 0,
                "rejected_count": 0,
                "avg_evaluation_time_ms": 0.0,
                "verification_rate": 0.0,
            }

        improved = sum(1 for r in self._evaluation_history if r.status == EvolutionStatus.IMPROVED)
        rejected = sum(1 for r in self._evaluation_history if r.status == EvolutionStatus.REJECTED)
        verified = sum(
            1
            for r in self._evaluation_history
            if r.verification_result and r.verification_result.verified
        )
        avg_time = sum(r.evaluation_time_ms for r in self._evaluation_history) / len(
            self._evaluation_history
        )
        avg_kappa = sum(r.kappa_contribution for r in self._evaluation_history) / len(
            self._evaluation_history
        )

        return {
            "total_evaluations": len(self._evaluation_history),
            "improved_count": improved,
            "rejected_count": rejected,
            "verified_count": verified,
            "improvement_rate": improved / len(self._evaluation_history),
            "verification_rate": verified / len(self._evaluation_history),
            "avg_evaluation_time_ms": avg_time,
            "avg_fitness_delta": (
                sum(r.fitness_delta for r in self._evaluation_history)
                / len(self._evaluation_history)
            ),
            "avg_kappa_contribution": avg_kappa,
        }

    async def _run_benchmarks(self, variant: AgentVariant) -> Dict[str, float]:
        """Run benchmark suite on variant."""
        if asyncio.iscoroutinefunction(self._benchmark_runner):
            return await self._benchmark_runner(variant)
        return self._benchmark_runner(variant)

    def _default_benchmark(self, variant: AgentVariant) -> Dict[str, float]:
        """
        Default benchmark implementation.

        Simulates multi-dimensional evaluation based on:
        - SWE-bench (code debugging/fixing)
        - HumanEval+ (code generation)
        - AgentBench (multi-dimensional capabilities)
        """
        base_score = 0.5

        # Prompts contribute (STaR-style reasoning)
        if variant.prompts:
            # Quality over quantity
            total_length = sum(len(p) for p in variant.prompts.values())
            prompt_bonus = min(0.15, (total_length / 5000) * 0.15)

            # Check for reasoning patterns
            reasoning_patterns = ["step by step", "verify", "consider", "analyze"]
            for prompt in variant.prompts.values():
                for pattern in reasoning_patterns:
                    if pattern in prompt.lower():
                        prompt_bonus += 0.02
            base_score += min(0.2, prompt_bonus)

        # Tools contribute (AgentBench tool use dimension)
        if variant.tools:
            tool_bonus = min(0.15, len(variant.tools) * 0.025)
            # Synergy bonus for complementary tools
            if "code_search" in variant.tools and "file_reader" in variant.tools:
                tool_bonus += 0.02
            if "test_runner" in variant.tools and "linter" in variant.tools:
                tool_bonus += 0.02
            base_score += tool_bonus

        # Workflow patterns (metacognition bonus)
        if variant.workflow.get("planning"):
            base_score += 0.05
        if variant.workflow.get("reflection"):
            base_score += 0.05
        if variant.workflow.get("verification"):  # Self-verification
            base_score += 0.03

        return {
            "overall": min(1.0, base_score),
            "code_generation": min(1.0, base_score * 0.95),
            "debugging": min(1.0, base_score * 0.90),
            "refactoring": min(1.0, base_score * 0.85),
            "reasoning": min(1.0, base_score * 0.88),
            "tool_use": min(1.0, base_score * 0.92),
            "instruction_following": min(1.0, base_score * 0.93),
        }

    def _calculate_fitness(self, benchmark_results: Dict[str, float]) -> float:
        """Calculate aggregate fitness from benchmark results using weighted average."""
        if not benchmark_results:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for key, score in benchmark_results.items():
            weight = self.BENCHMARK_WEIGHTS.get(key, 0.05)
            weighted_sum += score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _check_significance(
        self,
        results_a: Dict[str, float],
        results_b: Dict[str, float],
    ) -> bool:
        """
        Check if difference between results is statistically significant.

        Simplified approach using effect size (Cohen's d).
        """
        if not results_a or not results_b:
            return False

        # Get common keys
        common_keys = set(results_a.keys()) & set(results_b.keys())
        if not common_keys:
            return False

        scores_a = [results_a[k] for k in common_keys]
        scores_b = [results_b[k] for k in common_keys]

        # Calculate means
        mean_a = sum(scores_a) / len(scores_a)
        mean_b = sum(scores_b) / len(scores_b)

        # Calculate pooled standard deviation
        var_a = sum((x - mean_a) ** 2 for x in scores_a) / len(scores_a)
        var_b = sum((x - mean_b) ** 2 for x in scores_b) / len(scores_b)
        pooled_std = ((var_a + var_b) / 2) ** 0.5

        if pooled_std == 0:
            return abs(mean_a - mean_b) > 0

        # Cohen's d effect size
        cohens_d = abs(mean_a - mean_b) / pooled_std

        # Medium effect size threshold (0.5)
        return cohens_d >= 0.5

    def _estimate_kappa_contribution(
        self,
        fitness_delta: float,
        verification_score: float,
    ) -> float:
        """Estimate contribution to κ coefficient."""
        # κ contribution is weighted by verification confidence
        return fitness_delta * verification_score

    def _estimate_false_positive_risk(
        self,
        verification_score: float,
        sample_size: int,
    ) -> float:
        """
        Estimate risk of false positive improvement claim.

        Based on statistical power analysis.
        """
        if sample_size == 0:
            return 1.0

        # Simplified false positive estimation
        # More samples and higher verification score = lower risk
        base_risk = 0.05  # Baseline 5% false positive rate
        sample_factor = min(1.0, sample_size / 10)  # More samples = lower risk
        score_factor = verification_score

        return base_risk * (1.0 - 0.5 * sample_factor) * (1.0 - 0.5 * score_factor)

    def _update_calibration(
        self,
        fitness_score: float,
        verification_score: float,
    ) -> None:
        """Update confidence calibration data."""
        self._calibration_data.append(
            {
                "fitness": fitness_score,
                "verification": verification_score,
                "timestamp": time.time(),
            }
        )

        # Keep only recent calibration data
        max_calibration_samples = 100
        if len(self._calibration_data) > max_calibration_samples:
            self._calibration_data = self._calibration_data[-max_calibration_samples:]
