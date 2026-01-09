"""
Enforcement Actions - Action data structures.

EnforcementAction dataclass and ActionExecutor protocol.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Protocol
from uuid import UUID, uuid4

from ..constitution import Severity
from ..classifiers import ClassificationReport
from .types import ActionType


class ActionExecutor(Protocol):
    """Protocolo para executores de acoes."""

    def execute(self, action: EnforcementAction) -> bool:
        """Executa uma acao e retorna True se bem-sucedida."""
        ...


@dataclass
class EnforcementAction:
    """
    Uma acao de enforcement a ser executada.

    Attributes:
        id: Identificador unico
        action_type: Tipo da acao
        target: Alvo da acao (agent_id, tool_name, resource_id, etc.)
        reason: Razao para a acao
        severity: Severidade da violacao que causou a acao
        classification_report: Relatorio de classificacao associado
        metadata: Dados adicionais
        created_at: Timestamp de criacao
        executed_at: Timestamp de execucao (None se nao executada)
        success: Se a acao foi bem-sucedida (None se nao executada)
    """

    id: UUID = field(default_factory=uuid4)
    action_type: ActionType = ActionType.LOG_INFO
    target: str = ""
    reason: str = ""
    severity: Severity = Severity.INFO
    classification_report: Optional[ClassificationReport] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: Optional[datetime] = None
    success: Optional[bool] = None
    execution_result: Optional[str] = None

    def mark_executed(self, success: bool, result: str = "") -> None:
        """Marca a acao como executada."""
        self.executed_at = datetime.now(timezone.utc)
        self.success = success
        self.execution_result = result

    @property
    def is_executed(self) -> bool:
        """Check if action has been executed."""
        return self.executed_at is not None

    @property
    def is_blocking(self) -> bool:
        """Check if this is a blocking action."""
        return self.action_type in (
            ActionType.BLOCK_REQUEST,
            ActionType.BLOCK_AGENT,
            ActionType.BLOCK_TOOL,
            ActionType.BLOCK_RESOURCE,
        )

    @property
    def is_escalation(self) -> bool:
        """Check if this is an escalation action."""
        return self.action_type in (
            ActionType.ESCALATE_TO_HUMAN,
            ActionType.ESCALATE_TO_ADMIN,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "action_type": self.action_type.name,
            "target": self.target,
            "reason": self.reason,
            "severity": self.severity.name,
            "classification_report_id": (
                str(self.classification_report.id) if self.classification_report else None
            ),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "success": self.success,
            "execution_result": self.execution_result,
        }


__all__ = [
    "ActionExecutor",
    "EnforcementAction",
]
