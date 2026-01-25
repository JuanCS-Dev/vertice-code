"""
Three Loops Framework

Implements human-AI collaboration patterns for architecture decisions.

Pattern (InfoQ):
- IN THE LOOP: Human decides, AI assists
- ON THE LOOP: AI operates, human supervises
- OUT OF LOOP: AI self-designs with guardrails

Reference:
- https://www.infoq.com/articles/architects-ai-era/
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List
import logging

from .types import (
    ArchitectLoop,
    DecisionImpact,
    DecisionRisk,
    LoopContext,
    LoopRecommendation,
    LOOP_RULES,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ThreeLoopsMixin:
    """
    Mixin providing Three Loops framework capabilities.

    Add to ArchitectAgent via multiple inheritance.
    """

    def select_loop(self, context: LoopContext) -> LoopRecommendation:
        """
        Select the appropriate loop based on decision context.

        Args:
            context: Context for the decision.

        Returns:
            LoopRecommendation with loop and guardrails.
        """
        if context.ethical_considerations or context.regulatory_implications:
            return LoopRecommendation(
                recommended_loop=ArchitectLoop.IN_THE_LOOP,
                confidence=0.95,
                reasoning="Ethical or regulatory considerations require human oversight",
                guardrails=self._get_loop_guardrails(ArchitectLoop.IN_THE_LOOP),
                transition_triggers=self._get_transition_triggers(
                    ArchitectLoop.IN_THE_LOOP, context
                ),
            )

        if context.requires_domain_expertise:
            return LoopRecommendation(
                recommended_loop=ArchitectLoop.IN_THE_LOOP,
                confidence=0.85,
                reasoning="Domain expertise required for this decision",
                guardrails=self._get_loop_guardrails(ArchitectLoop.IN_THE_LOOP),
                transition_triggers=self._get_transition_triggers(
                    ArchitectLoop.IN_THE_LOOP, context
                ),
            )

        key = (context.impact, context.risk)
        loop = LOOP_RULES.get(key, ArchitectLoop.ON_THE_LOOP)

        if context.agent_confidence < 0.5:
            if loop == ArchitectLoop.OUT_OF_LOOP:
                loop = ArchitectLoop.ON_THE_LOOP
            elif loop == ArchitectLoop.ON_THE_LOOP:
                loop = ArchitectLoop.IN_THE_LOOP

        confidence = context.agent_confidence * 0.8
        if loop == ArchitectLoop.OUT_OF_LOOP:
            confidence = max(confidence, 0.7)

        reasoning = self._build_reasoning(context, loop)

        return LoopRecommendation(
            recommended_loop=loop,
            confidence=confidence,
            reasoning=reasoning,
            guardrails=self._get_loop_guardrails(loop),
            transition_triggers=self._get_transition_triggers(loop, context),
        )

    def classify_decision(self, decision_description: str) -> LoopContext:
        """
        Classify a decision to determine appropriate loop.

        Args:
            decision_description: Description of the decision.

        Returns:
            LoopContext for loop selection.
        """
        desc_lower = decision_description.lower()

        impact = DecisionImpact.MEDIUM
        if any(w in desc_lower for w in ["database", "schema", "api contract", "architecture"]):
            impact = DecisionImpact.CRITICAL
        elif any(w in desc_lower for w in ["service", "endpoint", "integration"]):
            impact = DecisionImpact.HIGH
        elif any(w in desc_lower for w in ["component", "module", "class"]):
            impact = DecisionImpact.MEDIUM
        elif any(w in desc_lower for w in ["refactor", "rename", "format"]):
            impact = DecisionImpact.LOW

        risk = DecisionRisk.MEDIUM
        if any(w in desc_lower for w in ["new", "unknown", "migrate", "replace"]):
            risk = DecisionRisk.HIGH
        elif any(w in desc_lower for w in ["add", "extend", "enhance"]):
            risk = DecisionRisk.MEDIUM
        elif any(w in desc_lower for w in ["update", "fix", "improve"]):
            risk = DecisionRisk.LOW

        ethical = any(w in desc_lower for w in ["user data", "privacy", "consent", "bias"])
        regulatory = any(w in desc_lower for w in ["gdpr", "hipaa", "compliance", "audit"])
        domain = any(w in desc_lower for w in ["business", "domain", "specific", "custom"])

        confidence = 0.7
        if "simple" in desc_lower or "straightforward" in desc_lower:
            confidence = 0.9
        elif "complex" in desc_lower or "unclear" in desc_lower:
            confidence = 0.4

        return LoopContext(
            decision_type=decision_description[:50],
            impact=impact,
            risk=risk,
            agent_confidence=confidence,
            requires_domain_expertise=domain,
            ethical_considerations=ethical,
            regulatory_implications=regulatory,
        )

    def _get_loop_guardrails(self, loop: ArchitectLoop) -> List[str]:
        """Get guardrails for a specific loop."""
        guardrails = {
            ArchitectLoop.IN_THE_LOOP: [
                "All proposals require human approval",
                "Agent provides options, human chooses",
                "Changes logged for audit trail",
                "Rollback plan required before execution",
            ],
            ArchitectLoop.ON_THE_LOOP: [
                "Agent executes, human monitors",
                "Automatic alerts on anomalies",
                "Human can intervene at any point",
                "Regular checkpoints for review",
            ],
            ArchitectLoop.OUT_OF_LOOP: [
                "Agent operates within defined boundaries",
                "Automatic validation of outputs",
                "Escalate to ON/IN loop if uncertain",
                "Post-execution review logging",
            ],
        }
        return guardrails.get(loop, [])

    def _get_transition_triggers(
        self,
        loop: ArchitectLoop,
        context: LoopContext,
    ) -> List[str]:
        """Get conditions that would trigger transition to different loop."""
        triggers = {
            ArchitectLoop.IN_THE_LOOP: [
                "Transition to ON: After human sets clear guidelines",
                "Transition to OUT: For well-understood patterns",
            ],
            ArchitectLoop.ON_THE_LOOP: [
                "Escalate to IN: If unexpected issues arise",
                "Transition to OUT: After pattern is validated",
            ],
            ArchitectLoop.OUT_OF_LOOP: [
                "Escalate to ON: If confidence drops below threshold",
                "Escalate to IN: If ethical/regulatory flags triggered",
            ],
        }
        return triggers.get(loop, [])

    def _build_reasoning(
        self,
        context: LoopContext,
        loop: ArchitectLoop,
    ) -> str:
        """Build reasoning for loop selection."""
        parts = []

        parts.append(f"Impact: {context.impact.value}")
        parts.append(f"Risk: {context.risk.value}")
        parts.append(f"Confidence: {context.agent_confidence:.2f}")

        if loop == ArchitectLoop.IN_THE_LOOP:
            parts.append("Human oversight required for this decision type")
        elif loop == ArchitectLoop.ON_THE_LOOP:
            parts.append("AI can operate with human supervision")
        else:
            parts.append("AI can self-design within guardrails")

        return " | ".join(parts)
