"""
BlackBoxLogger - Logger de Caixa Preta para Dumps de Falha.

Salva estado detalhado do sistema no momento de uma falha.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .monitor import EventTrace


class BlackBoxLogger:
    """
    Logger de caixa preta para dumps de falha.

    Salva:
    - Contexto do prompt
    - Snapshot da memória
    - Trace de eventos
    - Stack trace de exceções
    """

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        # CRITICAL FIX: Use absolute path relative to project root
        root_dir = (
            Path(__file__).resolve().parent.parent.parent.parent.parent
        )  # vertice_core.tui/core/autoaudit/logger.py -> root
        self.output_dir = output_dir or (root_dir / "logs" / "autoaudit")
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # Fallback to tmp if permissions fail
            self.output_dir = Path("/tmp/vertice_logs/autoaudit")
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_crash_dump(
        self,
        scenario_id: str,
        scenario_prompt: str,
        status: str,
        error_message: str,
        events: List[EventTrace],
        memory_snapshot: Optional[Dict[str, Any]] = None,
        context_window: Optional[List[Dict[str, str]]] = None,
        exception_trace: str = "",
        validation_results: Optional[Dict[str, bool]] = None,
    ) -> str:
        """
        Salva dump detalhado para debug.

        Returns:
            Caminho do arquivo salvo
        """
        timestamp = datetime.now()
        filename = f"audit_fail_{scenario_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename

        dump_data = {
            "meta": {
                "timestamp": timestamp.isoformat(),
                "scenario_id": scenario_id,
                "status": status,
            },
            "scenario": {
                "prompt": scenario_prompt,
                "error_message": error_message,
            },
            "validation": validation_results or {},
            "traces": {
                "events": [
                    {
                        "timestamp": e.timestamp,
                        "type": e.event_type,
                        "payload": e.payload,
                        "source": e.source,
                        "latency_ms": e.latency_ms,
                    }
                    for e in events
                ],
                "exception": exception_trace,
            },
            "context": {
                "memory_snapshot": memory_snapshot or {},
                "context_window": context_window or [],
            },
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(dump_data, f, indent=2, ensure_ascii=False, default=str)

        return str(filepath)

    def save_report(self, report: Dict[str, Any]) -> str:
        """Salva relatório completo da auditoria."""
        timestamp = datetime.now()
        filename = f"audit_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        return str(filepath)

    def get_recent_dumps(self, limit: int = 10) -> List[Path]:
        """Retorna dumps recentes."""
        dumps = sorted(self.output_dir.glob("audit_fail_*.json"), reverse=True)
        return dumps[:limit]

    def cleanup_old_dumps(self, keep_count: int = 50) -> int:
        """Remove dumps antigos, mantendo os mais recentes."""
        dumps = sorted(self.output_dir.glob("audit_*.json"), reverse=True)
        removed = 0
        for dump in dumps[keep_count:]:
            dump.unlink()
            removed += 1
        return removed


__all__ = ["BlackBoxLogger"]
