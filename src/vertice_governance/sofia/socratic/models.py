"""
Socratic Models - Dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import UUID, uuid4

from .types import QuestionType, DialoguePhase


@dataclass
class SocraticQuestion:
    """Uma pergunta socratica estruturada."""

    id: UUID = field(default_factory=uuid4)
    question_type: QuestionType = QuestionType.CLARIFICATION
    question_text: str = ""
    purpose: str = ""
    follow_ups: List[str] = field(default_factory=list)
    context_triggers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "type": self.question_type.name,
            "question": self.question_text,
            "purpose": self.purpose,
            "follow_ups": self.follow_ups,
        }


@dataclass
class DialogueState:
    """Estado atual do dialogo socratico."""

    id: UUID = field(default_factory=uuid4)
    phase: DialoguePhase = DialoguePhase.OPENING
    questions_asked: List[SocraticQuestion] = field(default_factory=list)
    insights_gathered: List[str] = field(default_factory=list)
    assumptions_identified: List[str] = field(default_factory=list)
    user_understanding_level: float = 0.5  # 0-1
    depth_level: int = 0  # Niveis de aprofundamento
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def should_synthesize(self) -> bool:
        """Verifica se e hora de sintetizar."""
        return (
            len(self.questions_asked) >= 3
            or self.depth_level >= 2
            or self.user_understanding_level > 0.8
        )


__all__ = ["SocraticQuestion", "DialogueState"]
