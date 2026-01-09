"""
Uncertainty Estimator

Estimates uncertainty in AI agent decisions.

References:
- arXiv:2503.15850 (Uncertainty Quantification in AI Agents)
- arXiv:2207.05221 (Predictive Uncertainty in Deep Learning)
- arXiv:2305.19187 (Conformal Prediction for LLMs)
- BALD (Bayesian Active Learning by Disagreement)
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional

from .types import UncertaintyEstimate

logger = logging.getLogger(__name__)


class UncertaintyEstimator:
    """
    Estimates uncertainty in agent decisions.

    Implements multiple uncertainty estimation methods:
    - Softmax entropy (predictive uncertainty)
    - BALD/mutual information (epistemic uncertainty)
    - Ensemble disagreement
    - Verbalized confidence

    References:
    - arXiv:2503.15850: Taxonomy of input/reasoning/parameter/prediction uncertainty
    - BALD: Mutual information for epistemic uncertainty
    """

    def __init__(
        self,
        calibrator: Optional[Any] = None,  # ConfidenceCalibrator
        ensemble_size: int = 5,
    ):
        """
        Initialize uncertainty estimator.

        Args:
            calibrator: Optional confidence calibrator
            ensemble_size: Number of samples for ensemble methods
        """
        self._calibrator = calibrator
        self._ensemble_size = ensemble_size

        # History for learning
        self._estimation_history: List[UncertaintyEstimate] = []

    def estimate(
        self,
        logits: Optional[List[float]] = None,
        verbalized_confidence: Optional[float] = None,
        input_text: Optional[str] = None,
        output_text: Optional[str] = None,
        samples: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> UncertaintyEstimate:
        """
        Estimate uncertainty from multiple sources.

        Args:
            logits: Model output logits (if available)
            verbalized_confidence: Model's stated confidence
            input_text: Input query
            output_text: Model output
            samples: Multiple samples from the model
            context: Additional context

        Returns:
            Comprehensive uncertainty estimate
        """
        estimate = UncertaintyEstimate()

        # 1. Input uncertainty (ambiguity in query)
        if input_text:
            estimate.input_uncertainty = self._estimate_input_uncertainty(input_text)

        # 2. Prediction uncertainty from logits
        if logits:
            entropy, variance = self._estimate_from_logits(logits)
            estimate.entropy = entropy
            estimate.variance = variance
            estimate.prediction_uncertainty = entropy

        # 3. Epistemic uncertainty from samples (BALD-style)
        if samples and len(samples) >= 2:
            mi, agreement = self._estimate_from_samples(samples)
            estimate.mutual_information = mi
            estimate.sample_agreement = agreement
            estimate.sample_count = len(samples)
            estimate.parameter_uncertainty = 1.0 - agreement

        # 4. Verbalized confidence
        raw_confidence = verbalized_confidence or 0.5
        estimate.confidence.raw_confidence = raw_confidence

        # 5. Calibrate confidence
        if self._calibrator:
            estimate.confidence.calibrated_confidence = self._calibrator.calibrate(raw_confidence)
        else:
            estimate.confidence.calibrated_confidence = raw_confidence

        # 6. Reasoning uncertainty (based on output analysis)
        if output_text:
            estimate.reasoning_uncertainty = self._estimate_reasoning_uncertainty(output_text)

        # 7. Decompose into epistemic/aleatoric
        self._decompose_uncertainty(estimate)

        # 8. Compute total uncertainty
        estimate.total_uncertainty = self._compute_total_uncertainty(estimate)

        # 9. Update confidence scores
        estimate.confidence.input_confidence = 1.0 - estimate.input_uncertainty
        estimate.confidence.reasoning_confidence = 1.0 - estimate.reasoning_uncertainty
        estimate.confidence.output_confidence = 1.0 - estimate.prediction_uncertainty
        estimate.confidence.epistemic = estimate.parameter_uncertainty
        estimate.confidence.aleatoric = estimate.prediction_uncertainty

        self._estimation_history.append(estimate)

        logger.debug(
            f"[Uncertainty] Estimated: total={estimate.total_uncertainty:.3f}, "
            f"epistemic={estimate.parameter_uncertainty:.3f}, "
            f"aleatoric={estimate.prediction_uncertainty:.3f}"
        )

        return estimate

    def estimate_from_verbalized(
        self,
        verbalized_confidence: float,
        hedging_phrases: Optional[List[str]] = None,
    ) -> UncertaintyEstimate:
        """
        Estimate uncertainty from verbalized confidence.

        Args:
            verbalized_confidence: Model's stated confidence (0-1)
            hedging_phrases: Detected hedging phrases in output

        Returns:
            Uncertainty estimate
        """
        estimate = UncertaintyEstimate()

        # Penalize for hedging phrases
        hedging_penalty = 0.0
        if hedging_phrases:
            hedging_penalty = min(0.3, len(hedging_phrases) * 0.05)

        adjusted_confidence = max(0.0, verbalized_confidence - hedging_penalty)

        estimate.confidence.raw_confidence = verbalized_confidence
        estimate.confidence.calibrated_confidence = adjusted_confidence
        estimate.total_uncertainty = 1.0 - adjusted_confidence

        return estimate

    def _estimate_input_uncertainty(self, input_text: str) -> float:
        """
        Estimate uncertainty from input ambiguity.

        Heuristics:
        - Question marks suggest clarification needed
        - Short inputs may be ambiguous
        - Certain keywords indicate ambiguity
        """
        uncertainty = 0.2  # Base uncertainty

        # Very short inputs are often ambiguous
        if len(input_text) < 20:
            uncertainty += 0.1

        # Multiple questions suggest complexity
        question_count = input_text.count("?")
        if question_count > 1:
            uncertainty += 0.05 * min(3, question_count)

        # Ambiguous phrases
        ambiguous_phrases = [
            "maybe", "perhaps", "possibly", "not sure", "unclear",
            "it depends", "or", "alternatively", "either",
        ]
        for phrase in ambiguous_phrases:
            if phrase in input_text.lower():
                uncertainty += 0.05

        return min(1.0, uncertainty)

    def _estimate_reasoning_uncertainty(self, output_text: str) -> float:
        """
        Estimate uncertainty in reasoning process.

        Detects hedging language and uncertainty markers.
        """
        uncertainty = 0.1  # Base uncertainty

        # Hedging phrases indicate uncertainty
        hedging_phrases = [
            "i think", "probably", "might", "could be", "possibly",
            "i'm not sure", "i believe", "it seems", "may be",
            "uncertain", "unclear", "depends on",
        ]

        for phrase in hedging_phrases:
            if phrase in output_text.lower():
                uncertainty += 0.08

        # Contradiction markers
        contradiction_phrases = ["however", "but", "although", "on the other hand"]
        for phrase in contradiction_phrases:
            if phrase in output_text.lower():
                uncertainty += 0.03

        return min(1.0, uncertainty)

    def _estimate_from_logits(
        self,
        logits: List[float],
    ) -> tuple[float, float]:
        """
        Estimate uncertainty from output logits.

        Returns:
            Tuple of (entropy, variance)
        """
        if not logits:
            return 0.5, 0.5

        # Convert to probabilities with softmax
        max_logit = max(logits)
        exp_logits = [math.exp(l - max_logit) for l in logits]
        sum_exp = sum(exp_logits)
        probs = [e / sum_exp for e in exp_logits]

        # Calculate entropy
        entropy = 0.0
        for p in probs:
            if p > 0:
                entropy -= p * math.log(p)

        # Normalize entropy
        max_entropy = math.log(len(probs)) if len(probs) > 1 else 1.0
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

        # Calculate variance
        mean_prob = sum(probs) / len(probs)
        variance = sum((p - mean_prob) ** 2 for p in probs) / len(probs)

        return normalized_entropy, variance

    def _estimate_from_samples(
        self,
        samples: List[str],
    ) -> tuple[float, float]:
        """
        Estimate uncertainty from multiple model samples (BALD-style).

        Returns:
            Tuple of (mutual_information, agreement)
        """
        if len(samples) < 2:
            return 0.0, 1.0

        # Simple agreement metric: how similar are the samples?
        unique_samples = set(samples)
        agreement = 1.0 - (len(unique_samples) - 1) / len(samples)

        # Mutual information approximation
        # Higher disagreement = higher epistemic uncertainty
        mi = 1.0 - agreement

        return mi, agreement

    def _decompose_uncertainty(self, estimate: UncertaintyEstimate) -> None:
        """
        Decompose total uncertainty into epistemic and aleatoric components.

        Based on BALD decomposition:
        - Epistemic (model uncertainty): mutual_information
        - Aleatoric (data uncertainty): entropy - mutual_information
        """
        if estimate.mutual_information > 0:
            # BALD decomposition
            estimate.parameter_uncertainty = estimate.mutual_information
            estimate.prediction_uncertainty = max(
                0.0,
                estimate.entropy - estimate.mutual_information
            )
        else:
            # Use entropy as aleatoric, sample disagreement as epistemic
            estimate.prediction_uncertainty = estimate.entropy
            estimate.parameter_uncertainty = 1.0 - estimate.sample_agreement

    def _compute_total_uncertainty(self, estimate: UncertaintyEstimate) -> float:
        """
        Compute total uncertainty from components.

        Weighted combination of uncertainty sources.
        """
        weights = {
            "input": 0.2,
            "reasoning": 0.3,
            "parameter": 0.25,  # Epistemic
            "prediction": 0.25,  # Aleatoric
        }

        total = (
            weights["input"] * estimate.input_uncertainty +
            weights["reasoning"] * estimate.reasoning_uncertainty +
            weights["parameter"] * estimate.parameter_uncertainty +
            weights["prediction"] * estimate.prediction_uncertainty
        )

        return min(1.0, total)

    def get_stats(self) -> Dict[str, Any]:
        """Get uncertainty estimation statistics."""
        if not self._estimation_history:
            return {"total_estimates": 0}

        avg_uncertainty = sum(e.total_uncertainty for e in self._estimation_history) / len(self._estimation_history)
        avg_epistemic = sum(e.parameter_uncertainty for e in self._estimation_history) / len(self._estimation_history)
        avg_aleatoric = sum(e.prediction_uncertainty for e in self._estimation_history) / len(self._estimation_history)

        return {
            "total_estimates": len(self._estimation_history),
            "avg_total_uncertainty": avg_uncertainty,
            "avg_epistemic_uncertainty": avg_epistemic,
            "avg_aleatoric_uncertainty": avg_aleatoric,
        }
