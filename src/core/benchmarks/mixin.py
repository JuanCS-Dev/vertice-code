"""
Benchmark Mixin

Mixin providing benchmarking capabilities to agents.

Reference:
- SWE-bench (Jimenez et al., 2024)
- Terminal-Bench (2025)
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from .types import (
    BenchmarkTask,
    BenchmarkResult,
    BenchmarkSuite,
    SuiteRunResult,
)
from .runner import BenchmarkRunner
from .suites import (
    create_swe_bench_mini,
    create_terminal_bench_mini,
    create_context_bench_mini,
    create_agent_bench_mini,
)

logger = logging.getLogger(__name__)


class BenchmarkMixin:
    """
    Mixin providing benchmarking capabilities.

    Add to orchestrator for:
    - Running built-in benchmark suites
    - Custom benchmark creation
    - Performance tracking
    - Regression detection
    """

    def _init_benchmarks(self) -> None:
        """Initialize benchmarking system."""
        self._benchmark_runner = BenchmarkRunner()
        self._benchmark_history: List[SuiteRunResult] = []
        self._registered_suites: Dict[str, BenchmarkSuite] = {}
        self._benchmarks_initialized = True

        # Register built-in suites
        for suite_fn in [
            create_swe_bench_mini,
            create_terminal_bench_mini,
            create_context_bench_mini,
            create_agent_bench_mini,
        ]:
            suite = suite_fn()
            self._registered_suites[suite.id] = suite

        logger.info(f"[Benchmark] Initialized with {len(self._registered_suites)} suites")

    def register_suite(self, suite: BenchmarkSuite) -> None:
        """Register a custom benchmark suite."""
        if not hasattr(self, "_registered_suites"):
            self._init_benchmarks()
        self._registered_suites[suite.id] = suite

    def get_available_suites(self) -> List[str]:
        """Get list of available benchmark suites."""
        if not hasattr(self, "_registered_suites"):
            self._init_benchmarks()
        return list(self._registered_suites.keys())

    async def run_benchmark(
        self,
        suite_id: str,
        executor: Optional[Callable[[BenchmarkTask], Any]] = None,
        progress_callback: Optional[Callable[[int, int, BenchmarkResult], None]] = None,
    ) -> Optional[SuiteRunResult]:
        """
        Run a registered benchmark suite.

        Args:
            suite_id: ID of the suite to run
            executor: Custom executor (defaults to self._execute_benchmark_task)
            progress_callback: Optional progress callback
        """
        if not hasattr(self, "_benchmark_runner"):
            self._init_benchmarks()

        suite = self._registered_suites.get(suite_id)
        if not suite:
            logger.error(f"[Benchmark] Suite not found: {suite_id}")
            return None

        # Use default executor if none provided
        if executor is None:
            executor = self._default_benchmark_executor

        result = await self._benchmark_runner.run_suite(
            suite,
            executor,
            progress_callback,
        )

        self._benchmark_history.append(result)
        return result

    def _default_benchmark_executor(self, task: BenchmarkTask) -> Dict[str, Any]:
        """Default executor that returns empty results."""
        # Subclasses should override this
        return {"status": "not_implemented"}

    def get_benchmark_history(
        self,
        suite_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[SuiteRunResult]:
        """Get benchmark run history."""
        if not hasattr(self, "_benchmark_history"):
            return []

        history = self._benchmark_history

        if suite_id:
            history = [h for h in history if h.suite_id == suite_id]

        return history[-limit:]

    def compare_runs(
        self,
        run_id_a: str,
        run_id_b: str,
    ) -> Optional[Dict[str, Any]]:
        """Compare two benchmark runs for regression detection."""
        if not hasattr(self, "_benchmark_history"):
            return None

        run_a = next((r for r in self._benchmark_history if r.run_id == run_id_a), None)
        run_b = next((r for r in self._benchmark_history if r.run_id == run_id_b), None)

        if not run_a or not run_b:
            return None

        return {
            "run_a": run_id_a,
            "run_b": run_id_b,
            "pass_rate_delta": run_b.pass_rate - run_a.pass_rate,
            "avg_time_delta_ms": run_b.avg_execution_time_ms - run_a.avg_execution_time_ms,
            "regression": run_b.pass_rate < run_a.pass_rate - 0.05,  # 5% threshold
            "improvement": run_b.pass_rate > run_a.pass_rate + 0.05,
        }

    def get_benchmark_status(self) -> Dict[str, Any]:
        """Get benchmarking system status."""
        if not hasattr(self, "_benchmark_runner"):
            return {"initialized": False}

        return {
            "initialized": True,
            "registered_suites": list(self._registered_suites.keys()),
            "total_runs": len(self._benchmark_history),
            "last_run": (
                self._benchmark_history[-1].to_dict()
                if self._benchmark_history else None
            ),
        }
