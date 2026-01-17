"""
AutoAudit - Sistema de Auditoria Automática da TUI.

Componentes:
- AutoAuditService: Orquestrador principal
- StateMonitor: Captura de eventos internos
- BlackBoxLogger: Dumps de falha
- SCENARIOS: Cenários de teste

Uso:
    /autoaudit           - Executa auditoria completa
    /autoaudit quick     - Apenas cenários rápidos
    /autoaudit list      - Lista cenários
    /autoaudit category  - Por categoria
"""

from __future__ import annotations

from .scenarios import (
    SCENARIOS,
    AuditScenario,
    ScenarioCategory,
    Expectation,
    get_scenarios_by_category,
    get_scenario_by_id,
    load_custom_scenarios,
)
from .monitor import StateMonitor, EventTrace
from .logger import BlackBoxLogger
from .service import AutoAuditService, AuditReport, ScenarioResult

__all__ = [
    # Service
    "AutoAuditService",
    "AuditReport",
    "ScenarioResult",
    # Monitor
    "StateMonitor",
    "EventTrace",
    # Logger
    "BlackBoxLogger",
    # Scenarios
    "SCENARIOS",
    "AuditScenario",
    "ScenarioCategory",
    "Expectation",
    "get_scenarios_by_category",
    "get_scenario_by_id",
    "load_custom_scenarios",
]
