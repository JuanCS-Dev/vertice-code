"""
Scoring Module - Code quality score calculation.

Provides score calculation based on issue severity, confidence,
and complexity metrics. Follows Constitution scoring algorithm.
"""

from typing import List

from .types import CodeIssue, ComplexityMetrics, IssueSeverity


def calculate_score(issues: List[CodeIssue], metrics: List[ComplexityMetrics]) -> int:
    """Calculate overall code quality score (0-100).

    Scoring algorithm:
    - Starts at 100
    - Deducts based on issue severity × confidence:
      CRITICAL: -30, HIGH: -15, MEDIUM: -7, LOW: -3, INFO: -1
    - Penalizes high average complexity (cyclomatic > 10, cognitive > 15)
    - Clamps to [0, 100] range

    Args:
        issues: List of found issues with severity and confidence
        metrics: List of complexity metrics per function

    Returns:
        Integer quality score between 0 and 100
    """
    score = 100

    severity_deductions = {
        IssueSeverity.CRITICAL: 30,
        IssueSeverity.HIGH: 15,
        IssueSeverity.MEDIUM: 7,
        IssueSeverity.LOW: 3,
        IssueSeverity.INFO: 1,
    }

    for issue in issues:
        deduction = severity_deductions.get(issue.severity, 5)
        score -= int(deduction * issue.confidence)

    if metrics:
        avg_cyclo = sum(m.cyclomatic for m in metrics) / len(metrics)
        avg_cognitive = sum(m.cognitive for m in metrics) / len(metrics)

        if avg_cyclo > 10:
            score -= int((avg_cyclo - 10) * 2)
        if avg_cognitive > 15:
            score -= int((avg_cognitive - 15) * 1.5)

    return max(0, min(100, score))


def calculate_risk(issues: List[CodeIssue], score: int) -> str:
    """Determine deployment risk level based on issues and score.

    Risk levels:
    - CRITICAL: Any critical issues OR score < 40
    - HIGH: More than 2 high issues OR score < 60
    - MEDIUM: More than 3 medium issues OR score <= 75
    - LOW: Otherwise

    Args:
        issues: List of found issues
        score: Quality score (0-100)

    Returns:
        Risk level string: "CRITICAL", "HIGH", "MEDIUM", or "LOW"
    """
    critical_count = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
    high_count = sum(1 for i in issues if i.severity == IssueSeverity.HIGH)
    medium_count = sum(1 for i in issues if i.severity == IssueSeverity.MEDIUM)

    if critical_count > 0 or score < 40:
        return "CRITICAL"
    if high_count > 2 or score < 60:
        return "HIGH"
    if medium_count > 3 or score <= 75:
        return "MEDIUM"
    return "LOW"


__all__ = ["calculate_score", "calculate_risk"]
