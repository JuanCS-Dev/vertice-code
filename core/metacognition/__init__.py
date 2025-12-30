"""
Vertice Metacognition - Self-Reflection & Learning

Phase 3 Integration:
- Cognitive-level reflection (in-task evaluation)
- Metacognitive learning (cross-task patterns)
- Confidence calibration
- Strategy adaptation

Reference:
- Reflexion (Shinn et al., 2023)
- MetaAgent (arXiv:2508.00271v2)
- Microsoft Metacognition Research (2025)
"""

from .types import (
    ReflectionLevel,
    ReflectionOutcome,
    ConfidenceLevel,
    ReasoningStep,
    ReflectionResult,
    ExperienceRecord,
    StrategyProfile,
)
from .calibrator import ConfidenceCalibrator
from .engine import ReflectionEngine
from .memory import ExperienceMemory
from .mixin import MetaCognitiveMixin

__all__ = [
    # Types
    "ReflectionLevel",
    "ReflectionOutcome",
    "ConfidenceLevel",
    "ReasoningStep",
    "ReflectionResult",
    "ExperienceRecord",
    "StrategyProfile",
    # Components
    "ConfidenceCalibrator",
    "ReflectionEngine",
    "ExperienceMemory",
    # Mixin
    "MetaCognitiveMixin",
]
