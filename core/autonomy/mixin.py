"""
Autonomy Mixin

Mixin providing bounded autonomy capabilities to agents.

References:
- arXiv:2503.15850 (Uncertainty Quantification)
- arXiv:2402.16906 (Confidence-Based Routing)
- arXiv:2307.15042 (Staged Autonomy)
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from .types import (
    AutonomyLevel,
    AutonomyDecision,
    ConfidenceScore,
    UncertaintyEstimate,
    EscalationRequest,
    AutonomyConfig,
)
from .uncertainty import UncertaintyEstimator
from .router import ConfidenceRouter
from .escalation import EscalationManager
from .calibrator import ConfidenceCalibrator

logger = logging.getLogger(__name__)


class AutonomyMixin:
    """
    Mixin providing bounded autonomy with uncertainty quantification.

    Adds:
    - Uncertainty estimation for decisions
    - Confidence-based routing
    - Human-in-the-loop escalation
    - Calibrated confidence scores

    Implements staged autonomy progression:
    ASSIST → APPROVE → NOTIFY → LEARN
    """

    def _init_autonomy(
        self,
        config: Optional[AutonomyConfig] = None,
        on_escalation: Optional[Callable[[EscalationRequest], None]] = None,
    ) -> None:
        """
        Initialize autonomy system.

        Args:
            config: Autonomy configuration
            on_escalation: Callback for escalation events
        """
        self._autonomy_config = config or AutonomyConfig()
        self._calibrator = ConfidenceCalibrator(
            method=self._autonomy_config.calibration_method
        )
        self._uncertainty_estimator = UncertaintyEstimator(
            calibrator=self._calibrator,
            ensemble_size=self._autonomy_config.ensemble_size,
        )
        self._router = ConfidenceRouter(self._autonomy_config)
        self._escalation_manager = EscalationManager(
            config=self._autonomy_config,
            on_escalation=on_escalation,
        )

        # Current autonomy level (can be upgraded over time)
        self._current_autonomy_level = self._autonomy_config.default_level
        self._autonomy_initialized = True

        logger.info(
            f"[Autonomy] Initialized with level={self._current_autonomy_level.value}, "
            f"calibration={self._autonomy_config.calibration_method}"
        )

    def estimate_uncertainty(
        self,
        verbalized_confidence: Optional[float] = None,
        logits: Optional[List[float]] = None,
        input_text: Optional[str] = None,
        output_text: Optional[str] = None,
        samples: Optional[List[str]] = None,
    ) -> UncertaintyEstimate:
        """
        Estimate uncertainty for a decision.

        Args:
            verbalized_confidence: Model's stated confidence
            logits: Model output logits
            input_text: Input query
            output_text: Model output
            samples: Multiple samples for ensemble

        Returns:
            Comprehensive uncertainty estimate
        """
        if not hasattr(self, "_uncertainty_estimator"):
            self._init_autonomy()

        return self._uncertainty_estimator.estimate(
            logits=logits,
            verbalized_confidence=verbalized_confidence,
            input_text=input_text,
            output_text=output_text,
            samples=samples,
        )

    def check_autonomy(
        self,
        action: str,
        confidence: Optional[float] = None,
        uncertainty: Optional[UncertaintyEstimate] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AutonomyDecision:
        """
        Check if an action can be performed autonomously.

        Args:
            action: The proposed action
            confidence: Optional pre-computed confidence
            uncertainty: Optional pre-computed uncertainty
            context: Additional context

        Returns:
            AutonomyDecision with routing result
        """
        if not hasattr(self, "_router"):
            self._init_autonomy()

        # Get or compute uncertainty
        if uncertainty is None:
            uncertainty = self.estimate_uncertainty(
                verbalized_confidence=confidence,
                input_text=action,
            )

        # Build confidence score
        conf_score = ConfidenceScore(
            raw_confidence=confidence or 0.5,
            calibrated_confidence=self._calibrator.calibrate(confidence or 0.5),
        )

        # Route the decision
        decision = self._router.route(
            action=action,
            confidence=conf_score,
            uncertainty=uncertainty,
            context=context,
        )

        # Override based on current autonomy level
        decision = self._apply_autonomy_level(decision)

        logger.debug(
            f"[Autonomy] Action '{action[:50]}...' -> "
            f"level={decision.autonomy_level.value}, can_proceed={decision.can_proceed}"
        )

        return decision

    def _apply_autonomy_level(self, decision: AutonomyDecision) -> AutonomyDecision:
        """Apply current autonomy level constraints to decision."""
        level_order = [
            AutonomyLevel.ASSIST,
            AutonomyLevel.APPROVE,
            AutonomyLevel.NOTIFY,
            AutonomyLevel.LEARN,
        ]

        current_idx = level_order.index(self._current_autonomy_level)
        decision_idx = level_order.index(decision.autonomy_level)

        # Cannot exceed current autonomy level
        if decision_idx > current_idx:
            decision.autonomy_level = self._current_autonomy_level
            decision.reasoning += f" [capped to {self._current_autonomy_level.value}]"

            # Recalculate can_proceed based on capped level
            if self._current_autonomy_level == AutonomyLevel.ASSIST:
                decision.can_proceed = False
            elif self._current_autonomy_level == AutonomyLevel.APPROVE:
                decision.can_proceed = False

        return decision

    async def request_approval(
        self,
        action: str,
        decision: Optional[AutonomyDecision] = None,
        options: Optional[List[str]] = None,
        recommended: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Optional[str]:
        """
        Request human approval for an action.

        Args:
            action: The action requiring approval
            decision: Optional pre-computed decision
            options: Options to present to human
            recommended: Recommended option
            timeout: Timeout in seconds

        Returns:
            Human response or None if timeout
        """
        if not hasattr(self, "_escalation_manager"):
            self._init_autonomy()

        # Get decision if not provided
        if decision is None:
            decision = self.check_autonomy(action)

        # Determine escalation reason
        reason = self._router.get_escalation_reason(decision)

        # Create escalation
        request = self._escalation_manager.create_escalation(
            decision=decision,
            reason=reason,
            options=options,
            recommended=recommended,
        )

        # Wait for response
        response = await self._escalation_manager.wait_for_response(
            request.id,
            timeout=timeout,
        )

        # Learn from escalation outcome
        if self._autonomy_config.learn_from_escalations and response:
            self._learn_from_escalation(decision, response)

        return response

    def respond_to_escalation(
        self,
        request_id: str,
        response: str,
    ) -> bool:
        """
        Submit response to a pending escalation.

        Args:
            request_id: Escalation request ID
            response: Human response

        Returns:
            True if response accepted
        """
        if not hasattr(self, "_escalation_manager"):
            return False

        return self._escalation_manager.respond(request_id, response)

    def get_pending_escalations(self) -> List[EscalationRequest]:
        """Get all pending escalation requests."""
        if not hasattr(self, "_escalation_manager"):
            return []
        return self._escalation_manager.get_pending()

    def upgrade_autonomy(self, level: AutonomyLevel) -> bool:
        """
        Upgrade to a higher autonomy level.

        Args:
            level: New autonomy level

        Returns:
            True if upgrade successful
        """
        if not hasattr(self, "_current_autonomy_level"):
            self._init_autonomy()

        level_order = [
            AutonomyLevel.ASSIST,
            AutonomyLevel.APPROVE,
            AutonomyLevel.NOTIFY,
            AutonomyLevel.LEARN,
        ]

        current_idx = level_order.index(self._current_autonomy_level)
        new_idx = level_order.index(level)

        # Only allow upgrading one level at a time
        if new_idx > current_idx + 1:
            logger.warning(f"[Autonomy] Cannot skip levels: {self._current_autonomy_level} -> {level}")
            return False

        self._current_autonomy_level = level
        logger.info(f"[Autonomy] Upgraded to {level.value}")
        return True

    def downgrade_autonomy(self, level: AutonomyLevel) -> bool:
        """
        Downgrade to a lower autonomy level.

        Args:
            level: New autonomy level

        Returns:
            True if downgrade successful
        """
        if not hasattr(self, "_current_autonomy_level"):
            self._init_autonomy()

        self._current_autonomy_level = level
        logger.info(f"[Autonomy] Downgraded to {level.value}")
        return True

    def record_outcome(
        self,
        predicted_confidence: float,
        was_correct: bool,
    ) -> None:
        """
        Record outcome for calibration learning.

        Args:
            predicted_confidence: Model's predicted confidence
            was_correct: Whether prediction was correct
        """
        if hasattr(self, "_calibrator"):
            self._calibrator.add_calibration_point(predicted_confidence, was_correct)

    def _learn_from_escalation(
        self,
        decision: AutonomyDecision,
        response: str,
    ) -> None:
        """Learn from escalation outcomes to improve routing."""
        # Record for calibration
        was_correct = response == "approve"
        self._calibrator.add_calibration_point(
            decision.confidence.calibrated_confidence,
            was_correct,
        )

    def get_autonomy_status(self) -> Dict[str, Any]:
        """Get autonomy system status."""
        if not hasattr(self, "_autonomy_initialized"):
            return {"initialized": False}

        return {
            "initialized": True,
            "current_level": self._current_autonomy_level.value,
            "routing_stats": self._router.get_stats(),
            "escalation_stats": self._escalation_manager.get_stats(),
            "calibration_stats": self._calibrator.get_stats(),
            "uncertainty_stats": self._uncertainty_estimator.get_stats(),
        }

    def get_current_autonomy_level(self) -> AutonomyLevel:
        """Get current autonomy level."""
        if not hasattr(self, "_current_autonomy_level"):
            return AutonomyLevel.APPROVE
        return self._current_autonomy_level
