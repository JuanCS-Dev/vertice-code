"""
Reviewer Agent Types

Dataclasses and types for Reviewer Agent.
Includes Deep Think pattern types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class ReviewSeverity(str, Enum):
    """Severity levels for review findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DeepThinkStage(str, Enum):
    """Stages of Deep Think analysis (CodeMender pattern)."""

    STATIC_ANALYSIS = "static"
    DEEP_REASONING = "reasoning"
    CRITIQUE = "critique"
    VALIDATION = "validation"


@dataclass
class ThinkingStep:
    """A single step in the Deep Think reasoning process."""

    stage: DeepThinkStage
    thought: str
    confidence: float
    evidence: List[str] = field(default_factory=list)


@dataclass
class ReviewFinding:
    """A single finding from code review."""

    id: str
    severity: ReviewSeverity
    category: str
    file_path: str
    line_start: int
    line_end: int
    title: str
    description: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    reasoning: Optional[str] = None
    confidence: float = 0.8
    validated: bool = False


@dataclass
class DeepThinkResult:
    """
    Result of Deep Think analysis.

    Each finding goes through reasoning → critique → validation.
    """

    thinking_steps: List[ThinkingStep]
    validated_findings: List[ReviewFinding]
    rejected_findings: List[ReviewFinding]
    reasoning_summary: str
    confidence_score: float

    @property
    def total_thinking_time(self) -> int:
        """Proxy for thinking depth (number of steps)."""
        return len(self.thinking_steps)


@dataclass
class ReviewResult:
    """Complete review result."""

    file_path: str
    findings: List[ReviewFinding]
    summary: str
    score: float
    reviewed_by: str = "reviewer"
    deep_think: Optional[DeepThinkResult] = None
