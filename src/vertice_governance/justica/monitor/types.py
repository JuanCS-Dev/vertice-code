"""
Monitor Types - Core types for the monitoring system.

SuspicionLevel enum and SuspicionScore dataclass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Tuple


class SuspicionLevel(Enum):
    """Niveis de suspeita baseado no score."""

    NONE = auto()  # 0-20: Comportamento normal
    LOW = auto()  # 21-40: Ligeiramente suspeito
    MODERATE = auto()  # 41-60: Moderadamente suspeito
    HIGH = auto()  # 61-80: Altamente suspeito
    CRITICAL = auto()  # 81-100: Violacao provavel

    @classmethod
    def from_score(cls, score: float) -> SuspicionLevel:
        """Converte score numerico para nivel de suspeita."""
        if score <= 20:
            return cls.NONE
        elif score <= 40:
            return cls.LOW
        elif score <= 60:
            return cls.MODERATE
        elif score <= 80:
            return cls.HIGH
        else:
            return cls.CRITICAL


@dataclass
class SuspicionScore:
    """
    Score de suspeita para um agente ou acao especifica.

    Attributes:
        score: Valor de 0 a 100
        agent_id: Agente analisado
        factors: Fatores que contribuiram para o score
        timestamp: Quando foi calculado
        context: Contexto adicional
    """

    score: float
    agent_id: str
    factors: List[Tuple[str, float]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    context: Dict[str, Any] = field(default_factory=dict)

    @property
    def level(self) -> SuspicionLevel:
        """Nivel de suspeita derivado do score."""
        return SuspicionLevel.from_score(self.score)

    @property
    def is_violation(self) -> bool:
        """Score >= 80 indica violacao detectada."""
        return self.score >= 80

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionario."""
        return {
            "score": self.score,
            "level": self.level.name,
            "is_violation": self.is_violation,
            "agent_id": self.agent_id,
            "factors": self.factors,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
        }


__all__ = [
    "SuspicionLevel",
    "SuspicionScore",
]
