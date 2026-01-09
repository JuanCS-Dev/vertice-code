"""
Monitor Events - Event dataclass for monitoring.

MonitoringEvent represents any observed action or behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import UUID, uuid4


@dataclass
class MonitoringEvent:
    """
    Evento de monitoramento - qualquer acao ou comportamento observado.

    Attributes:
        id: Identificador unico
        timestamp: Momento do evento
        agent_id: ID do agente
        event_type: Tipo (transcript, thought, tool_call, resource_access, etc.)
        content: Conteudo do evento
        metadata: Dados adicionais
        analyzed: Se ja foi analisado
        suspicion_contribution: Contribuicao para o score de suspeita
        flags: Flags detectadas na analise
    """

    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    agent_id: str = ""
    event_type: str = "unknown"
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Analise
    analyzed: bool = False
    suspicion_contribution: float = 0.0
    flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionario."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "event_type": self.event_type,
            "content_preview": (
                self.content[:200] + "..." if len(self.content) > 200 else self.content
            ),
            "flags": self.flags,
            "suspicion_contribution": self.suspicion_contribution,
        }


__all__ = ["MonitoringEvent"]
