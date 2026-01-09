"""
Trust Engine - Core trust management for multi-agent systems.

TrustEngine manages trust factors for all agents in the system.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..constitution import Severity, ViolationType
from .events import TrustEvent
from .factor import TrustFactor
from .types import AuthorizationContext, AuthorizationLevel, TrustLevel

logger = logging.getLogger(__name__)


class TrustEngine:
    """
    Motor de Trust Factor que gerencia a confianca em todos os agentes.

    Responsabilidades:
    1. Calcular e atualizar trust factors
    2. Registrar eventos que afetam confianca
    3. Aplicar decaimento temporal
    4. Gerenciar suspensoes
    5. Fornecer metricas de confianca

    "Confianca e conquistada lentamente e perdida rapidamente."

    Configuracoes importantes:
    - violation_weights: Peso de cada tipo de violacao
    - severity_multipliers: Multiplicador por severidade
    - recovery_rate: Taxa de recuperacao apos boas acoes
    - decay_halflife: Meia-vida do decaimento de violacoes antigas
    """

    # Pesos padrao para tipos de violacao
    DEFAULT_VIOLATION_WEIGHTS: Dict[ViolationType, float] = {
        ViolationType.DATA_EXFILTRATION: 0.30,
        ViolationType.MALICIOUS_CODE: 0.35,
        ViolationType.PRIVILEGE_ESCALATION: 0.25,
        ViolationType.SECURITY_BYPASS: 0.25,
        ViolationType.PROMPT_INJECTION: 0.20,
        ViolationType.JAILBREAK_ATTEMPT: 0.20,
        ViolationType.INSTRUCTION_OVERRIDE: 0.15,
        ViolationType.SCOPE_VIOLATION: 0.15,
        ViolationType.ROLE_VIOLATION: 0.10,
        ViolationType.CODE_INJECTION: 0.25,
        ViolationType.UNAUTHORIZED_DATA_ACCESS: 0.20,
        ViolationType.DATA_MANIPULATION: 0.25,
        ViolationType.AUTHENTICATION_BYPASS: 0.30,
        ViolationType.RESOURCE_ABUSE: 0.10,
        ViolationType.DEPENDENCY_POISONING: 0.30,
        ViolationType.MALICIOUS_COORDINATION: 0.35,
        ViolationType.COVERT_COMMUNICATION: 0.20,
        ViolationType.COLLECTIVE_BYPASS: 0.30,
        ViolationType.UNKNOWN: 0.10,
    }

    # Multiplicadores de severidade
    SEVERITY_MULTIPLIERS: Dict[Severity, float] = {
        Severity.CRITICAL: 2.0,
        Severity.HIGH: 1.5,
        Severity.MEDIUM: 1.0,
        Severity.LOW: 0.5,
        Severity.INFO: 0.1,
    }

    # Minimum authorization levels for sensitive operations
    LIFT_SUSPENSION_MIN_LEVEL = AuthorizationLevel.ADMIN
    CRITICAL_SUSPENSION_MIN_LEVEL = AuthorizationLevel.RSO

    def __init__(
        self,
        violation_weights: Optional[Dict[ViolationType, float]] = None,
        severity_multipliers: Optional[Dict[Severity, float]] = None,
        recovery_rate: float = 0.005,
        decay_halflife_days: float = 30.0,
        good_action_threshold: int = 10,
        auto_suspend_threshold: float = 0.20,
        critical_violation_suspension_hours: int = 24,
    ):
        self.violation_weights = violation_weights or self.DEFAULT_VIOLATION_WEIGHTS.copy()
        self.severity_multipliers = severity_multipliers or self.SEVERITY_MULTIPLIERS.copy()
        self.recovery_rate = recovery_rate
        self.decay_halflife_days = decay_halflife_days
        self.good_action_threshold = good_action_threshold
        self.auto_suspend_threshold = auto_suspend_threshold
        self.critical_violation_suspension_hours = critical_violation_suspension_hours

        # Storage of trust factors by agent
        self._trust_factors: Dict[str, TrustFactor] = {}

        # Global metrics
        self.total_events_processed = 0
        self.total_suspensions = 0

    def get_or_create_trust_factor(self, agent_id: str) -> TrustFactor:
        """Obtem ou cria um TrustFactor para um agente."""
        if agent_id not in self._trust_factors:
            self._trust_factors[agent_id] = TrustFactor(agent_id=agent_id)
        return self._trust_factors[agent_id]

    def get_trust_factor(self, agent_id: str) -> Optional[TrustFactor]:
        """Obtem o TrustFactor de um agente (None se nao existir)."""
        return self._trust_factors.get(agent_id)

    def record_violation(
        self,
        agent_id: str,
        violation_type: ViolationType,
        severity: Severity,
        description: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> TrustEvent:
        """
        Registra uma violacao e atualiza o trust factor.

        Args:
            agent_id: ID do agente
            violation_type: Tipo de violacao
            severity: Severidade
            description: Descricao
            context: Contexto adicional

        Returns:
            TrustEvent registrado
        """
        trust_factor = self.get_or_create_trust_factor(agent_id)

        # Calculate impact
        base_weight = self.violation_weights.get(violation_type, 0.1)
        severity_mult = self.severity_multipliers.get(severity, 1.0)
        impact = -(base_weight * severity_mult)

        # Create event
        event = TrustEvent(
            event_type="violation",
            violation_type=violation_type,
            severity=severity,
            impact=impact,
            description=description,
            context=context or {},
        )

        # Apply event
        self._apply_event(trust_factor, event)

        # Check if should suspend
        if severity == Severity.CRITICAL:
            self._suspend_agent(
                trust_factor,
                reason=f"Violacao critica: {violation_type.name}",
                duration_hours=self.critical_violation_suspension_hours,
            )
        elif trust_factor.current_factor < self.auto_suspend_threshold:
            self._suspend_agent(
                trust_factor,
                reason=f"Trust factor abaixo do threshold ({trust_factor.current_factor:.2f})",
                duration_hours=48,
            )

        self.total_events_processed += 1
        return event

    def record_good_action(
        self,
        agent_id: str,
        description: str = "Acao bem-sucedida",
        context: Optional[Dict[str, Any]] = None,
    ) -> TrustEvent:
        """
        Registra uma acao bem-sucedida e atualiza o trust factor.

        Acoes boas aumentam o trust factor gradualmente.
        Multiplas acoes boas consecutivas dao bonus adicional.
        """
        trust_factor = self.get_or_create_trust_factor(agent_id)

        # Calculate impact
        impact = self.recovery_rate

        # Bonus for consecutive actions
        if trust_factor.consecutive_good_actions >= self.good_action_threshold:
            bonus = 0.001 * (trust_factor.consecutive_good_actions - self.good_action_threshold + 1)
            impact += min(bonus, 0.01)

        event = TrustEvent(
            event_type="good_action",
            severity=Severity.INFO,
            impact=impact,
            description=description,
            context=context or {},
        )

        self._apply_event(trust_factor, event)
        trust_factor.consecutive_good_actions += 1

        self.total_events_processed += 1
        return event

    def _apply_event(self, trust_factor: TrustFactor, event: TrustEvent) -> None:
        """Aplica um evento ao trust factor."""
        trust_factor.events.append(event)
        trust_factor.total_actions += 1

        if event.event_type == "violation":
            trust_factor.total_violations += 1
            trust_factor.consecutive_good_actions = 0

        # Apply impact
        new_factor = trust_factor.current_factor + event.impact
        trust_factor.current_factor = max(0.0, min(1.0, new_factor))
        trust_factor.last_updated = datetime.now(timezone.utc)

    def _suspend_agent(
        self,
        trust_factor: TrustFactor,
        reason: str,
        duration_hours: int,
    ) -> None:
        """Suspende um agente."""
        trust_factor.is_suspended = True
        trust_factor.suspension_reason = reason
        trust_factor.suspension_until = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
        self.total_suspensions += 1

        event = TrustEvent(
            event_type="suspension",
            severity=Severity.CRITICAL,
            impact=0,
            description=f"Agente suspenso: {reason}",
            context={"duration_hours": duration_hours},
        )
        trust_factor.events.append(event)

    def check_suspension(self, agent_id: str) -> Tuple[bool, Optional[str]]:
        """
        Verifica se um agente esta suspenso.

        Returns:
            Tuple de (is_suspended, reason)
        """
        trust_factor = self.get_trust_factor(agent_id)

        if trust_factor is None:
            return False, None

        # Check if suspension expired
        if trust_factor.is_suspended and trust_factor.suspension_until:
            if datetime.now(timezone.utc) > trust_factor.suspension_until:
                trust_factor.is_suspended = False
                trust_factor.suspension_reason = None
                trust_factor.suspension_until = None
                return False, None

        return trust_factor.is_suspended, trust_factor.suspension_reason

    def lift_suspension(
        self,
        agent_id: str,
        auth_context: AuthorizationContext,
    ) -> bool:
        """
        Remove suspensao de um agente com autorizacao obrigatoria.

        Following Anthropic's two-party authorization pattern (2026).

        Args:
            agent_id: ID do agente
            auth_context: Authorization context with principal and level

        Returns:
            True se suspensao foi removida

        Raises:
            PermissionError: Se autorizacao insuficiente
            ValueError: Se auth_context invalido
        """
        if auth_context is None:
            raise ValueError(
                "AuthorizationContext required. "
                "lift_suspension() is a sensitive operation that requires explicit authorization."
            )

        trust_factor = self.get_trust_factor(agent_id)

        if trust_factor is None or not trust_factor.is_suspended:
            return False

        # Determine required authorization level
        was_critical_suspension = (
            trust_factor.suspension_reason and
            "critica" in trust_factor.suspension_reason.lower()
        )

        required_level = (
            self.CRITICAL_SUSPENSION_MIN_LEVEL if was_critical_suspension
            else self.LIFT_SUSPENSION_MIN_LEVEL
        )

        # Check authorization level
        if auth_context.level.value < required_level.value:
            logger.warning(
                f"Authorization denied for lift_suspension on {agent_id}. "
                f"Required: {required_level.name}, Got: {auth_context.level.name}, "
                f"Principal: {auth_context.principal}"
            )
            raise PermissionError(
                f"Insufficient authorization to lift suspension. "
                f"Required: {required_level.name}, Got: {auth_context.level.name}."
            )

        # Log authorization
        logger.info(
            f"Suspension lift authorized for {agent_id}. "
            f"Principal: {auth_context.principal}, Level: {auth_context.level.name}"
        )

        # Apply change
        trust_factor.is_suspended = False
        old_reason = trust_factor.suspension_reason
        trust_factor.suspension_reason = None
        trust_factor.suspension_until = None

        # Record event
        event = TrustEvent(
            event_type="suspension_lifted",
            severity=Severity.INFO,
            impact=0,
            description=f"Suspensao removida por {auth_context.principal}: {auth_context.reason}",
            context={
                "authorization": auth_context.to_dict(),
                "previous_suspension_reason": old_reason,
            },
        )
        trust_factor.events.append(event)

        return True

    def apply_temporal_decay(self, agent_id: str) -> float:
        """
        Aplica decaimento temporal as violacoes antigas.

        Violacoes antigas tem menos peso no calculo.
        Retorna o novo trust factor apos decaimento.
        """
        trust_factor = self.get_trust_factor(agent_id)

        if trust_factor is None:
            return 1.0

        now = datetime.now(timezone.utc)
        total_impact = 0.0

        for event in trust_factor.events:
            if event.impact < 0:
                age_days = (now - event.timestamp).total_seconds() / 86400
                decay_factor = math.pow(0.5, age_days / self.decay_halflife_days)
                total_impact += event.impact * decay_factor

        new_factor = max(0.0, min(1.0, 1.0 + total_impact))
        trust_factor.current_factor = (trust_factor.current_factor + new_factor) / 2
        trust_factor.last_updated = now

        return trust_factor.current_factor

    def get_all_agents(self) -> List[str]:
        """Retorna lista de todos os agentes monitorados."""
        return list(self._trust_factors.keys())

    def get_agents_by_level(self, level: TrustLevel) -> List[str]:
        """Retorna agentes em um determinado nivel de confianca."""
        return [
            agent_id
            for agent_id, tf in self._trust_factors.items()
            if tf.level == level
        ]

    def get_suspended_agents(self) -> List[Tuple[str, str]]:
        """Retorna lista de (agent_id, reason) para agentes suspensos."""
        return [
            (agent_id, tf.suspension_reason or "Unknown")
            for agent_id, tf in self._trust_factors.items()
            if tf.is_suspended
        ]

    def get_global_metrics(self) -> Dict[str, Any]:
        """Retorna metricas globais do Trust Engine."""
        all_factors = list(self._trust_factors.values())

        if not all_factors:
            return {
                "total_agents": 0,
                "total_events": self.total_events_processed,
                "total_suspensions": self.total_suspensions,
            }

        factors = [tf.current_factor for tf in all_factors]

        return {
            "total_agents": len(all_factors),
            "total_events": self.total_events_processed,
            "total_suspensions": self.total_suspensions,
            "average_trust_factor": sum(factors) / len(factors),
            "min_trust_factor": min(factors),
            "max_trust_factor": max(factors),
            "agents_by_level": {
                level.name: len(self.get_agents_by_level(level))
                for level in TrustLevel
            },
            "suspended_count": len([tf for tf in all_factors if tf.is_suspended]),
        }

    def __repr__(self) -> str:
        metrics = self.get_global_metrics()
        return f"TrustEngine(agents={metrics['total_agents']}, events={metrics['total_events']})"


__all__ = ["TrustEngine"]
