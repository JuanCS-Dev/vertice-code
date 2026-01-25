"""
Autonomy Types

Type definitions for bounded autonomy and uncertainty quantification.

References:
- arXiv:2503.15850 (Uncertainty Quantification in AI Agents)
- arXiv:2402.16906 (Confidence-Based Routing)
- arXiv:2310.03046 (LLM Confidence Calibration)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime
import uuid


class AutonomyLevel(str, Enum):
    """
    Staged autonomy levels (arXiv:2307.15042).

    Progressive trust model for AI agents:
    1. ASSIST: Human makes all decisions, agent provides information
    2. APPROVE: Agent proposes, human approves before action
    3. NOTIFY: Agent acts, notifies human of actions
    4. LEARN: Agent acts autonomously, learns from feedback
    """

    ASSIST = "assist"  # Agent assists, human decides
    APPROVE = "approve"  # Agent proposes, human approves
    NOTIFY = "notify"  # Agent acts, human notified
    LEARN = "learn"  # Full autonomy with learning


class UncertaintyType(str, Enum):
    """
    Types of uncertainty in AI agents (arXiv:2503.15850).

    Taxonomy:
    - Input: Ambiguity in the input/query
    - Reasoning: Uncertainty in the reasoning process
    - Parameter: Model weight uncertainty (epistemic)
    - Prediction: Output uncertainty (aleatoric)
    """

    INPUT = "input"  # Query ambiguity
    REASONING = "reasoning"  # Process uncertainty
    PARAMETER = "parameter"  # Model uncertainty (epistemic)
    PREDICTION = "prediction"  # Output uncertainty (aleatoric)


class EscalationReason(str, Enum):
    """Reasons for escalating to human oversight."""

    LOW_CONFIDENCE = "low_confidence"
    HIGH_RISK = "high_risk"
    POLICY_VIOLATION = "policy_violation"
    USER_PREFERENCE = "user_preference"
    AMBIGUOUS_INPUT = "ambiguous_input"
    NOVEL_SITUATION = "novel_situation"
    SAFETY_CONCERN = "safety_concern"


@dataclass
class ConfidenceScore:
    """
    Confidence score with calibration.

    Includes raw model confidence and calibrated probability.
    """

    raw_confidence: float = 0.5  # Model's stated confidence
    calibrated_confidence: float = 0.5  # Post-calibration confidence
    calibration_method: str = "platt"  # Calibration method used

    # Per-dimension confidence
    input_confidence: float = 0.5  # Confidence in understanding input
    reasoning_confidence: float = 0.5  # Confidence in reasoning process
    output_confidence: float = 0.5  # Confidence in output correctness

    # Uncertainty decomposition
    epistemic: float = 0.5  # Model uncertainty (reducible)
    aleatoric: float = 0.5  # Data uncertainty (irreducible)

    def overall(self) -> float:
        """Get overall calibrated confidence."""
        return self.calibrated_confidence

    def is_uncertain(self, threshold: float = 0.7) -> bool:
        """Check if confidence is below threshold."""
        return self.calibrated_confidence < threshold


@dataclass
class UncertaintyEstimate:
    """
    Comprehensive uncertainty estimate for a decision.

    Based on arXiv:2503.15850 taxonomy.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Overall uncertainty
    total_uncertainty: float = 0.5
    confidence: ConfidenceScore = field(default_factory=ConfidenceScore)

    # Decomposed uncertainty by type
    input_uncertainty: float = 0.0  # Ambiguity in query
    reasoning_uncertainty: float = 0.0  # Process uncertainty
    parameter_uncertainty: float = 0.0  # Model uncertainty
    prediction_uncertainty: float = 0.0  # Output uncertainty

    # Evidence
    entropy: float = 0.0  # Predictive entropy
    mutual_information: float = 0.0  # Epistemic uncertainty (BALD)
    variance: float = 0.0  # Prediction variance

    # Samples if using ensemble/sampling
    sample_count: int = 1
    sample_agreement: float = 1.0  # Agreement among samples

    def should_escalate(self, threshold: float = 0.5) -> bool:
        """Determine if uncertainty warrants escalation."""
        return self.total_uncertainty > threshold or self.confidence.is_uncertain()


@dataclass
class AutonomyDecision:
    """
    Decision about autonomy level for a specific action.

    Determines whether agent can act autonomously or needs human input.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    action: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

    # Decision
    autonomy_level: AutonomyLevel = AutonomyLevel.APPROVE
    can_proceed: bool = False

    # Confidence and uncertainty
    confidence: ConfidenceScore = field(default_factory=ConfidenceScore)
    uncertainty: UncertaintyEstimate = field(default_factory=UncertaintyEstimate)

    # Risk assessment
    risk_level: float = 0.0  # 0.0 = safe, 1.0 = high risk
    risk_factors: List[str] = field(default_factory=list)

    # Reasoning
    reasoning: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "action": self.action,
            "autonomy_level": self.autonomy_level.value,
            "can_proceed": self.can_proceed,
            "confidence": self.confidence.calibrated_confidence,
            "uncertainty": self.uncertainty.total_uncertainty,
            "risk_level": self.risk_level,
            "reasoning": self.reasoning,
        }


@dataclass
class EscalationRequest:
    """
    Request for human oversight/decision.

    Created when autonomy system determines human input is needed.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Context
    action: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    original_decision: Optional[AutonomyDecision] = None

    # Escalation details
    reason: EscalationReason = EscalationReason.LOW_CONFIDENCE
    severity: str = "medium"  # low, medium, high, critical
    timeout_seconds: int = 300  # How long to wait for response

    # Options for human
    options: List[str] = field(default_factory=list)
    recommended_option: Optional[str] = None

    # Response (filled when human responds)
    human_response: Optional[str] = None
    response_timestamp: Optional[str] = None
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "action": self.action,
            "reason": self.reason.value,
            "severity": self.severity,
            "options": self.options,
            "recommended": self.recommended_option,
            "resolved": self.resolved,
        }


@dataclass
class AutonomyConfig:
    """
    Configuration for autonomy system.

    Defines thresholds and policies for autonomous operation.
    """

    # Default autonomy level
    default_level: AutonomyLevel = AutonomyLevel.APPROVE

    # Confidence thresholds (Confidence-Based Routing)
    high_confidence_threshold: float = 0.85  # Can act autonomously
    medium_confidence_threshold: float = 0.7  # Notify human
    low_confidence_threshold: float = 0.5  # Require approval

    # Risk thresholds
    high_risk_threshold: float = 0.7
    block_high_risk: bool = True  # Block high-risk actions entirely

    # Uncertainty settings
    use_calibration: bool = True
    calibration_method: str = "temperature_scaling"
    ensemble_size: int = 5  # For ensemble uncertainty

    # Escalation settings
    escalation_timeout_seconds: int = 300
    max_pending_escalations: int = 10
    auto_deny_on_timeout: bool = False

    # Learning settings
    learn_from_escalations: bool = True
    learning_rate: float = 0.01

    # Safety rails
    blocked_actions: List[str] = field(default_factory=list)
    always_escalate_patterns: List[str] = field(default_factory=list)
