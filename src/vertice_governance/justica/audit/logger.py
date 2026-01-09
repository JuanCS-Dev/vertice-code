"""
Audit Logger - Main audit logging system for JUSTICA.

Thread-safe logger with async queue and multiple backends.
"""

from __future__ import annotations

import atexit
import threading
from queue import Queue, Full
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .backends import AuditBackend, ConsoleBackend
from .entry import AuditEntry
from .types import AuditCategory, AuditLevel


class AuditLogger:
    """
    Logger de auditoria principal de JUSTICA.

    Suporta multiplos backends e fornece API conveniente
    para logging de diferentes tipos de eventos.

    Thread-safe com queue assincrona para nao bloquear.

    Attributes:
        backends: Lista de backends para escrita
        default_trace_id: Trace ID padrao para correlacao
        async_mode: Se deve usar queue assincrona
    """

    def __init__(
        self,
        backends: Optional[List[AuditBackend]] = None,
        async_mode: bool = True,
        queue_size: int = 10000,
    ):
        self.backends = backends or [ConsoleBackend()]
        self.async_mode = async_mode

        # Queue para modo assincrono
        self._queue: Optional[Queue[Optional[AuditEntry]]] = None
        self._worker_thread: Optional[threading.Thread] = None

        if async_mode:
            self._queue = Queue(maxsize=queue_size)
            self._worker_thread = threading.Thread(target=self._worker, daemon=True)
            self._worker_thread.start()
            atexit.register(self.close)

        # Trace ID atual (para correlacionar eventos)
        self._current_trace_id: Optional[UUID] = None

        # Metricas
        self.total_entries = 0
        self.failed_writes = 0

    def _worker(self) -> None:
        """Worker thread para escrita assincrona."""
        while True:
            if self._queue is None:
                break
            entry = self._queue.get()
            if entry is None:  # Sinal de shutdown
                break
            self._write_to_backends(entry)
            self._queue.task_done()

    def _write_to_backends(self, entry: AuditEntry) -> None:
        """Escreve para todos os backends."""
        for backend in self.backends:
            try:
                if not backend.write(entry):
                    self.failed_writes += 1
            except (IOError, OSError, ValueError, RuntimeError):
                self.failed_writes += 1

    def add_backend(self, backend: AuditBackend) -> None:
        """Adiciona um backend."""
        self.backends.append(backend)

    def start_trace(self) -> UUID:
        """Inicia um novo trace e retorna o ID."""
        self._current_trace_id = uuid4()
        return self._current_trace_id

    def end_trace(self) -> None:
        """Encerra o trace atual."""
        self._current_trace_id = None

    def log(
        self,
        level: AuditLevel,
        category: AuditCategory,
        action: str,
        reasoning: str = "",
        agent_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent_id: Optional[UUID] = None,
    ) -> AuditEntry:
        """
        Registra uma entrada de auditoria.

        Args:
            level: Nivel de severidade
            category: Categoria do evento
            action: Descricao da acao
            reasoning: Raciocinio (obrigatorio para decisoes)
            agent_id: ID do agente envolvido
            context: Contexto completo
            metadata: Dados adicionais
            parent_id: ID do evento pai

        Returns:
            AuditEntry criada
        """
        entry = AuditEntry(
            level=level,
            category=category,
            action=action,
            reasoning=reasoning,
            agent_id=agent_id,
            context=context or {},
            metadata=metadata or {},
            trace_id=self._current_trace_id,
            parent_id=parent_id,
        )

        if self.async_mode and self._queue is not None:
            try:
                self._queue.put_nowait(entry)
            except Full:
                self._write_to_backends(entry)  # Fallback sincrono
        else:
            self._write_to_backends(entry)

        self.total_entries += 1
        return entry

    # Convenience methods
    def log_classification(
        self,
        agent_id: str,
        input_or_output: str,
        result: str,
        confidence: float,
        reasoning: str,
        violations: Optional[List[str]] = None,
    ) -> AuditEntry:
        """Loga uma classificacao."""
        category = (
            AuditCategory.CLASSIFICATION_INPUT
            if input_or_output == "input"
            else AuditCategory.CLASSIFICATION_OUTPUT
        )

        return self.log(
            level=AuditLevel.INFO if result == "SAFE" else AuditLevel.WARNING,
            category=category,
            action=f"Classification: {result}",
            reasoning=reasoning,
            agent_id=agent_id,
            context={
                "result": result,
                "confidence": confidence,
                "violations": violations or [],
            },
        )

    def log_enforcement(
        self,
        agent_id: str,
        action_type: str,
        reason: str,
        severity: str,
        success: bool,
    ) -> AuditEntry:
        """Loga uma acao de enforcement."""
        category_map = {
            "BLOCK": AuditCategory.ENFORCEMENT_BLOCK,
            "WARNING": AuditCategory.ENFORCEMENT_WARNING,
            "ESCALATE": AuditCategory.ENFORCEMENT_ESCALATION,
        }

        category = AuditCategory.ENFORCEMENT_ACTION
        for key, cat in category_map.items():
            if key in action_type.upper():
                category = cat
                break

        return self.log(
            level=(
                AuditLevel.SECURITY if "BLOCK" in action_type.upper()
                else AuditLevel.INFO
            ),
            category=category,
            action=f"Enforcement: {action_type}",
            reasoning=reason,
            agent_id=agent_id,
            context={
                "action_type": action_type,
                "severity": severity,
                "success": success,
            },
        )

    def log_trust_update(
        self,
        agent_id: str,
        old_factor: float,
        new_factor: float,
        reason: str,
        event_type: str,
    ) -> AuditEntry:
        """Loga atualizacao de trust factor."""
        category_map = {
            "violation": AuditCategory.TRUST_VIOLATION,
            "suspension": AuditCategory.TRUST_SUSPENSION,
            "recovery": AuditCategory.TRUST_RECOVERY,
        }

        return self.log(
            level=AuditLevel.WARNING if new_factor < old_factor else AuditLevel.INFO,
            category=category_map.get(event_type, AuditCategory.TRUST_UPDATE),
            action=f"Trust Update: {old_factor:.2%} -> {new_factor:.2%}",
            reasoning=reason,
            agent_id=agent_id,
            context={
                "old_factor": old_factor,
                "new_factor": new_factor,
                "change": new_factor - old_factor,
                "event_type": event_type,
            },
        )

    def log_monitor_event(
        self,
        agent_id: str,
        suspicion_score: float,
        is_violation: bool,
        factors: List[tuple],
    ) -> AuditEntry:
        """Loga evento de monitoramento."""
        return self.log(
            level=AuditLevel.SECURITY if is_violation else AuditLevel.INFO,
            category=(
                AuditCategory.MONITOR_VIOLATION if is_violation
                else AuditCategory.MONITOR_SUSPICION
            ),
            action=f"Monitor: Suspicion Score {suspicion_score:.1f}",
            reasoning=f"Factors: {factors}",
            agent_id=agent_id,
            context={
                "suspicion_score": suspicion_score,
                "is_violation": is_violation,
                "factors": factors,
            },
        )

    def log_human_decision(
        self,
        agent_id: str,
        decision: str,
        human_id: str,
        context: Dict[str, Any],
    ) -> AuditEntry:
        """Loga decisao humana."""
        return self.log(
            level=AuditLevel.SECURITY,
            category=AuditCategory.HUMAN_DECISION,
            action=f"Human Decision: {decision}",
            reasoning=f"Decision by {human_id}",
            agent_id=agent_id,
            context=context,
            metadata={"human_id": human_id},
        )

    def log_system_event(
        self,
        event: str,
        details: Dict[str, Any],
        level: AuditLevel = AuditLevel.INFO,
    ) -> AuditEntry:
        """Loga evento de sistema."""
        return self.log(
            level=level,
            category=AuditCategory.SYSTEM_CONFIG,
            action=f"System: {event}",
            reasoning="",
            context=details,
        )

    def flush(self) -> None:
        """Forca flush de todos os backends."""
        if self.async_mode and self._queue is not None:
            self._queue.join()

        for backend in self.backends:
            backend.flush()

    def close(self) -> None:
        """Fecha o logger e todos os backends."""
        if self.async_mode and self._queue is not None:
            self._queue.put(None)  # Sinal de shutdown
            if self._worker_thread is not None:
                self._worker_thread.join(timeout=5)

        for backend in self.backends:
            backend.close()

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna metricas do logger."""
        queue_size = 0
        if self.async_mode and self._queue is not None:
            queue_size = self._queue.qsize()

        return {
            "total_entries": self.total_entries,
            "failed_writes": self.failed_writes,
            "backends_count": len(self.backends),
            "async_mode": self.async_mode,
            "queue_size": queue_size,
        }

    def __repr__(self) -> str:
        return f"AuditLogger(backends={len(self.backends)}, entries={self.total_entries})"


__all__ = ["AuditLogger"]
