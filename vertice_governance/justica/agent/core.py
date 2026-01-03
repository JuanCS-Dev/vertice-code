"""
JUSTICA Agent Core - Main agent orchestrator.

The JusticaAgent coordinates all governance subsystems.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from ..audit import AuditLevel, create_test_logger
from ..classifiers import ConstitutionalClassifier
from ..constitution import Constitution, create_default_constitution
from ..enforcement import (
    ActionType,
    ConsoleExecutor,
    EnforcementAction,
    EnforcementEngine,
    EnforcementMode,
    EnforcementPolicy,
)
from ..monitor import JusticaMonitor
from ..trust import TrustEngine
from .evaluator import VerdictEvaluator
from .types import JusticaConfig, JusticaState, JusticaVerdict


JUSTICA_BANNER = """
JUSTICA - Sistema de Governanca Multi-Agente
Versao 3.0.0 (2030 Vision)
"Vigilancia sem paranoia. Proporcionalidade. Transparencia."
"""


class JusticaAgent:
    """
    O supervisor que protege a integridade de sistemas multi-agente.

    JUSTICA coordena todos os subsistemas de governanca:
    - Constitution: Principios fundamentais
    - Classifier: Deteccao de violacoes
    - TrustEngine: Gestao de confianca
    - EnforcementEngine: Aplicacao de politicas
    - Monitor: Monitoramento em tempo real
    - AuditLogger: Transparencia total

    Attributes:
        config: Configuracao do agente
        state: Estado atual
        constitution: Principios fundamentais
        classifier: Classificador constitucional
        trust_engine: Motor de confianca
        enforcement_engine: Motor de enforcement
        monitor: Monitor em tempo real
        audit_logger: Logger de auditoria
    """

    def __init__(
        self,
        config: Optional[JusticaConfig] = None,
        constitution: Optional[Constitution] = None,
    ):
        """
        Inicializa o Agente JUSTICA.

        Args:
            config: Configuracao customizada (usa default se nao fornecida)
            constitution: Constituicao customizada (usa default se nao fornecida)
        """
        self.config = config or JusticaConfig()
        self.state = JusticaState.INITIALIZING
        self.started_at: Optional[datetime] = None

        # Initialize components
        self._init_components(constitution)

        # Initialize callbacks
        self._on_violation_callbacks: List[Callable[[JusticaVerdict], None]] = []
        self._on_escalation_callbacks: List[Callable[[JusticaVerdict], None]] = []

        # Initialize metrics
        self.total_verdicts = 0
        self.total_approvals = 0
        self.total_violations = 0
        self.total_escalations = 0

        # Mark as ready
        self.state = JusticaState.READY

    def _init_components(self, constitution: Optional[Constitution]) -> None:
        """Initialize all governance components."""
        # 1. Constitution
        self.constitution = constitution or create_default_constitution()

        # 2. Classifier
        self.classifier = ConstitutionalClassifier(self.constitution)

        # 3. Trust Engine
        self.trust_engine = TrustEngine(
            auto_suspend_threshold=self.config.auto_suspend_threshold,
        )

        # 4. Enforcement Engine
        policy = self._create_enforcement_policy()
        self.enforcement_engine = EnforcementEngine(
            constitution=self.constitution,
            trust_engine=self.trust_engine,
            policy=policy,
        )

        # 5. Monitor
        self.monitor = JusticaMonitor(
            constitution=self.constitution,
            violation_threshold=self.config.violation_threshold,
            analysis_window_minutes=self.config.analysis_window_minutes,
            cross_agent_correlation_window_minutes=self.config.cross_agent_correlation_minutes,
        )

        # 6. Audit Logger
        self.audit_logger, self._memory_backend = create_test_logger()

        # 7. Evaluator
        self._evaluator = VerdictEvaluator(
            require_human_for_critical=self.config.require_human_for_critical
        )

        # Register default executors
        self._register_default_executors()

    def _create_enforcement_policy(self) -> EnforcementPolicy:
        """Cria politica de enforcement baseada na configuracao."""
        mode = self.config.enforcement_mode

        if mode == EnforcementMode.COERCIVE:
            return EnforcementPolicy.default_coercive()
        elif mode == EnforcementMode.ADAPTIVE:
            return EnforcementPolicy.default_adaptive()
        else:
            return EnforcementPolicy.default_normative()

    def _register_default_executors(self) -> None:
        """Registra executores padrao para acoes de enforcement."""
        executor = ConsoleExecutor()
        for action_type in ActionType:
            self.enforcement_engine.register_executor(action_type, executor)

    def start(self) -> None:
        """
        Inicia o Agente JUSTICA.

        Loga evento de inicializacao e entra em modo de monitoramento.
        """
        print(JUSTICA_BANNER)

        self.started_at = datetime.now(timezone.utc)
        self.state = JusticaState.MONITORING

        self.audit_logger.log_system_event(
            event="JUSTICA Started",
            details=self.config.to_dict(),
            level=AuditLevel.INFO,
        )

        print(f"\n+ JUSTICA iniciado em {self.started_at.isoformat()}")
        print(f"+ Modo de enforcement: {self.config.enforcement_mode.name}")
        print(f"+ Threshold de violacao: {self.config.violation_threshold}")
        print(
            f"+ Constituicao: {self.constitution.version} "
            f"({len(self.constitution.get_all_principles())} principios)"
        )

    def stop(self) -> None:
        """Para o Agente JUSTICA."""
        self.state = JusticaState.SHUTDOWN

        uptime = 0.0
        if self.started_at:
            uptime = (datetime.now(timezone.utc) - self.started_at).total_seconds()

        self.audit_logger.log_system_event(
            event="JUSTICA Shutdown",
            details={"uptime_seconds": uptime},
            level=AuditLevel.INFO,
        )

        self.audit_logger.close()
        print("\n+ JUSTICA encerrado.")

    def evaluate_input(
        self,
        agent_id: str,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> JusticaVerdict:
        """
        Avalia um input antes de ser processado.

        Esta e a principal funcao de gatekeeping - todo input de agentes
        deve passar por esta avaliacao.

        Args:
            agent_id: ID do agente que enviou o input
            content: Conteudo do input
            context: Contexto adicional

        Returns:
            JusticaVerdict com a decisao e acoes tomadas
        """
        start_time = time.time()
        context = context or {}

        # FASE 1: CLASSIFICACAO
        classification = self.classifier.classify_input(content, context)

        # FASE 2: MONITORAMENTO
        thoughts = context.get("thoughts")
        suspicion = self.monitor.monitor_agent(
            agent_id=agent_id,
            transcript=content,
            thoughts=thoughts,
        )

        # FASE 3: VERIFICACAO DE TRUST
        trust_factor = self.trust_engine.get_or_create_trust_factor(agent_id)
        is_suspended, suspension_reason = self.trust_engine.check_suspension(agent_id)

        # FASE 4: DETERMINACAO DO VEREDICTO
        verdict = self._evaluator.determine_verdict(
            agent_id=agent_id,
            content=content,
            classification=classification,
            suspicion=suspicion,
            trust_factor=trust_factor,
            is_suspended=is_suspended,
            suspension_reason=suspension_reason,
        )

        # FASE 5: ENFORCEMENT
        self._apply_enforcement(verdict, classification, agent_id)

        # FASE 6: LOGGING E CALLBACKS
        verdict.processing_time_ms = (time.time() - start_time) * 1000
        self._log_verdict(verdict)
        self._update_metrics(verdict)
        self._trigger_callbacks(verdict)

        return verdict

    def evaluate_output(
        self,
        agent_id: str,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> JusticaVerdict:
        """
        Avalia um output antes de ser entregue.

        Args:
            agent_id: ID do agente que gerou o output
            content: Conteudo do output
            context: Contexto adicional

        Returns:
            JusticaVerdict com a decisao
        """
        start_time = time.time()
        context = context or {}

        # Classificar output
        classification = self.classifier.classify_output(content, context)

        # Obter trust factor
        trust_factor = self.trust_engine.get_or_create_trust_factor(agent_id)

        # Determinar veredicto
        verdict = self._evaluator.determine_verdict(
            agent_id=agent_id,
            content=content,
            classification=classification,
            suspicion=None,
            trust_factor=trust_factor,
            is_suspended=False,
            suspension_reason=None,
        )

        # Enforcement se necessario
        if not verdict.approved:
            self.enforcement_engine.process_classification(
                classification=classification,
                agent_id=agent_id,
                auto_execute=self.config.auto_execute_enforcement,
            )

        verdict.processing_time_ms = (time.time() - start_time) * 1000
        self._log_verdict(verdict, is_output=True)
        self._update_metrics(verdict)

        return verdict

    def _apply_enforcement(
        self,
        verdict: JusticaVerdict,
        classification: Any,
        agent_id: str,
    ) -> None:
        """Apply enforcement actions if needed."""
        if not verdict.approved or verdict.requires_human_review:
            enforcement_result = self.enforcement_engine.process_classification(
                classification=classification,
                agent_id=agent_id,
                auto_execute=self.config.auto_execute_enforcement,
            )

            if "execution" in enforcement_result:
                for action_dict in enforcement_result["execution"].get("actions", []):
                    action = EnforcementAction(
                        action_type=ActionType[action_dict["action_type"]],
                        target=action_dict["target"],
                        reason=action_dict["reason"],
                    )
                    verdict.actions_taken.append(action)

    def _log_verdict(self, verdict: JusticaVerdict, is_output: bool = False) -> None:
        """Loga o veredicto no audit trail."""
        self.audit_logger.log_classification(
            agent_id=verdict.agent_id,
            input_or_output="output" if is_output else "input",
            result=verdict.classification.result.name if verdict.classification else "UNKNOWN",
            confidence=verdict.classification.confidence if verdict.classification else 0,
            reasoning=verdict.reasoning,
            violations=[
                vt.name for vt in verdict.classification.violation_types
            ] if verdict.classification else [],
        )

    def _update_metrics(self, verdict: JusticaVerdict) -> None:
        """Atualiza metricas internas."""
        self.total_verdicts += 1

        if verdict.approved:
            self.total_approvals += 1
        elif verdict.is_violation:
            self.total_violations += 1

        if verdict.requires_human_review:
            self.total_escalations += 1

    def _trigger_callbacks(self, verdict: JusticaVerdict) -> None:
        """Dispara callbacks registrados."""
        if verdict.is_violation:
            for callback in self._on_violation_callbacks:
                try:
                    callback(verdict)
                except Exception:
                    pass

        if verdict.requires_human_review:
            for callback in self._on_escalation_callbacks:
                try:
                    callback(verdict)
                except Exception:
                    pass

    # Callback registration API
    def on_violation(self, callback: Callable[[JusticaVerdict], None]) -> None:
        """Registra callback para violacoes."""
        self._on_violation_callbacks.append(callback)

    def on_escalation(self, callback: Callable[[JusticaVerdict], None]) -> None:
        """Registra callback para escalacoes."""
        self._on_escalation_callbacks.append(callback)

    # Query API
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Retorna status completo de um agente."""
        trust_factor = self.trust_engine.get_trust_factor(agent_id)
        session = self.monitor.get_or_create_session(agent_id)
        is_suspended, reason = self.trust_engine.check_suspension(agent_id)

        return {
            "agent_id": agent_id,
            "trust_factor": trust_factor.current_factor if trust_factor else 1.0,
            "trust_level": trust_factor.level.name if trust_factor else "MAXIMUM",
            "is_suspended": is_suspended,
            "suspension_reason": reason,
            "total_events": session.total_events,
            "flagged_events": session.flagged_events,
            "current_suspicion": session.current_suspicion,
            "violation_rate": trust_factor.violation_rate if trust_factor else 0,
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna metricas completas do sistema."""
        uptime = 0.0
        if self.started_at:
            uptime = (datetime.now(timezone.utc) - self.started_at).total_seconds()

        return {
            "justica": {
                "state": self.state.name,
                "uptime_seconds": uptime,
                "total_verdicts": self.total_verdicts,
                "total_approvals": self.total_approvals,
                "total_violations": self.total_violations,
                "total_escalations": self.total_escalations,
                "approval_rate": self.total_approvals / max(1, self.total_verdicts),
                "violation_rate": self.total_violations / max(1, self.total_verdicts),
                "escalation_rate": self.total_escalations / max(1, self.total_verdicts),
            },
            "classifier": self.classifier.get_metrics(),
            "trust_engine": self.trust_engine.get_global_metrics(),
            "enforcement": self.enforcement_engine.get_metrics(),
            "monitor": self.monitor.get_metrics(),
            "audit": self.audit_logger.get_metrics(),
        }

    def get_constitution_hash(self) -> str:
        """Retorna hash da constituicao para verificacao de integridade."""
        return self.constitution.integrity_hash

    def __repr__(self) -> str:
        return f"JusticaAgent(state={self.state.name}, verdicts={self.total_verdicts})"


__all__ = ["JusticaAgent", "JUSTICA_BANNER"]
