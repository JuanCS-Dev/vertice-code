"""
StateMonitor - Monitor de Estado para AutoAudit.

Captura eventos internos do sistema durante execução de cenários.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, List

if TYPE_CHECKING:
    pass


@dataclass
class EventTrace:
    """Registro de um evento interno capturado."""

    timestamp: float
    event_type: str
    payload: Dict[str, Any]
    source: str = ""
    latency_ms: float = 0.0


class StateMonitor:
    """
    Monitor de estado que observa eventos internos.

    Captura:
    - Tool calls e resultados
    - Agent routing decisions
    - LLM streaming events (SSE)
    - Erros e exceções
    """

    def __init__(self) -> None:
        self._events: List[EventTrace] = []
        self._is_active = False
        self._start_time: float = 0.0
        self._hooks: List[Callable[..., Any]] = []

    def add_hook(self, hook: Callable[..., Any]) -> None:
        """Adiciona hook para processamento de eventos em tempo real."""
        self._hooks.append(hook)

    def start(self) -> None:
        """Inicia captura de eventos."""
        self._events.clear()
        self._is_active = True
        self._start_time = time.time()

    def stop(self) -> List[EventTrace]:
        """Para captura e retorna eventos."""
        self._is_active = False
        return self._events.copy()

    def record(
        self,
        event_type: str,
        payload: Dict[str, Any],
        source: str = "",
    ) -> None:
        """Registra um evento."""
        if not self._is_active:
            return

        now = time.time()
        self._events.append(
            EventTrace(
                timestamp=now,
                event_type=event_type,
                payload=payload,
                source=source,
                latency_ms=(now - self._start_time) * 1000,
            )
        )

        # Execute hooks
        for hook in self._hooks:
            try:
                hook(event_type, payload)
            except Exception as e:
                pass  # Hooks não devem quebrar o monitor

    def record_sse_event(self, event: Any) -> None:
        """Registra evento SSE do OpenResponsesParser."""
        if not self._is_active:
            return

        event_type = getattr(event, "event_type", "unknown")
        raw_data = getattr(event, "raw_data", {})

        self.record(event_type, raw_data, source="sse")

    def record_tool_call(self, tool_name: str, args: Dict[str, Any], result: Any) -> None:
        """Registra chamada de ferramenta."""
        self.record(
            "tool_call",
            {"tool_name": tool_name, "args": args, "result_type": type(result).__name__},
            source="tools",
        )

    def record_agent_routing(self, agent_name: str, confidence: float) -> None:
        """Registra decisão de roteamento."""
        self.record(
            "agent_routing",
            {"agent_name": agent_name, "confidence": confidence},
            source="agents",
        )

    def record_error(self, error: Exception, context: str = "") -> None:
        """Registra erro."""
        self.record(
            "error",
            {"error_type": type(error).__name__, "message": str(error), "context": context},
            source="error",
        )

    def has_event_type(self, event_type: str) -> bool:
        """Verifica se há evento de determinado tipo."""
        return any(e.event_type == event_type for e in self._events)

    def get_events_by_type(self, event_type: str) -> List[EventTrace]:
        """Retorna eventos filtrados por tipo."""
        return [e for e in self._events if e.event_type == event_type]

    def get_total_latency_ms(self) -> float:
        """Retorna latência total desde o início."""
        if not self._events:
            return 0.0
        return self._events[-1].latency_ms

    def get_event_count(self) -> int:
        """Retorna quantidade total de eventos."""
        return len(self._events)

    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumo dos eventos capturados."""
        event_types: Dict[str, int] = {}
        for e in self._events:
            event_types[e.event_type] = event_types.get(e.event_type, 0) + 1

        return {
            "total_events": len(self._events),
            "event_types": event_types,
            "total_latency_ms": self.get_total_latency_ms(),
            "has_errors": self.has_event_type("error"),
        }


__all__ = ["StateMonitor", "EventTrace"]
