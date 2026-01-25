"""
Metacognition Types

Type definitions for meta-cognitive reflection system.

Reference:
- Microsoft Metacognition Research (2025)
- Reflexion (Shinn et al., 2023)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List
from enum import Enum
from datetime import datetime


class ReflectionLevel(str, Enum):
    """Level of reflection processing."""

    COGNITIVE = "cognitive"  # In-task reasoning evaluation
    METACOGNITIVE = "metacognitive"  # Cross-task learning
    STRATEGIC = "strategic"  # Long-term strategy adjustment


class ConfidenceLevel(str, Enum):
    """Confidence calibration levels."""

    VERY_LOW = "very_low"  # 0-20%
    LOW = "low"  # 20-40%
    MODERATE = "moderate"  # 40-60%
    HIGH = "high"  # 60-80%
    VERY_HIGH = "very_high"  # 80-100%


class ReflectionOutcome(str, Enum):
    """Outcome of a reflection evaluation."""

    PROCEED = "proceed"  # Continue with current approach
    ADJUST = "adjust"  # Minor adjustment needed
    RECONSIDER = "reconsider"  # Major rethink required
    ABORT = "abort"  # Stop current approach entirely


@dataclass
class ReasoningStep:
    """A single step in the reasoning chain."""

    id: str
    description: str
    input_state: Dict[str, Any]
    output_state: Dict[str, Any]
    confidence: float  # 0.0 to 1.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReflectionResult:
    """Result of a reflection evaluation."""

    id: str
    level: ReflectionLevel
    outcome: ReflectionOutcome
    confidence: float
    reasoning: str
    suggestions: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "level": self.level.value,
            "outcome": self.outcome.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class ExperienceRecord:
    """Record of past experience for learning."""

    id: str
    task_type: str
    strategy_used: str
    outcome: str  # success/failure/partial
    confidence_before: float
    confidence_after: float
    lessons_learned: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyProfile:
    """Profile for a problem-solving strategy."""

    id: str
    name: str
    description: str
    success_rate: float  # Historical success rate
    applicable_contexts: List[str]
    contraindications: List[str]
    avg_confidence: float
    usage_count: int = 0
