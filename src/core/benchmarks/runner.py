"""
Benchmark Runner

Executes benchmark suites and collects results.

Reference:
- SWE-bench (Jimenez et al., 2024)
- Terminal-Bench (2025)
"""

from __future__ import annotations

import uuid
import time
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

from .types import (
    BenchmarkTask,
    BenchmarkResult,
    BenchmarkSuite,
    BenchmarkStatus,
    SuiteRunResult,
)
from .validators import (
    BenchmarkValidator,
    ExactMatchValidator,
    ContainsValidator,
    TestPassValidator,
)

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """
    Executes benchmark suites and collects results.

    Supports:
    - Async execution
    - Timeout handling
    - Progress tracking
    - Result aggregation
    """

    def __init__(self) -> None:
        self._validators: Dict[str, BenchmarkValidator] = {
            "exact_match": ExactMatchValidator(),
            "contains": ContainsValidator(),
            "test_pass": TestPassValidator(),
        }

    def register_validator(self, name: str, validator: BenchmarkValidator) -> None:
        """Register a custom validator."""
        self._validators[name] = validator

    async def run_suite(
        self,
        suite: BenchmarkSuite,
        executor: Callable[[BenchmarkTask], Any],
        progress_callback: Optional[Callable[[int, int, BenchmarkResult], None]] = None,
    ) -> SuiteRunResult:
        """
        Run a complete benchmark suite.

        Args:
            suite: The benchmark suite to run
            executor: Function to execute each task
            progress_callback: Optional callback for progress updates
        """
        run_id = str(uuid.uuid4())
        start_time = datetime.now().isoformat()
        results: List[BenchmarkResult] = []

        logger.info(f"[Benchmark] Starting suite: {suite.name} ({len(suite.tasks)} tasks)")

        for i, task in enumerate(suite.tasks):
            result = await self._run_task(task, executor)
            results.append(result)

            if progress_callback:
                progress_callback(i + 1, len(suite.tasks), result)

            logger.debug(f"[Benchmark] Task {i+1}/{len(suite.tasks)}: {result.status.value}")

        end_time = datetime.now().isoformat()

        # Aggregate results
        passed = sum(1 for r in results if r.status == BenchmarkStatus.PASSED)
        failed = sum(1 for r in results if r.status == BenchmarkStatus.FAILED)
        errors = sum(1 for r in results if r.status == BenchmarkStatus.ERROR)
        timeouts = sum(1 for r in results if r.status == BenchmarkStatus.TIMEOUT)
        skipped = sum(1 for r in results if r.status == BenchmarkStatus.SKIPPED)

        total_time = sum(r.execution_time_ms for r in results)
        total_tokens = sum(r.tokens_used for r in results)

        suite_result = SuiteRunResult(
            suite_id=suite.id,
            run_id=run_id,
            results=results,
            start_time=start_time,
            end_time=end_time,
            total_tasks=len(suite.tasks),
            passed=passed,
            failed=failed,
            errors=errors,
            timeouts=timeouts,
            skipped=skipped,
            avg_execution_time_ms=total_time / len(results) if results else 0,
            total_tokens=total_tokens,
            pass_rate=passed / len(suite.tasks) if suite.tasks else 0,
        )

        logger.info(
            f"[Benchmark] Suite complete: {passed}/{len(suite.tasks)} passed "
            f"({suite_result.pass_rate:.1%})"
        )

        return suite_result

    async def _run_task(
        self,
        task: BenchmarkTask,
        executor: Callable[[BenchmarkTask], Any],
    ) -> BenchmarkResult:
        """Run a single benchmark task."""
        start_time = time.time()

        try:
            # Execute with timeout
            actual = await asyncio.wait_for(
                self._execute(task, executor),
                timeout=task.timeout_seconds,
            )

            execution_time = int((time.time() - start_time) * 1000)

            # Validate result
            validator_name = task.validation_fn or "exact_match"
            validator = self._validators.get(validator_name, ExactMatchValidator())

            passed, score, details = validator.validate(task, actual or {})

            return BenchmarkResult(
                task_id=task.id,
                status=BenchmarkStatus.PASSED if passed else BenchmarkStatus.FAILED,
                actual_output=actual,
                execution_time_ms=execution_time,
                partial_score=score,
                validation_details=details,
            )

        except asyncio.TimeoutError:
            return BenchmarkResult(
                task_id=task.id,
                status=BenchmarkStatus.TIMEOUT,
                execution_time_ms=task.timeout_seconds * 1000,
                error_message=f"Timeout after {task.timeout_seconds}s",
            )

        except Exception as e:
            return BenchmarkResult(
                task_id=task.id,
                status=BenchmarkStatus.ERROR,
                execution_time_ms=int((time.time() - start_time) * 1000),
                error_message=str(e),
            )

    async def _execute(
        self,
        task: BenchmarkTask,
        executor: Callable[[BenchmarkTask], Any],
    ) -> Any:
        """Execute task with the provided executor."""
        if asyncio.iscoroutinefunction(executor):
            return await executor(task)
        else:
            return executor(task)
