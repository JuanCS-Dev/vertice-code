"""
Trust Events - Event tracking for trust factor changes.

TrustEvent dataclass for recording trust-affecting events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from ..constitution import Severity, ViolationType


@dataclass
class TrustEvent:
    """
    Registro de um evento que afeta o trust factor.

    Attributes:
        id: Identificador unico
        timestamp: Quando ocorreu
        event_type: Tipo do evento (violation, good_action, decay, recovery)
        violation_type: Tipo de violacao (se aplicavel)
        severity: Severidade do evento
        impact: Impacto no trust factor (-1.0 a +1.0)
        description: Descricao do evento
        context: Contexto adicional
    """

    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str = "unknown"
    violation_type: Optional[ViolationType] = None
    severity: Severity = Severity.INFO
    impact: float = 0.0
    description: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "violation_type": self.violation_type.name if self.violation_type else None,
            "severity": self.severity.name,
            "impact": self.impact,
            "description": self.description,
            "context": self.context,
        }

    @property
    def is_violation(self) -> bool:
        """Check if this event represents a violation."""
        return self.event_type == "violation"

    @property
    def is_positive(self) -> bool:
        """Check if this event has positive impact."""
        return self.impact > 0


__all__ = ["TrustEvent"]
