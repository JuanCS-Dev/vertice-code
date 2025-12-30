"""
planner/types.py: Domain Types for Planning System.

Contains Enums and lightweight dataclasses used by the planner.
Extracted from planner.py for better modularity (Boris Cherny pattern).

Groups:
- Execution & Priority Enums
- Clarifying Questions (Cursor 2.1 pattern)
- Planning Modes (Claude Code pattern)
- Confidence Ratings (Devin pattern)
- Multi-Plan (Verbalized Sampling - Zhang et al. 2025)

NOTE: SOPStep, ExecutionStage, and ExecutionPlan are defined in agent.py
because they have complex fields tightly coupled with PlannerAgent.
They are re-exported from __init__.py for convenience.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================================
# EXECUTION & PRIORITY ENUMS
# ============================================================================

class ExecutionStrategy(str, Enum):
    """Execution patterns for multi-agent coordination."""
    SEQUENTIAL = "sequential"      # One after another (dependencies)
    PARALLEL = "parallel"          # All at once (no dependencies)
    FORK_JOIN = "fork-join"        # Parallel + merge at end
    PIPELINE = "pipeline"          # Stream output between agents
    CONDITIONAL = "conditional"    # Based on runtime conditions


class AgentPriority(str, Enum):
    """Priority levels for agent tasks."""
    CRITICAL = "critical"  # Must complete for success
    HIGH = "high"          # Important but can continue
    MEDIUM = "medium"      # Nice to have
    LOW = "low"            # Optional enhancement


class CheckpointType(str, Enum):
    """Types of execution checkpoints."""
    VALIDATION = "validation"      # Validate before continuing
    ROLLBACK = "rollback"          # Can rollback to here
    DECISION = "decision"          # Decision point for branching


# ============================================================================
# CLARIFYING QUESTIONS (Cursor 2.1 Pattern)
# ============================================================================

class ClarifyingQuestion(BaseModel):
    """
    Interactive question to gather user context before planning.

    Inspired by Cursor 2.1's clarifying questions feature.
    """
    id: str = Field(default_factory=lambda: f"q-{uuid.uuid4().hex[:8]}")
    question: str = Field(..., description="The question to ask the user")
    category: str = Field(default="general", description="scope|approach|constraints|preferences")
    options: List[str] = Field(default_factory=list, description="Suggested answers")
    required: bool = Field(default=False, description="Must be answered before planning")
    default: Optional[str] = Field(default=None, description="Default if user skips")


class ClarificationResponse(BaseModel):
    """User's response to clarifying questions."""
    question_id: str
    answer: str
    skipped: bool = False


# ============================================================================
# PLANNING MODES (Claude Code Pattern)
# ============================================================================

class PlanningMode(str, Enum):
    """
    Planning modes inspired by Claude Code Plan Mode.
    """
    EXPLORATION = "exploration"  # Read-only exploration
    PLANNING = "planning"        # Generate plan
    EXECUTION = "execution"      # Execute plan


# ============================================================================
# CONFIDENCE RATINGS (Devin Pattern)
# ============================================================================

class ConfidenceLevel(str, Enum):
    """Confidence levels for plan steps."""
    CERTAIN = "certain"          # 0.9-1.0
    CONFIDENT = "confident"      # 0.7-0.9
    MODERATE = "moderate"        # 0.5-0.7
    LOW = "low"                  # 0.3-0.5
    SPECULATIVE = "speculative"  # 0.0-0.3


@dataclass
class StepConfidence:
    """Confidence rating for a planning step."""
    score: float  # 0.0 to 1.0
    level: ConfidenceLevel
    reasoning: str
    risk_factors: List[str] = field(default_factory=list)

    @classmethod
    def from_score(cls, score: float, reasoning: str = "", risks: List[str] = None) -> StepConfidence:
        """Create confidence from numeric score."""
        score = max(0.0, min(1.0, score))

        if score >= 0.9:
            level = ConfidenceLevel.CERTAIN
        elif score >= 0.7:
            level = ConfidenceLevel.CONFIDENT
        elif score >= 0.5:
            level = ConfidenceLevel.MODERATE
        elif score >= 0.3:
            level = ConfidenceLevel.LOW
        else:
            level = ConfidenceLevel.SPECULATIVE

        return cls(
            score=score,
            level=level,
            reasoning=reasoning or f"Confidence score: {score:.2f}",
            risk_factors=risks or []
        )


# ============================================================================
# MULTI-PLAN (Verbalized Sampling - Zhang et al. 2025)
# ============================================================================

class PlanStrategy(str, Enum):
    """Plan generation strategies based on Verbalized Sampling."""
    STANDARD = "standard"        # Plan A: Conventional, low risk
    ACCELERATOR = "accelerator"  # Plan B: High speed, higher risk
    LATERAL = "lateral"          # Plan C: Creative/unconventional


@dataclass
class PlanProbabilities:
    """Verbalized probability estimates for a plan."""
    success: float      # P(Success)
    friction: float     # P(Friction)
    time_overrun: float # P(TimeOverrun)
    quality: float      # P(Quality)

    @property
    def risk_reward_ratio(self) -> float:
        """Calculate risk/reward ratio."""
        reward = self.success * self.quality
        risk = self.friction + self.time_overrun
        if risk == 0:
            return float('inf')
        return reward / risk

    @property
    def overall_score(self) -> float:
        """Weighted overall score (0-1)."""
        return (
            self.success * 0.4 +
            (1 - self.friction) * 0.25 +
            (1 - self.time_overrun) * 0.15 +
            self.quality * 0.2
        )

    def to_display(self) -> str:
        """Format for display."""
        return (
            f"P(Success)={self.success:.2f} | "
            f"P(Friction)={self.friction:.2f} | "
            f"P(Quality)={self.quality:.2f}"
        )


class AlternativePlan(BaseModel):
    """A single alternative plan with strategy and probabilities."""
    strategy: PlanStrategy
    name: str
    description: str
    plan: Dict[str, Any]

    # Verbalized probabilities
    p_success: float = Field(ge=0.0, le=1.0)
    p_friction: float = Field(ge=0.0, le=1.0)
    p_time_overrun: float = Field(default=0.3, ge=0.0, le=1.0)
    p_quality: float = Field(default=0.7, ge=0.0, le=1.0)

    # Analysis
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    best_for: str = ""

    @property
    def probabilities(self) -> PlanProbabilities:
        return PlanProbabilities(
            success=self.p_success,
            friction=self.p_friction,
            time_overrun=self.p_time_overrun,
            quality=self.p_quality
        )

    @property
    def risk_reward_ratio(self) -> float:
        return self.probabilities.risk_reward_ratio

    @property
    def overall_score(self) -> float:
        return self.probabilities.overall_score


class MultiPlanResult(BaseModel):
    """Result of multi-plan generation."""
    task_summary: str
    plans: List[AlternativePlan] = Field(min_length=1, max_length=5)
    recommended_plan: PlanStrategy
    recommendation_reasoning: str
    comparison_summary: str = ""
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    generation_time_ms: Optional[int] = None

    def get_plan(self, strategy: PlanStrategy) -> Optional[AlternativePlan]:
        """Get plan by strategy."""
        for plan in self.plans:
            if plan.strategy == strategy:
                return plan
        return None

    def get_recommended(self) -> Optional[AlternativePlan]:
        """Get the recommended plan."""
        return self.get_plan(self.recommended_plan)

    def to_markdown(self) -> str:
        """Format as markdown for display."""
        lines = [
            "# Multi-Plan Analysis (Verbalized Sampling)",
            "",
            f"**Task:** {self.task_summary}",
            "",
            "---",
            "",
        ]

        for plan in self.plans:
            emoji = {"standard": "A", "accelerator": "B", "lateral": "C"}.get(
                plan.strategy.value, "X"
            )
            lines.extend([
                f"## Plan {emoji}: {plan.name}",
                "",
                f"*{plan.description}*",
                "",
                f"**Probabilities:** {plan.probabilities.to_display()}",
                f"**Overall Score:** {plan.overall_score:.2f}",
                "",
            ])

            if plan.pros:
                lines.append("**Pros:**")
                for pro in plan.pros:
                    lines.append(f"- {pro}")
                lines.append("")

            if plan.cons:
                lines.append("**Cons:**")
                for con in plan.cons:
                    lines.append(f"- {con}")
                lines.append("")

            lines.append("---")
            lines.append("")

        rec = self.get_recommended()
        lines.extend([
            "## RECOMMENDATION",
            "",
            f"**Selected:** Plan {self.recommended_plan.value.upper()}" +
            (f" - {rec.name}" if rec else ""),
            "",
            f"**Reasoning:** {self.recommendation_reasoning}",
        ])

        return "\n".join(lines)


# ============================================================================
# SOP & EXECUTION MODELS - See agent.py
# ============================================================================
# NOTE: SOPStep, ExecutionStage, and ExecutionPlan are defined in agent.py
# because they have complex fields and are tightly coupled with PlannerAgent.
# They are re-exported from __init__.py for convenience.
