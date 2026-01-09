"""
Benchmark Validators

Validation classes for benchmark outputs.

Reference:
- SWE-bench (Jimenez et al., 2024)
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from .types import BenchmarkTask


class BenchmarkValidator:
    """Base class for benchmark validators."""

    def validate(
        self,
        task: BenchmarkTask,
        actual: Dict[str, Any],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Validate benchmark output.

        Returns:
            Tuple of (passed, partial_score, details)
        """
        raise NotImplementedError


class ExactMatchValidator(BenchmarkValidator):
    """Validates exact match against expected output."""

    def validate(
        self,
        task: BenchmarkTask,
        actual: Dict[str, Any],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        if task.expected_output is None:
            return True, 1.0, {"message": "No expected output defined"}

        passed = actual == task.expected_output
        return passed, 1.0 if passed else 0.0, {
            "expected": task.expected_output,
            "actual": actual,
        }


class ContainsValidator(BenchmarkValidator):
    """Validates that output contains expected elements."""

    def validate(
        self,
        task: BenchmarkTask,
        actual: Dict[str, Any],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        if task.expected_output is None:
            return True, 1.0, {"message": "No expected output defined"}

        matches: float = 0.0
        total = len(task.expected_output)

        for key, expected_value in task.expected_output.items():
            if key in actual:
                if actual[key] == expected_value:
                    matches += 1
                elif isinstance(expected_value, str) and expected_value in str(actual[key]):
                    matches += 0.5

        score = matches / total if total > 0 else 1.0
        passed = score >= 0.8  # 80% threshold

        return passed, score, {
            "matches": matches,
            "total": total,
            "score": score,
        }


class TestPassValidator(BenchmarkValidator):
    """Validates by running tests (SWE-bench style)."""

    def __init__(self, test_command: str = "pytest") -> None:
        self.test_command = test_command

    def validate(
        self,
        task: BenchmarkTask,
        actual: Dict[str, Any],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        # In production, this would actually run tests
        # For now, we simulate based on output structure
        if "test_results" in actual:
            results = actual["test_results"]
            passed = results.get("passed", 0)
            failed = results.get("failed", 0)
            total = passed + failed

            if total == 0:
                return False, 0.0, {"error": "No tests executed"}

            score = passed / total
            return failed == 0, score, {
                "passed": passed,
                "failed": failed,
                "total": total,
            }

        return False, 0.0, {"error": "No test results in output"}
