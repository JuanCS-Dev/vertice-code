"""
Learning Types - Enums and dataclasses for context learning.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class FeedbackType(str, Enum):
    """Types of user feedback."""
    EXPLICIT_POSITIVE = "explicit_positive"
    EXPLICIT_NEGATIVE = "explicit_negative"
    IMPLICIT_ACCEPT = "implicit_accept"
    IMPLICIT_REJECT = "implicit_reject"
    CORRECTION = "correction"
    PREFERENCE = "preference"


class LearningCategory(str, Enum):
    """Categories of learned behaviors."""
    CODE_STYLE = "code_style"
    TOOL_PREFERENCE = "tool_preference"
    RESPONSE_FORMAT = "response_format"
    LANGUAGE = "language"
    VERBOSITY = "verbosity"
    AGENT_ROUTING = "agent_routing"
    ERROR_HANDLING = "error_handling"


@dataclass
class LearningRecord:
    """Record of a learned behavior."""
    category: LearningCategory
    key: str
    value: Any
    confidence: float
    feedback_type: FeedbackType
    timestamp: float = field(default_factory=time.time)
    examples: List[str] = field(default_factory=list)
    decay_factor: float = 1.0


@dataclass
class UserPreferences:
    """Aggregated user preferences."""
    code_style: Dict[str, Any] = field(default_factory=dict)
    tool_preferences: Dict[str, float] = field(default_factory=dict)
    response_format: Dict[str, Any] = field(default_factory=dict)
    language: str = "en"
    verbosity: str = "normal"
    custom: Dict[str, Any] = field(default_factory=dict)


# Confidence deltas for different feedback types
CONFIDENCE_DELTAS = {
    FeedbackType.EXPLICIT_POSITIVE: 0.3,
    FeedbackType.EXPLICIT_NEGATIVE: -0.3,
    FeedbackType.IMPLICIT_ACCEPT: 0.1,
    FeedbackType.IMPLICIT_REJECT: -0.1,
    FeedbackType.CORRECTION: 0.4,
    FeedbackType.PREFERENCE: 0.5,
}
