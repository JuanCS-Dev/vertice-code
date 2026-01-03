"""
Enforcement Policy - Policy configuration for enforcement.

EnforcementPolicy dataclass with factory methods for different modes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from ..constitution import Severity, ViolationType
from ..trust import TrustLevel
from .types import ActionType, EnforcementMode


@dataclass
class EnforcementPolicy:
    """
    Politica de enforcement que mapeia severidades para acoes.

    Define como JUSTICA deve responder a cada nivel de severidade.
    """

    name: str
    mode: EnforcementMode

    # Mapeamento severidade -> lista de acoes
    severity_actions: Dict[Severity, List[ActionType]] = field(default_factory=dict)

    # Acoes adicionais por tipo de violacao
    violation_actions: Dict[ViolationType, List[ActionType]] = field(default_factory=dict)

    # Trust level minimo para permitir acoes
    min_trust_level: TrustLevel = TrustLevel.STANDARD

    # Se deve sempre escalar violacoes criticas
    always_escalate_critical: bool = True

    # Se deve bloquear agentes suspensos automaticamente
    block_suspended_agents: bool = True

    @classmethod
    def default_coercive(cls) -> EnforcementPolicy:
        """Politica coerciva padrao - maxima seguranca."""
        return cls(
            name="Coercive Default",
            mode=EnforcementMode.COERCIVE,
            severity_actions={
                Severity.CRITICAL: [
                    ActionType.BLOCK_REQUEST,
                    ActionType.SUSPEND_AGENT,
                    ActionType.ESCALATE_TO_ADMIN,
                    ActionType.LOG_CRITICAL,
                ],
                Severity.HIGH: [
                    ActionType.BLOCK_REQUEST,
                    ActionType.REDUCE_TRUST,
                    ActionType.LOG_ERROR,
                ],
                Severity.MEDIUM: [
                    ActionType.BLOCK_REQUEST,
                    ActionType.STRONG_WARNING,
                    ActionType.LOG_WARNING,
                ],
                Severity.LOW: [
                    ActionType.WARNING,
                    ActionType.LOG_INFO,
                ],
                Severity.INFO: [
                    ActionType.LOG_INFO,
                ],
            },
            always_escalate_critical=True,
            block_suspended_agents=True,
        )

    @classmethod
    def default_normative(cls) -> EnforcementPolicy:
        """Politica normativa padrao - balanceada."""
        return cls(
            name="Normative Default",
            mode=EnforcementMode.NORMATIVE,
            severity_actions={
                Severity.CRITICAL: [
                    ActionType.BLOCK_REQUEST,
                    ActionType.ESCALATE_TO_HUMAN,
                    ActionType.LOG_CRITICAL,
                ],
                Severity.HIGH: [
                    ActionType.BLOCK_REQUEST,
                    ActionType.STRONG_WARNING,
                    ActionType.LOG_ERROR,
                ],
                Severity.MEDIUM: [
                    ActionType.WARNING,
                    ActionType.INCREASE_MONITORING,
                    ActionType.LOG_WARNING,
                ],
                Severity.LOW: [
                    ActionType.FLAG_FOR_REVIEW,
                    ActionType.LOG_INFO,
                ],
                Severity.INFO: [
                    ActionType.ALLOW_WITH_LOGGING,
                ],
            },
            always_escalate_critical=True,
            block_suspended_agents=True,
        )

    @classmethod
    def default_adaptive(cls) -> EnforcementPolicy:
        """Politica adaptiva padrao - baseada em padroes."""
        return cls(
            name="Adaptive Default",
            mode=EnforcementMode.ADAPTIVE,
            severity_actions={
                Severity.CRITICAL: [
                    ActionType.BLOCK_REQUEST,
                    ActionType.ESCALATE_TO_HUMAN,
                    ActionType.LOG_CRITICAL,
                ],
                Severity.HIGH: [
                    ActionType.STRONG_WARNING,
                    ActionType.INCREASE_MONITORING,
                    ActionType.LOG_ERROR,
                ],
                Severity.MEDIUM: [
                    ActionType.WARNING,
                    ActionType.LOG_WARNING,
                ],
                Severity.LOW: [
                    ActionType.ALLOW_WITH_LOGGING,
                ],
                Severity.INFO: [
                    ActionType.ALLOW,
                ],
            },
            violation_actions={
                ViolationType.DATA_EXFILTRATION: [
                    ActionType.BLOCK_REQUEST,
                    ActionType.SUSPEND_AGENT,
                    ActionType.ESCALATE_TO_ADMIN,
                ],
                ViolationType.MALICIOUS_COORDINATION: [
                    ActionType.BLOCK_AGENT,
                    ActionType.ESCALATE_TO_ADMIN,
                ],
            },
            always_escalate_critical=False,
            block_suspended_agents=True,
        )

    @classmethod
    def default_passive(cls) -> EnforcementPolicy:
        """Politica passiva - apenas observacao (debug/desenvolvimento)."""
        return cls(
            name="Passive Debug",
            mode=EnforcementMode.PASSIVE,
            severity_actions={
                Severity.CRITICAL: [ActionType.LOG_CRITICAL],
                Severity.HIGH: [ActionType.LOG_ERROR],
                Severity.MEDIUM: [ActionType.LOG_WARNING],
                Severity.LOW: [ActionType.LOG_INFO],
                Severity.INFO: [ActionType.ALLOW],
            },
            always_escalate_critical=False,
            block_suspended_agents=False,
        )


__all__ = ["EnforcementPolicy"]
