"""
Thought Signatures Mixin - Manages reasoning chain signatures.
"""

from typing import List, Optional

from ..types import ThoughtSignature


class ThoughtSignaturesMixin:
    """Mixin for managing thought signatures."""

    def __init__(self) -> None:
        self._thoughts: List[ThoughtSignature] = []

    def add_thought(
        self,
        reasoning: str,
        agent_id: str = "",
        key_insights: Optional[List[str]] = None,
        next_action: str = "",
        confidence: float = 1.0,
    ) -> None:
        """Add a thought signature to the reasoning chain."""
        thought_sig = ThoughtSignature.from_reasoning(
            agent_id=agent_id,
            reasoning=reasoning,
            insights=key_insights or [],
            next_action=next_action,
        )
        thought_sig.confidence = confidence
        self._thoughts.append(thought_sig)

    def get_thought_chain(self) -> List[ThoughtSignature]:
        """Get the complete thought signature chain."""
        return self._thoughts.copy()
