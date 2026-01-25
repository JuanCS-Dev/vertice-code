"""
Autonomy Compatibility Layer

Maps ThreeLoops API to BoundedAutonomy for unified human-AI collaboration.

Mapping:
- IN_THE_LOOP (AITL) -> L2_APPROVE / L3_HUMAN_ONLY
- ON_THE_LOOP (AOTL) -> L1_NOTIFY
- OUT_OF_LOOP (AOOTL) -> L0_AUTONOMOUS

Both systems reference the same InfoQ article:
https://www.infoq.com/articles/architects-ai-era/

DEPRECATED: ThreeLoopsMixin is deprecated. Use BoundedAutonomyMixin directly.
"""

from __future__ import annotations

import warnings
from typing import List
import logging

from agents.orchestrator.types import AutonomyLevel
from .types import (
    ArchitectLoop,
    DecisionImpact,
    DecisionRisk,
    LoopContext,
    LoopRecommendation,
    LOOP_RULES,
)

logger = logging.getLogger(__name__)


# Mapping between the two systems
LOOP_TO_AUTONOMY = {
    ArchitectLoop.IN_THE_LOOP: AutonomyLevel.L2_APPROVE,
    ArchitectLoop.ON_THE_LOOP: AutonomyLevel.L1_NOTIFY,
    ArchitectLoop.OUT_OF_LOOP: AutonomyLevel.L0_AUTONOMOUS,
}

AUTONOMY_TO_LOOP = {
    AutonomyLevel.L0_AUTONOMOUS: ArchitectLoop.OUT_OF_LOOP,
    AutonomyLevel.L1_NOTIFY: ArchitectLoop.ON_THE_LOOP,
    AutonomyLevel.L2_APPROVE: ArchitectLoop.IN_THE_LOOP,
    AutonomyLevel.L3_HUMAN_ONLY: ArchitectLoop.IN_THE_LOOP,
}


class ThreeLoopsMixin:
    """
    DEPRECATED: Compatibility mixin providing ThreeLoops API.
    
    This mixin is deprecated. The underlying logic now uses BoundedAutonomy
    concepts (L0-L3) which are more granular and widely used in the codebase.
    
    Migration guide:
    - select_loop() -> Use check_autonomy() from OrchestratorAgent
    - classify_decision() -> Use classify_operation() from OrchestratorAgent
    - ArchitectLoop.IN_THE_LOOP -> AutonomyLevel.L2_APPROVE
    - ArchitectLoop.ON_THE_LOOP -> AutonomyLevel.L1_NOTIFY
    - ArchitectLoop.OUT_OF_LOOP -> AutonomyLevel.L0_AUTONOMOUS
    """

    def select_loop(self, context: LoopContext) -> LoopRecommendation:
        """
        Select the appropriate loop based on decision context.
        
        DEPRECATED: Use check_autonomy() for new code.
        """
        warnings.warn(
            "ThreeLoopsMixin.select_loop() is deprecated. "
            "Use BoundedAutonomyMixin.check_autonomy() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        
        # Ethical/regulatory -> always IN_THE_LOOP
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

        # Domain expertise -> IN_THE_LOOP
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

        # Use impact/risk matrix
        key = (context.impact, context.risk)
        loop = LOOP_RULES.get(key, ArchitectLoop.ON_THE_LOOP)

        # Adjust based on confidence
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
        
        DEPRECATED: Use classify_operation() for new code.
        """
        desc_lower = decision_description.lower()

        # Determine impact
        impact = DecisionImpact.MEDIUM
        if any(w in desc_lower for w in ["database", "schema", "api contract", "architecture"]):
            impact = DecisionImpact.CRITICAL
        elif any(w in desc_lower for w in ["service", "endpoint", "integration"]):
            impact = DecisionImpact.HIGH
        elif any(w in desc_lower for w in ["component", "module", "class"]):
            impact = DecisionImpact.MEDIUM
        elif any(w in desc_lower for w in ["refactor", "rename", "format"]):
            impact = DecisionImpact.LOW

        # Determine risk
        risk = DecisionRisk.MEDIUM
        if any(w in desc_lower for w in ["new", "unknown", "migrate", "replace"]):
            risk = DecisionRisk.HIGH
        elif any(w in desc_lower for w in ["add", "extend", "enhance"]):
            risk = DecisionRisk.MEDIUM
        elif any(w in desc_lower for w in ["update", "fix", "improve"]):
            risk = DecisionRisk.LOW

        # Check for special considerations
        ethical = any(w in desc_lower for w in ["user data", "privacy", "consent", "bias"])
        regulatory = any(w in desc_lower for w in ["gdpr", "hipaa", "compliance", "audit"])
        domain = any(w in desc_lower for w in ["business", "domain", "specific", "custom"])

        # Determine confidence
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

    def get_autonomy_level_from_loop(self, loop: ArchitectLoop) -> AutonomyLevel:
        """Convert ThreeLoops loop to BoundedAutonomy level."""
        return LOOP_TO_AUTONOMY.get(loop, AutonomyLevel.L1_NOTIFY)

    def get_loop_from_autonomy(self, level: AutonomyLevel) -> ArchitectLoop:
        """Convert BoundedAutonomy level to ThreeLoops loop."""
        return AUTONOMY_TO_LOOP.get(level, ArchitectLoop.ON_THE_LOOP)

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
