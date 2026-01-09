"""
Monitor Session - Agent session tracking.

AgentSession maintains history and metrics for pattern analysis.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Deque
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from .events import MonitoringEvent
    from .types import SuspicionScore


@dataclass
class AgentSession:
    """
    Sessao de monitoramento de um agente.

    Mantem historico e metricas para analise de padroes.

    Attributes:
        agent_id: ID do agente
        session_id: ID da sessao
        started_at: Inicio da sessao
        last_activity: Ultima atividade
        events: Historico de eventos (ultimos 1000)
        suspicion_history: Historico de scores (ultimos 100)
        total_events: Total de eventos processados
        flagged_events: Eventos com flags
        denied_attempts: Tentativas negadas
        tool_calls: Chamadas de ferramentas
        resource_accesses: Acessos a recursos
        current_suspicion: Score de suspeita atual
        is_under_investigation: Se esta sob investigacao
    """

    agent_id: str
    session_id: UUID = field(default_factory=uuid4)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Historico de eventos (ultimos 1000)
    events: Deque["MonitoringEvent"] = field(default_factory=lambda: deque(maxlen=1000))

    # Historico de scores
    suspicion_history: Deque["SuspicionScore"] = field(
        default_factory=lambda: deque(maxlen=100)
    )

    # Contadores
    total_events: int = 0
    flagged_events: int = 0

    # Metricas de comportamento
    denied_attempts: int = 0
    tool_calls: int = 0
    resource_accesses: int = 0

    # Estado
    current_suspicion: float = 0.0
    is_under_investigation: bool = False

    @property
    def average_suspicion(self) -> float:
        """Calcula media dos scores de suspeita."""
        if not self.suspicion_history:
            return 0.0
        return sum(s.score for s in self.suspicion_history) / len(self.suspicion_history)

    @property
    def max_suspicion(self) -> float:
        """Retorna o maior score de suspeita."""
        if not self.suspicion_history:
            return 0.0
        return max(s.score for s in self.suspicion_history)

    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return {
            "agent_id": self.agent_id,
            "session_id": str(self.session_id),
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "total_events": self.total_events,
            "flagged_events": self.flagged_events,
            "denied_attempts": self.denied_attempts,
            "current_suspicion": self.current_suspicion,
            "average_suspicion": self.average_suspicion,
            "max_suspicion": self.max_suspicion,
        }


__all__ = ["AgentSession"]
