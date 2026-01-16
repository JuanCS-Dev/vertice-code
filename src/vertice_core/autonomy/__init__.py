"""
Autonomy Module

Bounded Human-in-the-Loop (HITL) autonomy with uncertainty quantification.

References:
- arXiv:2503.15850 (Uncertainty Quantification in AI Agents)
- arXiv:2402.16906 (Confidence-Based Routing)
- arXiv:2310.03046 (Calibration of LLM Confidence)
- arXiv:2307.15042 (Staged Autonomy)
- Constitutional AI (Anthropic, 2022)
"""

from .types import (
    AutonomyLevel,
    UncertaintyType,
    EscalationReason,
    ConfidenceScore,
    UncertaintyEstimate,
    AutonomyDecision,
    EscalationRequest,
    AutonomyConfig,
)
from .uncertainty import UncertaintyEstimator
from .router import ConfidenceRouter
from .escalation import EscalationManager
from .calibrator import ConfidenceCalibrator
from .mixin import AutonomyMixin

__all__ = [
    # Types
    "AutonomyLevel",
    "UncertaintyType",
    "EscalationReason",
    "ConfidenceScore",
    "UncertaintyEstimate",
    "AutonomyDecision",
    "EscalationRequest",
    "AutonomyConfig",
    # Core
    "UncertaintyEstimator",
    "ConfidenceRouter",
    "EscalationManager",
    "ConfidenceCalibrator",
    "AutonomyMixin",
]
