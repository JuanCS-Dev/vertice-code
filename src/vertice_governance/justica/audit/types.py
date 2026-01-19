"""
Audit Types - Enums for the JUSTICA audit system.

AuditLevel and AuditCategory enums.
"""

from __future__ import annotations

from enum import Enum, auto


class AuditLevel(Enum):
    """Niveis de audit log."""

    DEBUG = auto()  # Informacoes de debug
    INFO = auto()  # Operacoes normais
    WARNING = auto()  # Situacoes que merecem atencao
    ERROR = auto()  # Erros que nao impedem operacao
    CRITICAL = auto()  # Situacoes criticas
    SECURITY = auto()  # Eventos de seguranca (sempre logados)


class AuditCategory(Enum):
    """Categorias de eventos de auditoria."""

    # Classificacao
    CLASSIFICATION_INPUT = "classification.input"
    CLASSIFICATION_OUTPUT = "classification.output"
    CLASSIFICATION_RESULT = "classification.result"

    # Enforcement
    ENFORCEMENT_ACTION = "enforcement.action"
    ENFORCEMENT_BLOCK = "enforcement.block"
    ENFORCEMENT_WARNING = "enforcement.warning"
    ENFORCEMENT_ESCALATION = "enforcement.escalation"

    # Trust
    TRUST_UPDATE = "trust.update"
    TRUST_VIOLATION = "trust.violation"
    TRUST_SUSPENSION = "trust.suspension"
    TRUST_RECOVERY = "trust.recovery"

    # Monitoring
    MONITOR_EVENT = "monitor.event"
    MONITOR_SUSPICION = "monitor.suspicion"
    MONITOR_VIOLATION = "monitor.violation"
    MONITOR_CROSSAGENT = "monitor.crossagent"

    # System
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_CONFIG = "system.config"
    SYSTEM_ERROR = "system.error"

    # Human
    HUMAN_REVIEW = "human.review"
    HUMAN_DECISION = "human.decision"
    HUMAN_OVERRIDE = "human.override"


__all__ = [
    "AuditLevel",
    "AuditCategory",
]
