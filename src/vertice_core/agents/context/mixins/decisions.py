"""
Decision Tracking Mixin - Records and manages agent decisions.
"""

from typing import Any, Dict, List, Optional

from ..types import Decision, DecisionType


class DecisionTrackingMixin:
    """Mixin for tracking agent decisions."""

    def __init__(self) -> None:
        self._decisions: List[Decision] = []

    def record_decision(
        self,
        description: str,
        decision_type: DecisionType,
        confidence: float,
        reasoning: str,
        alternatives_considered: Optional[List[str]] = None,
        agent_id: str = "",
        outcome: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an agent decision for explainability."""
        decision_obj = Decision(
            description=description,
            decision_type=decision_type,
            confidence=confidence,
            reasoning=reasoning,
            alternatives_considered=alternatives_considered or [],
            agent_id=agent_id,
            outcome=outcome,
            metadata=metadata or {},
        )
        self._decisions.append(decision_obj)

    def get_decisions(
        self,
        agent_id: Optional[str] = None,
        decision_type: Optional[DecisionType] = None,
        limit: int = 0,
    ) -> List[Decision]:
        """Get recorded decisions with optional filtering."""
        decisions = self._decisions

        if agent_id:
            decisions = [d for d in decisions if d.agent_id == agent_id]

        if decision_type:
            decisions = [d for d in decisions if d.decision_type == decision_type]

        if limit > 0:
            decisions = decisions[-limit:]

        return decisions.copy()
