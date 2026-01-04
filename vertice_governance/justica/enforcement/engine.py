"""
Enforcement Engine - Core enforcement logic for JUSTICA.

EnforcementEngine manages action determination and execution.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from ..constitution import Constitution, Severity
from ..classifiers import ClassificationReport, ClassificationResult
from ..trust import TrustEngine
from .actions import ActionExecutor, EnforcementAction
from .policy import EnforcementPolicy
from .types import ActionType


class EnforcementEngine:
    """
    Motor de Enforcement de JUSTICA.

    Responsavel por:
    1. Determinar acoes apropriadas para cada classificacao
    2. Coordenar com Trust Engine
    3. Executar acoes de enforcement
    4. Manter historico de acoes
    5. Fornecer metricas de enforcement

    "A resposta deve ser proporcional a severidade da violacao."

    Attributes:
        constitution: Constituicao base
        trust_engine: Motor de trust
        policy: Politica de enforcement atual
        action_history: Historico de acoes
        executors: Executores registrados para cada tipo de acao
    """

    def __init__(
        self,
        constitution: Constitution,
        trust_engine: TrustEngine,
        policy: Optional[EnforcementPolicy] = None,
    ):
        self.constitution = constitution
        self.trust_engine = trust_engine
        self.policy = policy or EnforcementPolicy.default_normative()

        # History (last 10000)
        self._action_history: List[EnforcementAction] = []
        self._max_history = 10000

        # Registered executors
        self._executors: Dict[ActionType, ActionExecutor] = {}

        # Callbacks
        self._on_action_callbacks: List[Callable[[EnforcementAction], None]] = []

        # Metrics
        self.total_actions = 0
        self.total_blocks = 0
        self.total_warnings = 0
        self.total_escalations = 0

    def set_policy(self, policy: EnforcementPolicy) -> None:
        """Define a politica de enforcement."""
        self.policy = policy

    def register_executor(self, action_type: ActionType, executor: ActionExecutor) -> None:
        """Registra um executor para um tipo de acao."""
        self._executors[action_type] = executor

    def add_action_callback(self, callback: Callable[[EnforcementAction], None]) -> None:
        """Adiciona callback para ser chamado quando acoes sao executadas."""
        self._on_action_callbacks.append(callback)

    def determine_actions(
        self,
        classification: ClassificationReport,
        agent_id: str,
    ) -> List[EnforcementAction]:
        """
        Determina as acoes a serem tomadas com base na classificacao.

        Args:
            classification: Relatorio de classificacao
            agent_id: ID do agente que gerou o conteudo classificado

        Returns:
            Lista de acoes a serem executadas
        """
        actions: List[EnforcementAction] = []

        # FASE 1: Verificar Suspensao
        if self.policy.block_suspended_agents:
            is_suspended, reason = self.trust_engine.check_suspension(agent_id)
            if is_suspended:
                actions.append(EnforcementAction(
                    action_type=ActionType.BLOCK_AGENT,
                    target=agent_id,
                    reason=f"Agente suspenso: {reason}",
                    severity=Severity.CRITICAL,
                    classification_report=classification,
                ))
                return actions

        # FASE 2: Verificar Trust Level
        trust_factor = self.trust_engine.get_or_create_trust_factor(agent_id)
        # Trust logic can be extended here

        # FASE 3: Resultado SAFE - Permitir
        if classification.result == ClassificationResult.SAFE:
            self.trust_engine.record_good_action(agent_id, "Acao segura aprovada")
            actions.append(EnforcementAction(
                action_type=ActionType.ALLOW,
                target=agent_id,
                reason="Classificacao SAFE",
                severity=Severity.INFO,
                classification_report=classification,
            ))
            return actions

        # FASE 4: Resultado NEEDS_REVIEW - Escalar
        if classification.result == ClassificationResult.NEEDS_REVIEW:
            actions.append(EnforcementAction(
                action_type=ActionType.ESCALATE_TO_HUMAN,
                target=agent_id,
                reason="Classificacao ambigua requer revisao humana",
                severity=classification.severity,
                classification_report=classification,
                metadata={"detected_patterns": classification.detected_patterns},
            ))
            return actions

        # FASE 5: Violacao/Critico - Aplicar Politica
        severity = classification.severity
        action_types = list(self.policy.severity_actions.get(severity, []))

        # Add violation-specific actions
        for violation_type in classification.violation_types:
            specific_actions = self.policy.violation_actions.get(violation_type, [])
            for action_type in specific_actions:
                if action_type not in action_types:
                    action_types.append(action_type)

        # Create actions
        for action_type in action_types:
            action = EnforcementAction(
                action_type=action_type,
                target=agent_id,
                reason=classification.reasoning,
                severity=severity,
                classification_report=classification,
                metadata={
                    "violation_types": [vt.name for vt in classification.violation_types],
                    "confidence": classification.confidence,
                },
            )
            actions.append(action)

        # FASE 6: Atualizar Trust Factor
        for violation_type in classification.violation_types:
            self.trust_engine.record_violation(
                agent_id=agent_id,
                violation_type=violation_type,
                severity=severity,
                description=classification.reasoning,
                context={"classification_id": str(classification.id)},
            )

        # FASE 7: Escalacao Critica Obrigatoria
        if (
            self.policy.always_escalate_critical and
            severity == Severity.CRITICAL and
            ActionType.ESCALATE_TO_ADMIN not in action_types and
            ActionType.ESCALATE_TO_HUMAN not in action_types
        ):
            actions.append(EnforcementAction(
                action_type=ActionType.ESCALATE_TO_ADMIN,
                target=agent_id,
                reason="Violacao critica requer atencao administrativa",
                severity=Severity.CRITICAL,
                classification_report=classification,
            ))

        return actions

    def execute_actions(self, actions: List[EnforcementAction]) -> Dict[str, Any]:
        """
        Executa uma lista de acoes.

        Returns:
            Dicionario com resultados da execucao
        """
        results = {
            "total": len(actions),
            "executed": 0,
            "succeeded": 0,
            "failed": 0,
            "no_executor": 0,
            "actions": [],
        }

        for action in actions:
            executor = self._executors.get(action.action_type)

            if executor is None:
                action.mark_executed(True, "No executor - logged only")
                results["no_executor"] += 1
            else:
                try:
                    success = executor.execute(action)
                    action.mark_executed(success, "Executed by registered executor")
                    if success:
                        results["succeeded"] += 1
                    else:
                        results["failed"] += 1
                except Exception as e:
                    action.mark_executed(False, f"Error: {str(e)}")
                    results["failed"] += 1

            results["executed"] += 1
            results["actions"].append(action.to_dict())

            # Update metrics
            self._update_metrics(action)

            # Add to history
            self._add_to_history(action)

            # Notify callbacks
            self._notify_callbacks(action)

        return results

    def _update_metrics(self, action: EnforcementAction) -> None:
        """Update internal metrics."""
        self.total_actions += 1
        if action.is_blocking:
            self.total_blocks += 1
        elif action.action_type in (ActionType.WARNING, ActionType.STRONG_WARNING):
            self.total_warnings += 1
        elif action.is_escalation:
            self.total_escalations += 1

    def _add_to_history(self, action: EnforcementAction) -> None:
        """Adiciona acao ao historico."""
        self._action_history.append(action)
        if len(self._action_history) > self._max_history:
            self._action_history = self._action_history[-self._max_history:]

    def _notify_callbacks(self, action: EnforcementAction) -> None:
        """Notify registered callbacks."""
        for callback in self._on_action_callbacks:
            try:
                callback(action)
            except (TypeError, ValueError, RuntimeError):
                pass

    def process_classification(
        self,
        classification: ClassificationReport,
        agent_id: str,
        auto_execute: bool = True,
    ) -> Dict[str, Any]:
        """
        Processa uma classificacao completa: determina e executa acoes.

        Args:
            classification: Relatorio de classificacao
            agent_id: ID do agente
            auto_execute: Se deve executar automaticamente

        Returns:
            Dicionario com acoes determinadas e resultados
        """
        actions = self.determine_actions(classification, agent_id)

        result = {
            "classification_id": str(classification.id),
            "classification_result": classification.result.name,
            "agent_id": agent_id,
            "actions_determined": len(actions),
            "should_block": any(a.is_blocking for a in actions),
            "should_escalate": any(a.is_escalation for a in actions),
        }

        if auto_execute:
            execution_results = self.execute_actions(actions)
            result["execution"] = execution_results
        else:
            result["pending_actions"] = [a.to_dict() for a in actions]

        return result

    def get_recent_actions(
        self,
        limit: int = 100,
        action_type: Optional[ActionType] = None,
        agent_id: Optional[str] = None,
    ) -> List[EnforcementAction]:
        """Retorna acoes recentes com filtros opcionais."""
        actions = self._action_history

        if action_type:
            actions = [a for a in actions if a.action_type == action_type]

        if agent_id:
            actions = [a for a in actions if a.target == agent_id]

        return actions[-limit:]

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna metricas do engine."""
        return {
            "policy": self.policy.name,
            "mode": self.policy.mode.name,
            "total_actions": self.total_actions,
            "total_blocks": self.total_blocks,
            "total_warnings": self.total_warnings,
            "total_escalations": self.total_escalations,
            "block_rate": self.total_blocks / max(1, self.total_actions),
            "escalation_rate": self.total_escalations / max(1, self.total_actions),
            "history_size": len(self._action_history),
            "registered_executors": [at.name for at in self._executors.keys()],
        }

    def __repr__(self) -> str:
        return f"EnforcementEngine(policy={self.policy.name}, actions={self.total_actions})"


__all__ = ["EnforcementEngine"]
