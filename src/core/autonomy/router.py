"""
Confidence-Based Router

Routes decisions based on confidence and risk levels.

References:
- arXiv:2402.16906 (Confidence-Based Routing)
- arXiv:2307.15042 (Staged Autonomy)
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from .types import (
    AutonomyLevel,
    AutonomyDecision,
    ConfidenceScore,
    UncertaintyEstimate,
    AutonomyConfig,
    EscalationReason,
)

logger = logging.getLogger(__name__)


class ConfidenceRouter:
    """
    Routes agent decisions based on confidence and risk.

    Implements Confidence-Based Routing (CBR):
    1. Estimate confidence for action
    2. Assess risk level
    3. Route to appropriate autonomy level
    4. Generate escalation if needed

    References:
    - arXiv:2402.16906: CBR for LLM routing
    - Staged autonomy progression
    """

    # Risk patterns for common actions
    HIGH_RISK_PATTERNS = [
        r"delete.*(?:file|data|database|record)",
        r"rm\s+-rf",
        r"drop\s+(?:table|database)",
        r"execute.*(?:command|shell|script)",
        r"modify.*(?:permission|credential|secret)",
        r"send.*(?:email|message|notification).*(?:all|everyone)",
        r"deploy.*production",
        r"push.*(?:main|master)",
    ]

    MEDIUM_RISK_PATTERNS = [
        r"write.*file",
        r"update.*(?:config|setting)",
        r"install.*(?:package|dependency)",
        r"create.*(?:user|account)",
        r"modify.*(?:code|source)",
    ]

    def __init__(self, config: Optional[AutonomyConfig] = None):
        """
        Initialize confidence router.

        Args:
            config: Autonomy configuration
        """
        self._config = config or AutonomyConfig()
        self._routing_history: List[AutonomyDecision] = []

        # Compile risk patterns
        self._high_risk_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in self.HIGH_RISK_PATTERNS
        ]
        self._medium_risk_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in self.MEDIUM_RISK_PATTERNS
        ]

    def route(
        self,
        action: str,
        confidence: ConfidenceScore,
        uncertainty: UncertaintyEstimate,
        context: Optional[Dict[str, Any]] = None,
    ) -> AutonomyDecision:
        """
        Route a decision based on confidence and risk.

        Args:
            action: The proposed action
            confidence: Confidence score for the action
            uncertainty: Uncertainty estimate
            context: Additional context

        Returns:
            AutonomyDecision with routing result
        """
        decision = AutonomyDecision(
            action=action,
            context=context or {},
            confidence=confidence,
            uncertainty=uncertainty,
        )

        # 1. Check for blocked actions
        if self._is_blocked(action):
            decision.autonomy_level = AutonomyLevel.ASSIST
            decision.can_proceed = False
            decision.reasoning = "Action is blocked by policy"
            decision.risk_factors.append("blocked_action")
            self._routing_history.append(decision)
            return decision

        # 2. Assess risk level
        decision.risk_level = self._assess_risk(action, context)
        decision.risk_factors = self._get_risk_factors(action)

        # 3. Check for always-escalate patterns
        if self._should_always_escalate(action):
            decision.autonomy_level = AutonomyLevel.APPROVE
            decision.can_proceed = False
            decision.reasoning = "Action matches always-escalate pattern"
            self._routing_history.append(decision)
            return decision

        # 4. Apply confidence-based routing
        cal_confidence = confidence.calibrated_confidence

        # High confidence + low risk = can act autonomously
        if (
            cal_confidence >= self._config.high_confidence_threshold and
            decision.risk_level < self._config.high_risk_threshold
        ):
            decision.autonomy_level = AutonomyLevel.NOTIFY
            decision.can_proceed = True
            decision.reasoning = (
                f"High confidence ({cal_confidence:.2f}) and low risk ({decision.risk_level:.2f})"
            )

        # Medium confidence = notify human
        elif cal_confidence >= self._config.medium_confidence_threshold:
            decision.autonomy_level = AutonomyLevel.NOTIFY
            decision.can_proceed = True
            decision.reasoning = (
                f"Medium confidence ({cal_confidence:.2f}), proceeding with notification"
            )

        # Low confidence or high risk = require approval
        elif cal_confidence >= self._config.low_confidence_threshold:
            decision.autonomy_level = AutonomyLevel.APPROVE
            decision.can_proceed = False
            decision.reasoning = (
                f"Low confidence ({cal_confidence:.2f}), approval required"
            )

        # Very low confidence = assist mode only
        else:
            decision.autonomy_level = AutonomyLevel.ASSIST
            decision.can_proceed = False
            decision.reasoning = (
                f"Very low confidence ({cal_confidence:.2f}), human decision required"
            )

        # 5. Override for high risk
        if decision.risk_level >= self._config.high_risk_threshold:
            if self._config.block_high_risk:
                decision.can_proceed = False
                decision.autonomy_level = AutonomyLevel.APPROVE
                decision.reasoning += f" [HIGH RISK: {decision.risk_level:.2f}]"
            else:
                decision.autonomy_level = AutonomyLevel.APPROVE

        # 6. Override for high uncertainty
        if uncertainty.should_escalate():
            decision.can_proceed = False
            decision.autonomy_level = AutonomyLevel.APPROVE
            decision.reasoning += f" [HIGH UNCERTAINTY: {uncertainty.total_uncertainty:.2f}]"

        logger.debug(
            f"[Router] Action '{action[:50]}...' routed to {decision.autonomy_level.value}, "
            f"can_proceed={decision.can_proceed}"
        )

        self._routing_history.append(decision)
        return decision

    def _is_blocked(self, action: str) -> bool:
        """Check if action is in blocked list."""
        action_lower = action.lower()
        for blocked in self._config.blocked_actions:
            if blocked.lower() in action_lower:
                return True
        return False

    def _should_always_escalate(self, action: str) -> bool:
        """Check if action matches always-escalate patterns."""
        action_lower = action.lower()
        for pattern in self._config.always_escalate_patterns:
            if pattern.lower() in action_lower:
                return True
        return False

    def _assess_risk(
        self,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Assess risk level of an action.

        Returns:
            Risk level from 0.0 (safe) to 1.0 (dangerous)
        """
        risk = 0.1  # Base risk

        # Check high-risk patterns
        for pattern in self._high_risk_patterns:
            if pattern.search(action):
                risk = max(risk, 0.8)
                break

        # Check medium-risk patterns
        for pattern in self._medium_risk_patterns:
            if pattern.search(action):
                risk = max(risk, 0.5)
                break

        # Context-based risk adjustment
        if context:
            # Production environment increases risk
            if context.get("environment") == "production":
                risk *= 1.3

            # User-specified high risk
            if context.get("high_risk"):
                risk = max(risk, 0.7)

        return min(1.0, risk)

    def _get_risk_factors(self, action: str) -> List[str]:
        """Get list of risk factors for an action."""
        factors = []

        for pattern in self._high_risk_patterns:
            if pattern.search(action):
                factors.append("high_risk_pattern")
                break

        for pattern in self._medium_risk_patterns:
            if pattern.search(action):
                factors.append("medium_risk_pattern")
                break

        # Common risk indicators
        if "production" in action.lower():
            factors.append("production_environment")
        if "delete" in action.lower() or "remove" in action.lower():
            factors.append("destructive_operation")
        if "secret" in action.lower() or "credential" in action.lower():
            factors.append("sensitive_data")

        return factors

    def get_escalation_reason(self, decision: AutonomyDecision) -> EscalationReason:
        """Determine escalation reason from decision."""
        if decision.risk_level >= self._config.high_risk_threshold:
            return EscalationReason.HIGH_RISK

        if decision.confidence.calibrated_confidence < self._config.low_confidence_threshold:
            return EscalationReason.LOW_CONFIDENCE

        if decision.uncertainty.total_uncertainty > 0.5:
            return EscalationReason.AMBIGUOUS_INPUT

        if "blocked" in decision.reasoning.lower():
            return EscalationReason.POLICY_VIOLATION

        return EscalationReason.USER_PREFERENCE

    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        if not self._routing_history:
            return {"total_decisions": 0}

        total = len(self._routing_history)
        approved = sum(1 for d in self._routing_history if d.can_proceed)
        by_level = {}
        for d in self._routing_history:
            level = d.autonomy_level.value
            by_level[level] = by_level.get(level, 0) + 1

        avg_risk = sum(d.risk_level for d in self._routing_history) / total
        avg_confidence = sum(d.confidence.calibrated_confidence for d in self._routing_history) / total

        return {
            "total_decisions": total,
            "approved_count": approved,
            "approval_rate": approved / total,
            "by_autonomy_level": by_level,
            "avg_risk_level": avg_risk,
            "avg_confidence": avg_confidence,
        }
