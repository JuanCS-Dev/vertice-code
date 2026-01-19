"""
Discernment Models - Dataclasses.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .types import DiscernmentPhase, WayType


@dataclass
class DiscernmentQuestion:
    """Uma pergunta para guiar o discernimento."""

    category: str
    question: str
    purpose: str
    source: str


@dataclass
class ExperienceWitness:
    """Um testemunho de experiencia relevante."""

    description: str
    lessons_learned: List[str]
    relevance_to_situation: str
    source: str


@dataclass
class TraditionWisdom:
    """Sabedoria da tradicao."""

    teaching: str
    source: str
    application: str
    caveats: List[str] = field(default_factory=list)


@dataclass
class DiscernmentResult:
    """Resultado do processo de discernimento."""

    id: UUID = field(default_factory=uuid4)
    situation: str = ""
    phases_completed: List[DiscernmentPhase] = field(default_factory=list)
    questions_explored: List[DiscernmentQuestion] = field(default_factory=list)
    experiences_considered: List[ExperienceWitness] = field(default_factory=list)
    traditions_consulted: List[TraditionWisdom] = field(default_factory=list)
    way_of_life_indicators: List[str] = field(default_factory=list)
    way_of_death_indicators: List[str] = field(default_factory=list)
    discerned_direction: Optional[WayType] = None
    counsel: str = ""
    confidence: float = 0.5
    need_for_community: bool = True
    suggested_advisors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "situation": self.situation[:100],
            "phases_completed": [p.name for p in self.phases_completed],
            "discerned_direction": self.discerned_direction.name
            if self.discerned_direction
            else None,
            "confidence": self.confidence,
            "need_for_community": self.need_for_community,
        }


__all__ = ["DiscernmentQuestion", "ExperienceWitness", "TraditionWisdom", "DiscernmentResult"]
