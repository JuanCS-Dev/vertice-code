"""
Confidence Calibrator

Calibrate confidence scores for accurate uncertainty estimation.

Reference:
- Microsoft Metacognition Research (2025)
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .types import ConfidenceLevel


class ConfidenceCalibrator:
    """
    Calibrate confidence scores for accurate uncertainty estimation.

    Based on research showing AI agents often over/under-estimate confidence.
    Uses historical accuracy to adjust raw confidence scores.
    """

    def __init__(self) -> None:
        self._calibration_history: List[Tuple[float, bool]] = []
        self._bucket_accuracy: Dict[str, Dict[str, float]] = {
            level.value: {"predicted": 0.0, "actual": 0.0, "count": 0} for level in ConfidenceLevel
        }

    def calibrate(self, raw_confidence: float) -> float:
        """
        Calibrate a raw confidence score.

        Args:
            raw_confidence: Raw confidence (0-1)

        Returns:
            Calibrated confidence (0-1)
        """
        if not self._calibration_history:
            return raw_confidence

        # Calculate historical calibration factor
        bucket = self._get_bucket(raw_confidence)
        bucket_data = self._bucket_accuracy[bucket.value]

        if bucket_data["count"] < 5:
            # Not enough data, return raw
            return raw_confidence

        # Adjust based on historical accuracy in this bucket
        historical_accuracy = bucket_data["actual"] / bucket_data["count"]
        avg_predicted = bucket_data["predicted"] / bucket_data["count"]

        if avg_predicted > 0:
            calibration_factor = historical_accuracy / avg_predicted
            calibrated = raw_confidence * calibration_factor
            return max(0.0, min(1.0, calibrated))

        return raw_confidence

    def record_outcome(self, confidence: float, was_correct: bool) -> None:
        """Record an outcome for future calibration."""
        self._calibration_history.append((confidence, was_correct))

        bucket = self._get_bucket(confidence)
        self._bucket_accuracy[bucket.value]["predicted"] += confidence
        self._bucket_accuracy[bucket.value]["actual"] += 1.0 if was_correct else 0.0
        self._bucket_accuracy[bucket.value]["count"] += 1

        # Keep history bounded
        if len(self._calibration_history) > 1000:
            self._calibration_history = self._calibration_history[-500:]

    def _get_bucket(self, confidence: float) -> ConfidenceLevel:
        """Get confidence bucket for a value."""
        if confidence < 0.2:
            return ConfidenceLevel.VERY_LOW
        elif confidence < 0.4:
            return ConfidenceLevel.LOW
        elif confidence < 0.6:
            return ConfidenceLevel.MODERATE
        elif confidence < 0.8:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.VERY_HIGH

    def get_calibration_stats(self) -> Dict[str, Any]:
        """Get calibration statistics."""
        return {
            "history_size": len(self._calibration_history),
            "buckets": {
                level: {
                    "count": data["count"],
                    "avg_predicted": (
                        data["predicted"] / data["count"] if data["count"] > 0 else 0
                    ),
                    "accuracy": (data["actual"] / data["count"] if data["count"] > 0 else 0),
                }
                for level, data in self._bucket_accuracy.items()
            },
        }
