"""
Auto-Critique System - Constitutional Layer 2 validation.

Implements Constitutional AI governance:
- P1: Completeness check
- P2: Validation check
- P6: Efficiency check
- LEI: Lazy Execution Index calculation
"""

from typing import Any, List

from .models import Critique, WorkflowStep


class AutoCritique:
    """
    Auto-critique system (Constitutional Layer 2).

    Features:
    - Completeness check (P1)
    - Validation check (P2)
    - Efficiency check (P6)
    - LEI calculation (Constitutional metric)
    """

    def __init__(self) -> None:
        self.lei_threshold = 1.0  # Constitutional requirement

    def critique_step(self, step: WorkflowStep, result: Any) -> Critique:
        """
        Critique step execution.

        Args:
            step: Executed step
            result: Step result

        Returns:
            Critique with Constitutional checks
        """
        # P1: Completeness
        completeness = self._check_completeness(result)

        # P2: Validation
        validation = self._validate_result(result)

        # P6: Efficiency
        efficiency = self._check_efficiency(step)

        # Constitutional: LEI calculation
        lei = self._calculate_lei(result)

        # Determine if passed
        passed = all([completeness > 0.9, validation, efficiency > 0.7, lei < self.lei_threshold])

        critique = Critique(
            passed=passed,
            completeness_score=completeness,
            validation_passed=validation,
            efficiency_score=efficiency,
            lei=lei,
        )

        # Generate issues and suggestions
        if not passed:
            critique.issues = self._identify_issues(completeness, validation, efficiency, lei)
            critique.suggestions = self._generate_suggestions(critique.issues)

        return critique

    def _check_completeness(self, result: Any) -> float:
        """Check if result is complete."""
        if result is None:
            return 0.0

        # Check for success indicator
        if hasattr(result, "success"):
            return 1.0 if result.success else 0.5

        return 0.8  # Assume mostly complete

    def _validate_result(self, result: Any) -> bool:
        """Validate result correctness."""
        if result is None:
            return False

        # Check for error indicators
        if hasattr(result, "success"):
            return bool(result.success)

        if hasattr(result, "error") and result.error:
            return False

        return True

    def _check_efficiency(self, step: WorkflowStep) -> float:
        """Check execution efficiency."""
        # Fast execution scores higher
        if step.execution_time < 1.0:
            return 1.0
        elif step.execution_time < 5.0:
            return 0.8
        elif step.execution_time < 10.0:
            return 0.6
        else:
            return 0.4

    def _calculate_lei(self, result: Any) -> float:
        """
        Calculate Lazy Execution Index (Constitutional metric).

        LEI = (lazy_patterns / total_lines) * 1000
        Target: < 1.0
        """
        # Extract code if available
        code = ""
        if hasattr(result, "data") and isinstance(result.data, str):
            code = result.data
        elif isinstance(result, str):
            code = result

        if not code:
            return 0.0  # No code to analyze

        # Lazy patterns
        lazy_patterns = [
            "TODO",
            "FIXME",
            "HACK",
            "XXX",
            "NotImplementedError",
            "pass  #",
            "... #",
            "raise NotImplementedError",
        ]

        lazy_count = sum(1 for pattern in lazy_patterns if pattern in code)

        lines = [line for line in code.split("\n") if line.strip()]
        total_lines = len(lines)

        if total_lines == 0:
            return 0.0

        lei = (lazy_count / total_lines) * 1000
        return lei

    def _identify_issues(
        self, completeness: float, validation: bool, efficiency: float, lei: float
    ) -> List[str]:
        """Identify specific issues."""
        issues = []

        if completeness < 0.9:
            issues.append(f"Incomplete result (score: {completeness:.2f})")

        if not validation:
            issues.append("Validation failed")

        if efficiency < 0.7:
            issues.append(f"Low efficiency (score: {efficiency:.2f})")

        if lei >= self.lei_threshold:
            issues.append(f"Lazy code detected (LEI: {lei:.2f}, threshold: {self.lei_threshold})")

        return issues

    def _generate_suggestions(self, issues: List[str]) -> List[str]:
        """Generate suggestions for fixes."""
        suggestions = []

        for issue in issues:
            if "Incomplete" in issue:
                suggestions.append("Complete all required fields")
            elif "Validation" in issue:
                suggestions.append("Fix validation errors")
            elif "efficiency" in issue:
                suggestions.append("Optimize execution time")
            elif "Lazy" in issue:
                suggestions.append("Replace TODO/FIXME with actual implementation")

        return suggestions
