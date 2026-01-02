"""
Confidence Calibration - Dynamic threshold adjustment.

Implements adaptive confidence thresholds based on historical accuracy.
Prevents both over-confidence and under-confidence in predictions.

Reference: HEROIC_IMPLEMENTATION_PLAN.md Sprint 1.3
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class PredictionCategory(str, Enum):
    """Categories of predictions that can be calibrated."""
    ROUTING = "routing"           # Agent routing decisions
    TOOL_SELECTION = "tool_selection"  # Which tool to use
    CODE_GENERATION = "code_generation"  # Code output quality
    INTENT = "intent"             # Intent classification
    COMPLEXITY = "complexity"     # Task complexity assessment


@dataclass
class CalibrationRecord:
    """Record of a prediction for calibration."""
    category: PredictionCategory
    confidence: float
    was_correct: bool
    timestamp: float = field(default_factory=time.time)
    details: Optional[str] = None


@dataclass
class CalibrationStats:
    """Statistics for a category."""
    category: PredictionCategory
    total_predictions: int
    correct_predictions: int
    accuracy: float
    current_threshold: float
    recommended_threshold: float


class ConfidenceCalibrator:
    """
    Adaptive confidence thresholds based on historical accuracy.

    Key principles:
    - Start with conservative thresholds
    - Lower thresholds as accuracy improves
    - Raise thresholds when accuracy drops
    - Maintain separate thresholds per category

    Usage:
        calibrator = ConfidenceCalibrator()

        # When making a prediction
        threshold = calibrator.get_threshold(PredictionCategory.ROUTING)
        if confidence >= threshold:
            proceed_with_action()

        # After outcome is known
        calibrator.record_outcome(
            category=PredictionCategory.ROUTING,
            confidence=0.85,
            was_correct=True
        )
    """

    # Default thresholds (conservative)
    DEFAULT_THRESHOLDS = {
        PredictionCategory.ROUTING: 0.70,
        PredictionCategory.TOOL_SELECTION: 0.80,
        PredictionCategory.CODE_GENERATION: 0.85,
        PredictionCategory.INTENT: 0.60,
        PredictionCategory.COMPLEXITY: 0.65,
    }

    # Calibration parameters
    MIN_THRESHOLD = 0.40  # Never go below this
    MAX_THRESHOLD = 0.95  # Never go above this
    RECALIBRATION_WINDOW = 100  # Use last N predictions
    MIN_SAMPLES_FOR_CALIBRATION = 10  # Need at least N samples

    def __init__(self):
        self.history: List[CalibrationRecord] = []
        self.thresholds: Dict[PredictionCategory, float] = dict(self.DEFAULT_THRESHOLDS)
        self._last_calibration: float = 0

    def get_threshold(self, category: PredictionCategory) -> float:
        """
        Get current threshold for a category.

        Args:
            category: Prediction category

        Returns:
            Current calibrated threshold
        """
        return self.thresholds.get(category, 0.7)

    def should_proceed(self, category: PredictionCategory, confidence: float) -> bool:
        """
        Check if confidence meets threshold for proceeding.

        Args:
            category: Prediction category
            confidence: Confidence score (0-1)

        Returns:
            True if confidence meets or exceeds threshold
        """
        threshold = self.get_threshold(category)
        return confidence >= threshold

    def record_outcome(
        self,
        category: PredictionCategory,
        confidence: float,
        was_correct: bool,
        details: Optional[str] = None,
    ) -> None:
        """
        Record prediction outcome for calibration.

        Args:
            category: Prediction category
            confidence: Original confidence score
            was_correct: Whether prediction was correct
            details: Optional details about the prediction
        """
        record = CalibrationRecord(
            category=category,
            confidence=confidence,
            was_correct=was_correct,
            details=details,
        )
        self.history.append(record)

        # Trigger recalibration periodically
        if len(self.history) % 10 == 0:
            self._recalibrate()

    def _recalibrate(self) -> None:
        """Adjust thresholds based on recent accuracy."""
        recent = self.history[-self.RECALIBRATION_WINDOW:]

        for category in PredictionCategory:
            category_records = [r for r in recent if r.category == category]

            if len(category_records) < self.MIN_SAMPLES_FOR_CALIBRATION:
                continue

            # Calculate accuracy
            correct = sum(1 for r in category_records if r.was_correct)
            accuracy = correct / len(category_records)

            current_threshold = self.thresholds[category]
            new_threshold = current_threshold

            # Adjust threshold based on accuracy
            if accuracy < 0.70:
                # Low accuracy: increase threshold (be more conservative)
                new_threshold = min(self.MAX_THRESHOLD, current_threshold + 0.05)
                logger.info(
                    f"[Calibrator] {category.value}: accuracy {accuracy:.0%} < 70%, "
                    f"raising threshold {current_threshold:.2f} → {new_threshold:.2f}"
                )
            elif accuracy > 0.90:
                # High accuracy: decrease threshold (can be more confident)
                new_threshold = max(self.MIN_THRESHOLD, current_threshold - 0.02)
                logger.info(
                    f"[Calibrator] {category.value}: accuracy {accuracy:.0%} > 90%, "
                    f"lowering threshold {current_threshold:.2f} → {new_threshold:.2f}"
                )

            self.thresholds[category] = new_threshold

        self._last_calibration = time.time()

    def get_stats(self, category: Optional[PredictionCategory] = None) -> List[CalibrationStats]:
        """
        Get calibration statistics.

        Args:
            category: Specific category, or None for all

        Returns:
            List of CalibrationStats
        """
        categories = [category] if category else list(PredictionCategory)
        stats = []

        for cat in categories:
            records = [r for r in self.history if r.category == cat]
            total = len(records)
            correct = sum(1 for r in records if r.was_correct)
            accuracy = correct / total if total > 0 else 0.0

            current = self.thresholds[cat]
            recommended = self._calculate_recommended_threshold(accuracy)

            stats.append(CalibrationStats(
                category=cat,
                total_predictions=total,
                correct_predictions=correct,
                accuracy=accuracy,
                current_threshold=current,
                recommended_threshold=recommended,
            ))

        return stats

    def _calculate_recommended_threshold(self, accuracy: float) -> float:
        """Calculate recommended threshold based on accuracy."""
        if accuracy < 0.60:
            return 0.90
        elif accuracy < 0.70:
            return 0.85
        elif accuracy < 0.80:
            return 0.75
        elif accuracy < 0.90:
            return 0.65
        else:
            return 0.50

    def get_report(self) -> str:
        """Generate a calibration report."""
        lines = [
            "=" * 50,
            "CONFIDENCE CALIBRATION REPORT",
            "=" * 50,
            "",
        ]

        stats = self.get_stats()

        for s in stats:
            lines.append(f"**{s.category.value}**")
            lines.append(f"  Predictions: {s.total_predictions}")
            lines.append(f"  Accuracy: {s.accuracy:.0%}")
            lines.append(f"  Threshold: {s.current_threshold:.2f}")
            if abs(s.current_threshold - s.recommended_threshold) > 0.05:
                lines.append(f"  Recommended: {s.recommended_threshold:.2f}")
            lines.append("")

        lines.append("=" * 50)
        return "\n".join(lines)

    def reset(self) -> None:
        """Reset calibrator to defaults."""
        self.history.clear()
        self.thresholds = dict(self.DEFAULT_THRESHOLDS)
        self._last_calibration = 0


# Singleton instance
_calibrator: Optional[ConfidenceCalibrator] = None


def get_calibrator() -> ConfidenceCalibrator:
    """Get or create the global calibrator instance."""
    global _calibrator
    if _calibrator is None:
        _calibrator = ConfidenceCalibrator()
    return _calibrator


def record_prediction_outcome(
    category: str,
    confidence: float,
    was_correct: bool,
) -> None:
    """Convenience function to record prediction outcome."""
    try:
        cat = PredictionCategory(category)
    except ValueError:
        cat = PredictionCategory.ROUTING  # Default

    get_calibrator().record_outcome(cat, confidence, was_correct)


def get_threshold(category: str) -> float:
    """Convenience function to get threshold."""
    try:
        cat = PredictionCategory(category)
    except ValueError:
        return 0.7

    return get_calibrator().get_threshold(cat)
