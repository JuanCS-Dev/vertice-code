"""
Audit Entry - Data structure for audit log entries.

AuditEntry dataclass with serialization support.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from .types import AuditCategory, AuditLevel


@dataclass
class AuditEntry:
    """
    Uma entrada no audit log.

    Contem todas as informacoes necessarias para reconstruir
    o contexto e raciocinio de uma decisao.

    Attributes:
        id: Identificador unico
        timestamp: Quando ocorreu
        level: Nivel de severidade
        category: Categoria do evento
        agent_id: ID do agente envolvido (se aplicavel)
        action: Acao tomada ou evento
        reasoning: Raciocinio por tras da decisao
        context: Contexto completo
        metadata: Dados adicionais
        trace_id: ID para correlacionar eventos relacionados
        parent_id: ID do evento pai (para hierarquia)
    """

    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    level: AuditLevel = AuditLevel.INFO
    category: AuditCategory = AuditCategory.SYSTEM_CONFIG

    agent_id: Optional[str] = None
    action: str = ""
    reasoning: str = ""

    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    trace_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None

    # Campos computados
    source: str = "justica"
    version: str = "3.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionario."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.name,
            "category": self.category.value,
            "agent_id": self.agent_id,
            "action": self.action,
            "reasoning": self.reasoning,
            "context": self.context,
            "metadata": self.metadata,
            "trace_id": str(self.trace_id) if self.trace_id else None,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "source": self.source,
            "version": self.version,
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serializa para JSON."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuditEntry:
        """Deserializa de dicionario."""
        return cls(
            id=UUID(data["id"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            level=AuditLevel[data["level"]],
            category=AuditCategory(data["category"]),
            agent_id=data.get("agent_id"),
            action=data.get("action", ""),
            reasoning=data.get("reasoning", ""),
            context=data.get("context", {}),
            metadata=data.get("metadata", {}),
            trace_id=UUID(data["trace_id"]) if data.get("trace_id") else None,
            parent_id=UUID(data["parent_id"]) if data.get("parent_id") else None,
            source=data.get("source", "justica"),
            version=data.get("version", "3.0.0"),
        )


__all__ = ["AuditEntry"]
