"""
JUSTICA Agent Types - Data structures for the JUSTICA agent.

JusticaState, JusticaConfig, and JusticaVerdict dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ..constitution import Severity
from ..classifiers import ClassificationReport
from ..enforcement import EnforcementAction, EnforcementMode
from ..monitor import SuspicionScore
from ..trust import TrustFactor


class JusticaState(Enum):
    """Estados possiveis do agente JUSTICA."""

    INITIALIZING = auto()   # Inicializando componentes
    READY = auto()          # Pronto para operar
    MONITORING = auto()     # Em modo de monitoramento ativo
    INVESTIGATING = auto()  # Investigando incidente
    SUSPENDED = auto()      # Suspenso (requer intervencao humana)
    SHUTDOWN = auto()       # Desligado


@dataclass
class JusticaConfig:
    """
    Configuracao do Agente JUSTICA.

    Permite customizacao de todos os parametros do sistema.
    """

    # Identificacao
    agent_id: str = "justica-primary"
    name: str = "JUSTICA"
    version: str = "3.0.0"

    # Politicas
    enforcement_mode: EnforcementMode = EnforcementMode.NORMATIVE

    # Thresholds
    violation_threshold: float = 80.0
    auto_suspend_threshold: float = 0.20
    critical_alert_threshold: float = 90.0

    # Monitoramento
    analysis_window_minutes: int = 30
    cross_agent_correlation_minutes: int = 5

    # Logging
    log_dir: Optional[Path] = None
    console_logging: bool = True
    file_logging: bool = True

    # Comportamento
    auto_execute_enforcement: bool = True
    require_human_for_critical: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "enforcement_mode": self.enforcement_mode.name,
            "violation_threshold": self.violation_threshold,
            "auto_suspend_threshold": self.auto_suspend_threshold,
            "critical_alert_threshold": self.critical_alert_threshold,
            "analysis_window_minutes": self.analysis_window_minutes,
            "cross_agent_correlation_minutes": self.cross_agent_correlation_minutes,
            "console_logging": self.console_logging,
            "file_logging": self.file_logging,
            "auto_execute_enforcement": self.auto_execute_enforcement,
            "require_human_for_critical": self.require_human_for_critical,
        }


@dataclass
class JusticaVerdict:
    """
    Veredicto de JUSTICA sobre uma acao ou agente.

    Contem a decisao completa com todas as evidencias e raciocinio.
    """

    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Sujeito do veredicto
    agent_id: str = ""
    content_analyzed: str = ""

    # Decisao
    approved: bool = True
    requires_human_review: bool = False

    # Evidencias
    classification: Optional[ClassificationReport] = None
    suspicion_score: Optional[SuspicionScore] = None
    trust_factor: Optional[TrustFactor] = None

    # Acoes tomadas
    actions_taken: List[EnforcementAction] = field(default_factory=list)

    # Raciocinio
    reasoning: str = ""
    constitutional_basis: List[str] = field(default_factory=list)

    # Metadados
    processing_time_ms: float = 0.0

    @property
    def is_violation(self) -> bool:
        """Verifica se o veredicto indica violacao."""
        return not self.approved and not self.requires_human_review

    @property
    def severity(self) -> Severity:
        """Retorna a severidade do veredicto."""
        if self.classification:
            return self.classification.severity
        return Severity.INFO

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "content_preview": (
                self.content_analyzed[:200] + "..."
                if len(self.content_analyzed) > 200
                else self.content_analyzed
            ),
            "approved": self.approved,
            "requires_human_review": self.requires_human_review,
            "is_violation": self.is_violation,
            "severity": self.severity.name,
            "classification_result": (
                self.classification.result.name if self.classification else None
            ),
            "suspicion_score": (
                self.suspicion_score.score if self.suspicion_score else None
            ),
            "trust_level": (
                self.trust_factor.level.name if self.trust_factor else None
            ),
            "actions_count": len(self.actions_taken),
            "reasoning": self.reasoning,
            "constitutional_basis": self.constitutional_basis,
            "processing_time_ms": self.processing_time_ms,
        }


__all__ = [
    "JusticaState",
    "JusticaConfig",
    "JusticaVerdict",
]
