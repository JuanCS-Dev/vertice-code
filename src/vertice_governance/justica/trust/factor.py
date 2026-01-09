"""
Trust Factor - Per-agent trust tracking.

TrustFactor dataclass for managing agent trust state.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Deque, Dict, Optional

from .events import TrustEvent
from .types import TrustLevel


@dataclass
class TrustFactor:
    """
    Trust Factor de um agente especifico.

    O Trust Factor e calculado como:
        TF = 1 - (weighted_violations + severity_score) / total_actions

    E e modificado por:
        - Violacoes (reduzem)
        - Acoes bem-sucedidas (aumentam lentamente)
        - Decaimento temporal (violacoes antigas pesam menos)
        - Recuperacao gradual (apos periodo sem violacoes)

    Attributes:
        agent_id: ID do agente
        current_factor: Valor atual do trust factor (0.0 a 1.0)
        level: Nivel de confianca derivado
        events: Historico de eventos
        total_actions: Total de acoes do agente
        total_violations: Total de violacoes
    """

    agent_id: str
    current_factor: float = 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Historico (ultimos 1000 eventos)
    events: Deque[TrustEvent] = field(default_factory=lambda: deque(maxlen=1000))

    # Contadores
    total_actions: int = 0
    total_violations: int = 0
    consecutive_good_actions: int = 0

    # Estado
    is_suspended: bool = False
    suspension_reason: Optional[str] = None
    suspension_until: Optional[datetime] = None

    @property
    def level(self) -> TrustLevel:
        """Retorna o nivel de confianca atual."""
        if self.is_suspended:
            return TrustLevel.SUSPENDED
        return TrustLevel.from_factor(self.current_factor)

    @property
    def violation_rate(self) -> float:
        """Taxa de violacoes."""
        if self.total_actions == 0:
            return 0.0
        return self.total_violations / self.total_actions

    @property
    def is_healthy(self) -> bool:
        """Check if trust factor is in healthy range."""
        return self.current_factor >= 0.60 and not self.is_suspended

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "current_factor": self.current_factor,
            "level": self.level.name,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "total_actions": self.total_actions,
            "total_violations": self.total_violations,
            "violation_rate": self.violation_rate,
            "consecutive_good_actions": self.consecutive_good_actions,
            "is_suspended": self.is_suspended,
            "suspension_reason": self.suspension_reason,
            "recent_events": [e.to_dict() for e in list(self.events)[-10:]],
        }


__all__ = ["TrustFactor"]
