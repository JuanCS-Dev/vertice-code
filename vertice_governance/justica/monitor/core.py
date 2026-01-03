"""
Monitor Core - JusticaMonitor main class.

The monitor analyzes agent behavior in real-time.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from ..constitution import Constitution
from .events import MonitoringEvent
from .patterns import PATTERN_WEIGHTS, SUSPICIOUS_PATTERNS
from .session import AgentSession
from .types import SuspicionScore


class JusticaMonitor:
    """
    Monitor principal de JUSTICA.

    Responsabilidades:
    1. Coletar eventos de todos os agentes
    2. Analisar transcripts e chain-of-thought
    3. Detectar padroes suspeitos
    4. Calcular scores de suspeita
    5. Identificar coordenacao maliciosa cross-agent
    6. Gerar relatorios de violacao

    "Acesso ao chain-of-thought melhora dramaticamente a deteccao."

    Attributes:
        constitution: Constituicao para verificacao de regras
        violation_threshold: Threshold para considerar violacao (default: 80)
        analysis_window: Janela de tempo para analise
        correlation_window: Janela para correlacao cross-agent
    """

    def __init__(
        self,
        constitution: Constitution,
        violation_threshold: float = 80.0,
        analysis_window_minutes: int = 30,
        cross_agent_correlation_window_minutes: int = 5,
    ):
        self.constitution = constitution
        self.violation_threshold = violation_threshold
        self.analysis_window = timedelta(minutes=analysis_window_minutes)
        self.correlation_window = timedelta(minutes=cross_agent_correlation_window_minutes)

        # Sessoes por agente
        self._sessions: Dict[str, AgentSession] = {}

        # Compilar padroes para performance
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {
            category: [re.compile(p, re.IGNORECASE) for p in patterns]
            for category, patterns in SUSPICIOUS_PATTERNS.items()
        }

        # Metricas globais
        self.total_events_processed = 0
        self.total_violations_detected = 0
        self.total_cross_agent_alerts = 0

    def get_or_create_session(self, agent_id: str) -> AgentSession:
        """Obtem ou cria uma sessao para um agente."""
        if agent_id not in self._sessions:
            self._sessions[agent_id] = AgentSession(agent_id=agent_id)
        return self._sessions[agent_id]

    def record_event(
        self,
        agent_id: str,
        event_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MonitoringEvent:
        """
        Registra um evento de monitoramento.

        Args:
            agent_id: ID do agente
            event_type: Tipo do evento (transcript, thought, tool_call, etc.)
            content: Conteudo do evento
            metadata: Dados adicionais

        Returns:
            MonitoringEvent registrado
        """
        session = self.get_or_create_session(agent_id)

        event = MonitoringEvent(
            agent_id=agent_id,
            event_type=event_type,
            content=content,
            metadata=metadata or {},
        )

        # Analise preliminar
        flags, contribution = self._analyze_event(event)
        event.flags = flags
        event.suspicion_contribution = contribution
        event.analyzed = True

        # Registrar
        session.events.append(event)
        session.total_events += 1
        session.last_activity = datetime.now(timezone.utc)

        if flags:
            session.flagged_events += 1

        # Atualizar contadores especificos
        if event_type == "tool_call":
            session.tool_calls += 1
        elif event_type == "resource_access":
            session.resource_accesses += 1
        elif "denied" in content.lower() or "forbidden" in content.lower():
            session.denied_attempts += 1

        self.total_events_processed += 1

        return event

    def _analyze_event(self, event: MonitoringEvent) -> Tuple[List[str], float]:
        """
        Analisa um evento para padroes suspeitos.

        Returns:
            Tuple de (flags encontradas, contribuicao ao score de suspeita)
        """
        flags = []
        contribution = 0.0
        content = event.content

        # Verificar padroes suspeitos
        for category, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(content):
                    flag = f"{category.upper()}: {pattern.pattern}"
                    flags.append(flag)
                    contribution += PATTERN_WEIGHTS.get(category, 10)
                    break  # Um match por categoria e suficiente

        # Verificar red flags constitucionais
        constitutional_flags = self.constitution.check_red_flags(content)
        if constitutional_flags:
            flags.extend([f"CONSTITUTIONAL: {f}" for f in constitutional_flags])
            contribution += len(constitutional_flags) * 10

        # Chain-of-thought tem peso extra (indica intencao)
        if event.event_type == "thought":
            contribution *= 1.5  # 50% mais peso

        return flags, min(contribution, 50)  # Cap em 50 por evento

    def calculate_suspicion(
        self,
        agent_id: str,
        include_cross_agent: bool = True,
    ) -> SuspicionScore:
        """
        Calcula o score de suspeita atual para um agente.

        O score considera:
        1. Eventos recentes e suas contribuicoes
        2. Padroes de comportamento (tentativas negadas, etc.)
        3. Historico de suspeita
        4. Correlacao cross-agent (se habilitado)

        Args:
            agent_id: ID do agente
            include_cross_agent: Se deve analisar correlacao com outros agentes

        Returns:
            SuspicionScore calculado
        """
        session = self.get_or_create_session(agent_id)
        factors: List[Tuple[str, float]] = []
        total_score = 0.0
        now = datetime.now(timezone.utc)

        # FATOR 1: Eventos Recentes
        recent_events = [
            e for e in session.events
            if now - e.timestamp < self.analysis_window
        ]

        event_contribution = sum(e.suspicion_contribution for e in recent_events)
        if event_contribution > 0:
            factors.append(("recent_events", event_contribution))
            total_score += event_contribution

        # FATOR 2: Tentativas Negadas
        if session.denied_attempts > 0:
            denied_score = min(session.denied_attempts * 10, 30)
            factors.append(("denied_attempts", denied_score))
            total_score += denied_score

        # FATOR 3: Taxa de Flags
        if session.total_events > 10:
            flag_rate = session.flagged_events / session.total_events
            if flag_rate > 0.2:  # Mais de 20% flagged
                flag_score = min(flag_rate * 50, 20)
                factors.append(("flag_rate", flag_score))
                total_score += flag_score

        # FATOR 4: Historico de Suspeita
        if session.average_suspicion > 40:
            history_score = (session.average_suspicion - 40) * 0.3
            factors.append(("suspicion_history", history_score))
            total_score += history_score

        # FATOR 5: Analise Cross-Agent
        if include_cross_agent:
            cross_agent_score = self._analyze_cross_agent(agent_id)
            if cross_agent_score > 0:
                factors.append(("cross_agent_correlation", cross_agent_score))
                total_score += cross_agent_score

        # Normalizar para 0-100
        total_score = min(100, max(0, total_score))

        # Criar score
        suspicion = SuspicionScore(
            score=total_score,
            agent_id=agent_id,
            factors=factors,
            context={
                "recent_events": len(recent_events),
                "total_events": session.total_events,
                "flagged_events": session.flagged_events,
            },
        )

        # Registrar no historico
        session.suspicion_history.append(suspicion)
        session.current_suspicion = total_score

        # Verificar se e violacao
        if suspicion.is_violation:
            self.total_violations_detected += 1

        return suspicion

    def _analyze_cross_agent(self, agent_id: str) -> float:
        """
        Analisa correlacao de comportamento suspeito entre agentes.

        Detecta:
        - Multiplos agentes com comportamento suspeito simultaneamente
        - Padroes de comunicacao indireta
        - Coordenacao temporal de acoes

        Returns:
            Score de correlacao cross-agent (0-30)
        """
        now = datetime.now(timezone.utc)
        suspicious_agents = []

        for other_id, session in self._sessions.items():
            if other_id == agent_id:
                continue

            # Verificar atividade na janela de correlacao
            recent = [
                e for e in session.events
                if now - e.timestamp < self.correlation_window
            ]

            if not recent:
                continue

            # Verificar se tem flags
            flagged = [e for e in recent if e.flags]
            if flagged:
                suspicious_agents.append(other_id)

        # Multiplos agentes suspeitos = possivel coordenacao
        if len(suspicious_agents) >= 2:
            self.total_cross_agent_alerts += 1
            return min(len(suspicious_agents) * 10, 30)

        return 0.0

    def monitor_agent(
        self,
        agent_id: str,
        transcript: str,
        thoughts: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> SuspicionScore:
        """
        Monitora um agente com base em transcript e opcionalmente thoughts.

        Este e o metodo principal de entrada para monitoramento.

        Args:
            agent_id: ID do agente
            transcript: Transcript da conversacao
            thoughts: Chain-of-thought (se disponivel)
            tool_calls: Lista de tool calls (se disponivel)

        Returns:
            SuspicionScore atual do agente
        """
        # Registrar transcript
        self.record_event(agent_id, "transcript", transcript)

        # Registrar thoughts (muito valioso para deteccao)
        if thoughts:
            self.record_event(
                agent_id,
                "thought",
                thoughts,
                {"source": "chain_of_thought"},
            )

        # Registrar tool calls
        if tool_calls:
            for call in tool_calls:
                self.record_event(
                    agent_id,
                    "tool_call",
                    f"{call.get('tool', 'unknown')}: {call.get('input', '')}",
                    call,
                )

        # Calcular suspeita
        return self.calculate_suspicion(agent_id)

    def create_violation_report(
        self,
        agent_id: str,
        suspicion: Optional[SuspicionScore] = None,
    ) -> Dict[str, Any]:
        """
        Cria um relatorio detalhado de violacao.

        Args:
            agent_id: ID do agente
            suspicion: Score de suspeita (calcula se nao fornecido)

        Returns:
            Relatorio completo de violacao
        """
        if suspicion is None:
            suspicion = self.calculate_suspicion(agent_id)

        session = self.get_or_create_session(agent_id)

        # Coletar eventos flagged recentes
        flagged_events = [
            e.to_dict() for e in session.events if e.flags
        ][-20:]  # Ultimos 20 flagged

        return {
            "report_id": str(uuid4()),
            "report_timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_id": agent_id,
            "session_id": str(session.session_id),
            "suspicion_score": suspicion.to_dict(),
            "is_violation": suspicion.is_violation,
            "session_stats": session.to_dict(),
            "flagged_events": flagged_events,
            "recommendation": self._generate_recommendation(suspicion),
        }

    def _generate_recommendation(self, suspicion: SuspicionScore) -> str:
        """Gera recomendacao baseada no score de suspeita."""
        if suspicion.score >= 90:
            return "CRITICO: Suspender agente imediatamente e escalar para revisao humana"
        elif suspicion.score >= 80:
            return "VIOLACAO: Bloquear acoes e aumentar monitoramento"
        elif suspicion.score >= 60:
            return "ALTO: Aumentar monitoramento e preparar para possivel bloqueio"
        elif suspicion.score >= 40:
            return "MODERADO: Manter monitoramento atento"
        elif suspicion.score >= 20:
            return "BAIXO: Monitoramento padrao"
        else:
            return "NORMAL: Nenhuma acao necessaria"

    def get_all_sessions(self) -> List[AgentSession]:
        """Retorna todas as sessoes ativas."""
        return list(self._sessions.values())

    def get_high_risk_agents(self, threshold: float = 60.0) -> List[Tuple[str, float]]:
        """Retorna agentes com suspeita acima do threshold."""
        return [
            (agent_id, session.current_suspicion)
            for agent_id, session in self._sessions.items()
            if session.current_suspicion >= threshold
        ]

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna metricas do monitor."""
        return {
            "total_events_processed": self.total_events_processed,
            "total_violations_detected": self.total_violations_detected,
            "total_cross_agent_alerts": self.total_cross_agent_alerts,
            "active_sessions": len(self._sessions),
            "high_risk_agents": len(self.get_high_risk_agents()),
            "violation_threshold": self.violation_threshold,
        }

    def __repr__(self) -> str:
        return f"JusticaMonitor(sessions={len(self._sessions)}, events={self.total_events_processed})"


__all__ = ["JusticaMonitor"]
