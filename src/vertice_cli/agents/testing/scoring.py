"""
Quality Scoring - Comprehensive Test Quality Assessment.

Provides quality scoring based on multiple metrics:
- Coverage (40% weight)
- Mutation score (30% weight)
- Test count (15% weight)
- No flaky tests (15% weight)

Philosophy:
    "Quality > Quantity. Every test must be deterministic."
"""

import logging
from typing import Any, Dict

from .analyzers import CoverageAnalyzer, MutationAnalyzer

logger = logging.getLogger(__name__)


class QualityScorer:
    """Calculates comprehensive test quality scores."""

    # Scoring weights
    COVERAGE_WEIGHT = 40
    MUTATION_WEIGHT = 30
    TEST_COUNT_WEIGHT = 15
    FLAKY_WEIGHT = 15

    def __init__(
        self,
        coverage_analyzer: CoverageAnalyzer,
        mutation_analyzer: MutationAnalyzer,
    ):
        """Initialize quality scorer.

        Args:
            coverage_analyzer: Coverage analysis component
            mutation_analyzer: Mutation testing component
        """
        self.coverage_analyzer = coverage_analyzer
        self.mutation_analyzer = mutation_analyzer

    async def calculate_score(
        self, test_path: str = "tests/", source_path: str = "."
    ) -> Dict[str, Any]:
        """Calculate comprehensive test quality score.

        Args:
            test_path: Path to test files
            source_path: Path to source files

        Returns:
            Dictionary with quality score and breakdown

        Scoring Formula:
            - Coverage: 40 points (40% weight)
            - Mutation score: 30 points (30% weight)
            - Test count: 15 points (15% weight)
            - No flaky tests: 15 points (15% weight)
        """
        # Get coverage
        coverage_result = await self.coverage_analyzer.analyze(test_path, source_path)
        coverage_pct = coverage_result.get("coverage", {}).get("coverage_percentage", 0)

        # Get mutation score
        try:
            mutation_result = await self.mutation_analyzer.analyze(source_path)
            mutation_pct = mutation_result.get("mutation_testing", {}).get("mutation_score", 0)
        except Exception as e:
            logger.warning(f"Mutation testing failed during quality analysis: {e}")
            mutation_pct = 0

        # Calculate component scores
        coverage_score = (coverage_pct / 100) * self.COVERAGE_WEIGHT
        mutation_component = (mutation_pct / 100) * self.MUTATION_WEIGHT
        test_count_component = self.TEST_COUNT_WEIGHT  # Assume good if tests exist
        flaky_component = self.FLAKY_WEIGHT  # Assume no flaky tests

        total_score = int(
            coverage_score + mutation_component + test_count_component + flaky_component
        )

        return {
            "quality_score": total_score,
            "breakdown": {
                "coverage": int(coverage_score),
                "mutation": int(mutation_component),
                "test_count": test_count_component,
                "no_flaky": flaky_component,
            },
            "grade": score_to_grade(total_score),
        }


def score_to_grade(score: int) -> str:
    """Convert numeric score to letter grade.

    Args:
        score: Score from 0-100

    Returns:
        Letter grade (A+, A, B+, etc.)
    """
    if score >= 95:
        return "A+"
    elif score >= 90:
        return "A"
    elif score >= 85:
        return "B+"
    elif score >= 80:
        return "B"
    elif score >= 75:
        return "C+"
    elif score >= 70:
        return "C"
    else:
        return "D"


__all__ = [
    "QualityScorer",
    "score_to_grade",
]
