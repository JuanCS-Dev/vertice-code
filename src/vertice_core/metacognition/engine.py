"""
Reflection Engine

Core reflection engine for metacognitive processing.

Reference:
- Microsoft Metacognition Research (2025)
- Reflexion (Shinn et al., 2023)
"""

from __future__ import annotations

import uuid
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from .types import (
    ReflectionLevel,
    ReflectionOutcome,
    ReasoningStep,
    ReflectionResult,
)
from .calibrator import ConfidenceCalibrator

logger = logging.getLogger(__name__)


class ReflectionEngine:
    """
    Core reflection engine for metacognitive processing.

    Provides:
    - Step-by-step reasoning evaluation
    - Confidence scoring with calibration
    - Outcome prediction
    - Strategy recommendation
    """

    def __init__(self) -> None:
        self._reasoning_chain: List[ReasoningStep] = []
        self._reflection_history: List[ReflectionResult] = []
        self._calibrator = ConfidenceCalibrator()

    def add_reasoning_step(
        self,
        description: str,
        input_state: Dict[str, Any],
        output_state: Dict[str, Any],
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReasoningStep:
        """Add a reasoning step to the chain."""
        step = ReasoningStep(
            id=str(uuid.uuid4()),
            description=description,
            input_state=input_state,
            output_state=output_state,
            confidence=self._calibrator.calibrate(confidence),
            metadata=metadata or {},
        )
        self._reasoning_chain.append(step)
        logger.debug(f"[Reflection] Added step: {description[:50]}...")
        return step

    def reflect_on_chain(self) -> ReflectionResult:
        """
        Perform cognitive-level reflection on the reasoning chain.

        Evaluates the coherence and confidence of the current approach.
        """
        if not self._reasoning_chain:
            return ReflectionResult(
                id=str(uuid.uuid4()),
                level=ReflectionLevel.COGNITIVE,
                outcome=ReflectionOutcome.PROCEED,
                confidence=0.5,
                reasoning="No reasoning chain to evaluate",
                suggestions=[],
            )

        # Calculate aggregate confidence
        confidences = [s.confidence for s in self._reasoning_chain]
        avg_confidence = sum(confidences) / len(confidences)
        min_confidence = min(confidences)

        # Check for confidence drops (potential issues)
        confidence_drops = []
        for i in range(1, len(confidences)):
            if confidences[i] < confidences[i - 1] * 0.7:  # 30%+ drop
                confidence_drops.append(i)

        # Determine outcome
        suggestions: List[str] = []
        if min_confidence < 0.3:
            outcome = ReflectionOutcome.RECONSIDER
            suggestions.append(
                f"Low confidence step detected at position {confidences.index(min_confidence)}"
            )
        elif confidence_drops:
            outcome = ReflectionOutcome.ADJUST
            suggestions.append(f"Confidence dropped significantly at steps: {confidence_drops}")
        elif avg_confidence < 0.5:
            outcome = ReflectionOutcome.ADJUST
            suggestions.append("Overall confidence is below threshold")
        else:
            outcome = ReflectionOutcome.PROCEED

        result = ReflectionResult(
            id=str(uuid.uuid4()),
            level=ReflectionLevel.COGNITIVE,
            outcome=outcome,
            confidence=avg_confidence,
            reasoning=f"Evaluated {len(self._reasoning_chain)} steps. "
            f"Avg confidence: {avg_confidence:.2f}, Min: {min_confidence:.2f}",
            suggestions=suggestions,
        )

        self._reflection_history.append(result)
        logger.info(f"[Reflection] Chain evaluation: {outcome.value} (conf: {avg_confidence:.2f})")

        return result

    def evaluate_decision(
        self,
        decision: str,
        alternatives: List[str],
        context: Dict[str, Any],
    ) -> Tuple[ReflectionOutcome, float, str]:
        """
        Evaluate a decision against alternatives.

        Returns:
            Tuple of (outcome, confidence, reasoning)
        """
        context_complexity = len(json.dumps(context))
        num_alternatives = len(alternatives)

        # Base confidence decreases with complexity and alternatives
        base_confidence = 0.8
        complexity_penalty = min(0.3, context_complexity / 10000)
        alternatives_penalty = min(0.2, num_alternatives * 0.05)

        confidence = max(0.2, base_confidence - complexity_penalty - alternatives_penalty)
        confidence = self._calibrator.calibrate(confidence)

        if confidence > 0.7:
            outcome = ReflectionOutcome.PROCEED
            reasoning = f"Decision '{decision}' appears sound given context"
        elif confidence > 0.4:
            outcome = ReflectionOutcome.ADJUST
            reasoning = f"Decision '{decision}' may need refinement. Consider: {alternatives[:2]}"
        else:
            outcome = ReflectionOutcome.RECONSIDER
            reasoning = (
                f"Decision '{decision}' has low confidence. " f"Review alternatives: {alternatives}"
            )

        return outcome, confidence, reasoning

    def predict_outcome(
        self,
        action: str,
        expected_effect: str,
        risk_factors: List[str],
    ) -> Dict[str, Any]:
        """
        Predict the outcome of an action.

        Returns prediction with confidence and risk assessment.
        """
        # Risk-adjusted confidence
        base_confidence = 0.75
        risk_penalty = len(risk_factors) * 0.1
        confidence = max(0.2, base_confidence - risk_penalty)
        confidence = self._calibrator.calibrate(confidence)

        risk_level = "high" if len(risk_factors) > 2 else "moderate" if risk_factors else "low"
        recommendation = (
            "proceed"
            if confidence > 0.6
            else "proceed_with_caution" if confidence > 0.4 else "reconsider"
        )

        return {
            "action": action,
            "expected_effect": expected_effect,
            "success_probability": confidence,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendation": recommendation,
        }

    def clear_chain(self) -> None:
        """Clear the current reasoning chain."""
        self._reasoning_chain = []

    def get_chain_summary(self) -> Dict[str, Any]:
        """Get summary of the reasoning chain."""
        if not self._reasoning_chain:
            return {"steps": 0, "avg_confidence": 0, "status": "empty"}

        confidences = [s.confidence for s in self._reasoning_chain]
        return {
            "steps": len(self._reasoning_chain),
            "avg_confidence": sum(confidences) / len(confidences),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "status": "active",
        }
