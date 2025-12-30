"""
Confidence Calibrator

Calibrates model confidence scores for better decision-making.

References:
- arXiv:2310.03046 (Calibration of LLM Confidence)
- arXiv:2207.07411 (Temperature Scaling)
- Platt Scaling (Platt, 1999)
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class ConfidenceCalibrator:
    """
    Calibrates model confidence scores.

    Implements multiple calibration methods:
    - Temperature scaling (single parameter)
    - Platt scaling (logistic regression)
    - Isotonic regression (non-parametric)

    References:
    - arXiv:2310.03046: LLM confidence is often miscalibrated
    - Temperature scaling is simple but effective
    """

    def __init__(
        self,
        method: str = "temperature_scaling",
        initial_temperature: float = 1.0,
    ):
        """
        Initialize calibrator.

        Args:
            method: Calibration method ("temperature_scaling", "platt", "isotonic")
            initial_temperature: Initial temperature for temperature scaling
        """
        self._method = method
        self._temperature = initial_temperature

        # Platt scaling parameters
        self._platt_a = 0.0
        self._platt_b = 0.0

        # Isotonic regression bins
        self._isotonic_bins: List[Tuple[float, float]] = []

        # Calibration data for learning
        self._calibration_data: List[Tuple[float, bool]] = []
        self._is_fitted = False

    def calibrate(self, raw_confidence: float) -> float:
        """
        Calibrate a raw confidence score.

        Args:
            raw_confidence: Model's raw confidence (0-1)

        Returns:
            Calibrated confidence (0-1)
        """
        if not self._is_fitted:
            # Use default calibration (slight temperature)
            return self._apply_temperature(raw_confidence, 1.2)

        if self._method == "temperature_scaling":
            return self._apply_temperature(raw_confidence, self._temperature)
        elif self._method == "platt":
            return self._apply_platt(raw_confidence)
        elif self._method == "isotonic":
            return self._apply_isotonic(raw_confidence)
        else:
            return raw_confidence

    def _apply_temperature(self, confidence: float, temperature: float) -> float:
        """Apply temperature scaling."""
        if temperature <= 0:
            return confidence

        # Convert confidence to logit, scale, convert back
        epsilon = 1e-7
        confidence = max(epsilon, min(1 - epsilon, confidence))

        logit = math.log(confidence / (1 - confidence))
        scaled_logit = logit / temperature

        calibrated = 1 / (1 + math.exp(-scaled_logit))
        return calibrated

    def _apply_platt(self, confidence: float) -> float:
        """Apply Platt scaling (logistic regression on logits)."""
        epsilon = 1e-7
        confidence = max(epsilon, min(1 - epsilon, confidence))

        logit = math.log(confidence / (1 - confidence))
        scaled_logit = self._platt_a * logit + self._platt_b

        calibrated = 1 / (1 + math.exp(-scaled_logit))
        return calibrated

    def _apply_isotonic(self, confidence: float) -> float:
        """Apply isotonic regression calibration."""
        if not self._isotonic_bins:
            return confidence

        # Find appropriate bin
        for lower, upper in self._isotonic_bins:
            if confidence <= upper:
                return lower  # Return calibrated value for bin

        return self._isotonic_bins[-1][0]

    def add_calibration_point(
        self,
        predicted_confidence: float,
        was_correct: bool,
    ) -> None:
        """
        Add a calibration data point for learning.

        Args:
            predicted_confidence: Model's predicted confidence
            was_correct: Whether the prediction was actually correct
        """
        self._calibration_data.append((predicted_confidence, was_correct))

        # Re-fit after accumulating enough data
        if len(self._calibration_data) >= 50:
            self._fit()

    def _fit(self) -> None:
        """Fit calibration parameters to accumulated data."""
        if len(self._calibration_data) < 20:
            return

        if self._method == "temperature_scaling":
            self._fit_temperature()
        elif self._method == "platt":
            self._fit_platt()
        elif self._method == "isotonic":
            self._fit_isotonic()

        self._is_fitted = True
        logger.info(f"[Calibrator] Fitted {self._method} on {len(self._calibration_data)} points")

    def _fit_temperature(self) -> None:
        """Fit optimal temperature via grid search."""
        best_temperature = 1.0
        best_ece = float('inf')

        for temp in [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]:
            ece = self._compute_ece(temp)
            if ece < best_ece:
                best_ece = ece
                best_temperature = temp

        self._temperature = best_temperature
        logger.debug(f"[Calibrator] Optimal temperature: {best_temperature}, ECE: {best_ece:.4f}")

    def _fit_platt(self) -> None:
        """Fit Platt scaling parameters."""
        # Simple fitting via grid search
        best_a, best_b = 1.0, 0.0
        best_ece = float('inf')

        for a in [0.5, 0.75, 1.0, 1.25, 1.5]:
            for b in [-1.0, -0.5, 0.0, 0.5, 1.0]:
                self._platt_a = a
                self._platt_b = b
                ece = self._compute_ece_platt()
                if ece < best_ece:
                    best_ece = ece
                    best_a, best_b = a, b

        self._platt_a = best_a
        self._platt_b = best_b

    def _fit_isotonic(self) -> None:
        """Fit isotonic regression."""
        # Sort by confidence
        sorted_data = sorted(self._calibration_data)

        # Create bins
        n_bins = 10
        bin_size = len(sorted_data) // n_bins

        self._isotonic_bins = []
        for i in range(n_bins):
            start = i * bin_size
            end = start + bin_size if i < n_bins - 1 else len(sorted_data)
            bin_data = sorted_data[start:end]

            if bin_data:
                # Average actual accuracy in bin
                accuracy = sum(1 for _, correct in bin_data if correct) / len(bin_data)
                upper_bound = bin_data[-1][0] if bin_data else 1.0
                self._isotonic_bins.append((accuracy, upper_bound))

    def _compute_ece(self, temperature: float) -> float:
        """Compute Expected Calibration Error for temperature scaling."""
        n_bins = 10
        bins = [[] for _ in range(n_bins)]

        for conf, correct in self._calibration_data:
            calibrated = self._apply_temperature(conf, temperature)
            bin_idx = min(int(calibrated * n_bins), n_bins - 1)
            bins[bin_idx].append((calibrated, correct))

        ece = 0.0
        total = len(self._calibration_data)

        for bin_data in bins:
            if not bin_data:
                continue

            bin_size = len(bin_data)
            avg_confidence = sum(c for c, _ in bin_data) / bin_size
            accuracy = sum(1 for _, correct in bin_data if correct) / bin_size

            ece += (bin_size / total) * abs(avg_confidence - accuracy)

        return ece

    def _compute_ece_platt(self) -> float:
        """Compute ECE for Platt scaling."""
        n_bins = 10
        bins = [[] for _ in range(n_bins)]

        for conf, correct in self._calibration_data:
            calibrated = self._apply_platt(conf)
            bin_idx = min(int(calibrated * n_bins), n_bins - 1)
            bins[bin_idx].append((calibrated, correct))

        ece = 0.0
        total = len(self._calibration_data)

        for bin_data in bins:
            if not bin_data:
                continue

            bin_size = len(bin_data)
            avg_confidence = sum(c for c, _ in bin_data) / bin_size
            accuracy = sum(1 for _, correct in bin_data if correct) / bin_size

            ece += (bin_size / total) * abs(avg_confidence - accuracy)

        return ece

    def get_stats(self) -> Dict[str, Any]:
        """Get calibration statistics."""
        if not self._calibration_data:
            return {"fitted": False, "data_points": 0}

        # Compute calibration metrics
        ece = self._compute_ece(self._temperature) if self._method == "temperature_scaling" else 0.0

        return {
            "fitted": self._is_fitted,
            "method": self._method,
            "data_points": len(self._calibration_data),
            "temperature": self._temperature if self._method == "temperature_scaling" else None,
            "platt_a": self._platt_a if self._method == "platt" else None,
            "platt_b": self._platt_b if self._method == "platt" else None,
            "ece": ece,
        }

    def reset(self) -> None:
        """Reset calibrator state."""
        self._calibration_data.clear()
        self._is_fitted = False
        self._temperature = 1.0
        self._platt_a = 0.0
        self._platt_b = 0.0
        self._isotonic_bins.clear()
