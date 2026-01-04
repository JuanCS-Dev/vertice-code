"""
Testing Models - Enums and Dataclasses for Testing Agent.

Contains type-safe data structures for test cases, coverage reports,
mutation results, and flaky test detection.

Philosophy (Boris Cherny):
    "Type-safe interfaces eliminate runtime errors at compile time."
"""

from dataclasses import dataclass
from enum import Enum
from typing import List


class TestFramework(str, Enum):
    """Supported test frameworks."""

    PYTEST = "pytest"
    UNITTEST = "unittest"
    DOCTEST = "doctest"


class TestType(str, Enum):
    """Types of tests that can be generated."""

    UNIT = "unit"
    INTEGRATION = "integration"
    FUNCTIONAL = "functional"
    EDGE_CASE = "edge_case"
    PROPERTY_BASED = "property_based"
    TUI = "tui"


@dataclass(frozen=True)
class TestCase:
    """Represents a single test case.

    Attributes:
        name: Test function name (e.g., test_user_creation)
        code: Complete test function code
        test_type: Type of test (unit, integration, etc.)
        target: Function/class being tested
        assertions: Number of assertions in test
        complexity: Estimated complexity (1-10)
    """

    name: str
    code: str
    test_type: TestType
    target: str
    assertions: int
    complexity: int

    def __post_init__(self) -> None:
        """Validate test case fields."""
        if not self.name.startswith("test_"):
            object.__setattr__(self, "name", f"test_{self.name}")
        if self.assertions < 0:
            raise ValueError("Assertions count cannot be negative")
        if not 1 <= self.complexity <= 10:
            raise ValueError("Complexity must be between 1 and 10")


@dataclass(frozen=True)
class CoverageReport:
    """Coverage analysis result.

    Attributes:
        total_statements: Total executable statements
        covered_statements: Statements executed by tests
        coverage_percentage: Coverage as percentage (0-100)
        missing_lines: Line numbers not covered
        branches_total: Total conditional branches
        branches_covered: Branches executed
    """

    total_statements: int
    covered_statements: int
    coverage_percentage: float
    missing_lines: List[int]
    branches_total: int
    branches_covered: int

    @property
    def branch_coverage(self) -> float:
        """Calculate branch coverage percentage."""
        if self.branches_total == 0:
            return 100.0
        return (self.branches_covered / self.branches_total) * 100.0


@dataclass(frozen=True)
class MutationResult:
    """Mutation testing result.

    Attributes:
        total_mutants: Total mutations generated
        killed_mutants: Mutations caught by tests
        survived_mutants: Mutations that passed tests
        timeout_mutants: Mutations that caused timeout
    """

    total_mutants: int
    killed_mutants: int
    survived_mutants: int
    timeout_mutants: int

    @property
    def mutation_score(self) -> float:
        """Calculate mutation score (higher is better)."""
        if self.total_mutants == 0:
            return 100.0
        return (self.killed_mutants / self.total_mutants) * 100.0


@dataclass(frozen=True)
class FlakyTest:
    """Information about a flaky test.

    Attributes:
        name: Test function name
        file_path: Path to test file
        failure_rate: Percentage of runs that fail (0-100)
        error_messages: Unique error messages seen
        suspected_cause: Most likely cause of flakiness
    """

    name: str
    file_path: str
    failure_rate: float
    error_messages: List[str]
    suspected_cause: str


__all__ = [
    "TestFramework",
    "TestType",
    "TestCase",
    "CoverageReport",
    "MutationResult",
    "FlakyTest",
]
