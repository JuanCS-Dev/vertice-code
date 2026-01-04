"""
Test Analyzers - Coverage, Mutation, and Flaky Test Detection.

Provides analysis capabilities for test quality assessment:
- Coverage analysis (pytest-cov integration)
- Mutation testing (mutmut integration)
- Flaky test detection (multiple runs)

Philosophy (Boris Cherny):
    "Tests are executable specifications. If it's not tested, it's broken."
"""

import json
import logging
import re
from typing import Any, Callable, Dict, List

from .models import CoverageReport, FlakyTest, MutationResult

logger = logging.getLogger(__name__)


class CoverageAnalyzer:
    """Analyzes test coverage using pytest-cov."""

    def __init__(self, execute_tool: Callable[..., Any], min_coverage_threshold: float = 90.0):
        """Initialize coverage analyzer.

        Args:
            execute_tool: Async function to execute tools
            min_coverage_threshold: Minimum acceptable coverage percentage
        """
        self._execute_tool = execute_tool
        self.min_coverage_threshold = min_coverage_threshold

    async def analyze(self, test_path: str = "tests/", source_path: str = ".") -> Dict[str, Any]:
        """Analyze test coverage.

        Args:
            test_path: Path to test files
            source_path: Path to source files

        Returns:
            Dictionary with coverage data and quality metrics
        """
        # Run pytest with coverage
        cmd = f"pytest {test_path} --cov={source_path} --cov-report=json --quiet"
        await self._execute_tool("bash_command", {"command": cmd})

        # Parse coverage JSON
        coverage_data = await self._parse_coverage_json()

        # Calculate quality score
        quality_score = self._calculate_coverage_score(coverage_data)

        return {
            "coverage": {
                "total_statements": coverage_data.total_statements,
                "covered_statements": coverage_data.covered_statements,
                "coverage_percentage": coverage_data.coverage_percentage,
                "branch_coverage": coverage_data.branch_coverage,
                "missing_lines_count": len(coverage_data.missing_lines),
            },
            "quality_score": quality_score,
            "meets_threshold": coverage_data.coverage_percentage >= self.min_coverage_threshold,
        }

    async def _parse_coverage_json(self) -> CoverageReport:
        """Parse coverage.json file.

        Returns:
            CoverageReport object
        """
        try:
            result = await self._execute_tool("read_file", {"path": "coverage.json"})
            data = json.loads(result.get("content", "{}"))

            totals = data.get("totals", {})

            return CoverageReport(
                total_statements=totals.get("num_statements", 0),
                covered_statements=totals.get("covered_lines", 0),
                coverage_percentage=totals.get("percent_covered", 0.0),
                missing_lines=[],
                branches_total=totals.get("num_branches", 0),
                branches_covered=totals.get("covered_branches", 0),
            )
        except (json.JSONDecodeError, KeyError, TypeError, FileNotFoundError):
            return CoverageReport(
                total_statements=0,
                covered_statements=0,
                coverage_percentage=0.0,
                missing_lines=[],
                branches_total=0,
                branches_covered=0,
            )

    def _calculate_coverage_score(self, coverage: CoverageReport) -> int:
        """Calculate quality score from coverage metrics.

        Args:
            coverage: CoverageReport object

        Returns:
            Score from 0-100

        Formula:
            base_score = coverage_percentage * 0.7
            branch_bonus = branch_coverage * 0.3
            final_score = base_score + branch_bonus
        """
        base_score = coverage.coverage_percentage * 0.7
        branch_bonus = coverage.branch_coverage * 0.3

        return min(100, int(base_score + branch_bonus))


class MutationAnalyzer:
    """Runs mutation testing using mutmut."""

    def __init__(self, execute_tool: Callable[..., Any], min_mutation_score: float = 80.0):
        """Initialize mutation analyzer.

        Args:
            execute_tool: Async function to execute tools
            min_mutation_score: Minimum acceptable mutation score
        """
        self._execute_tool = execute_tool
        self.min_mutation_score = min_mutation_score

    async def analyze(self, source_path: str = ".") -> Dict[str, Any]:
        """Run mutation testing.

        Args:
            source_path: Path to source files

        Returns:
            Dictionary with mutation testing results
        """
        # Run mutmut
        cmd = f"mutmut run --paths-to-mutate={source_path} --runner='pytest -x'"
        await self._execute_tool("bash_command", {"command": cmd})

        # Get results
        result = await self._execute_tool("bash_command", {"command": "mutmut results"})

        # Parse mutation results
        mutation_result = self._parse_mutation_results(result.get("output", ""))

        # Calculate score
        quality_score = int(mutation_result.mutation_score)

        return {
            "mutation_testing": {
                "total_mutants": mutation_result.total_mutants,
                "killed_mutants": mutation_result.killed_mutants,
                "survived_mutants": mutation_result.survived_mutants,
                "timeout_mutants": mutation_result.timeout_mutants,
                "mutation_score": mutation_result.mutation_score,
            },
            "quality_score": quality_score,
            "meets_threshold": mutation_result.mutation_score >= self.min_mutation_score,
        }

    def _parse_mutation_results(self, output: str) -> MutationResult:
        """Parse mutmut results output.

        Args:
            output: mutmut results command output

        Returns:
            MutationResult object
        """
        killed = len(re.findall(r"KILLED", output))
        survived = len(re.findall(r"SURVIVED", output))
        timeout = len(re.findall(r"TIMEOUT", output))
        total = killed + survived + timeout

        return MutationResult(
            total_mutants=total,
            killed_mutants=killed,
            survived_mutants=survived,
            timeout_mutants=timeout,
        )


class FlakyDetector:
    """Detects flaky tests through multiple runs."""

    def __init__(self, execute_tool: Callable[..., Any], default_runs: int = 5):
        """Initialize flaky detector.

        Args:
            execute_tool: Async function to execute tools
            default_runs: Default number of test runs for detection
        """
        self._execute_tool = execute_tool
        self.default_runs = default_runs

    async def detect(self, test_path: str = "tests/", runs: int | None = None) -> Dict[str, Any]:
        """Detect flaky tests by running multiple times.

        Args:
            test_path: Path to tests
            runs: Number of times to run tests

        Returns:
            Dictionary with flaky test results
        """
        runs = runs or self.default_runs
        flaky_tests = await self._detect_flaky_tests(test_path, runs)

        return {
            "flaky_tests": [
                {
                    "name": ft.name,
                    "file_path": ft.file_path,
                    "failure_rate": ft.failure_rate,
                    "error_messages": ft.error_messages,
                    "suspected_cause": ft.suspected_cause,
                }
                for ft in flaky_tests
            ],
            "flaky_count": len(flaky_tests),
        }

    async def _detect_flaky_tests(self, test_path: str, runs: int) -> List[FlakyTest]:
        """Run tests multiple times to detect flakiness.

        Args:
            test_path: Path to tests
            runs: Number of times to run tests

        Returns:
            List of detected flaky tests
        """
        test_results: Dict[str, List[bool]] = {}

        for _ in range(runs):
            result = await self._execute_tool("bash_command", {"command": f"pytest {test_path} -v"})

            # Parse test results
            output = result.get("output", "")
            for line in output.split("\n"):
                if "::" in line and ("PASSED" in line or "FAILED" in line):
                    test_name = line.split("::")[0].strip()
                    if test_name:
                        if test_name not in test_results:
                            test_results[test_name] = []
                        test_results[test_name].append("PASSED" in line)

        # Identify flaky tests (inconsistent results)
        flaky_tests: List[FlakyTest] = []
        for test_name, results in test_results.items():
            if len(set(results)) > 1:  # Both True and False present
                failure_rate = (results.count(False) / len(results)) * 100
                flaky_tests.append(
                    FlakyTest(
                        name=test_name,
                        file_path=test_path,
                        failure_rate=failure_rate,
                        error_messages=["Intermittent failure"],
                        suspected_cause="Race condition or timing issue",
                    )
                )

        return flaky_tests


__all__ = [
    "CoverageAnalyzer",
    "MutationAnalyzer",
    "FlakyDetector",
]
