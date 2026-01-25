"""
Compatibility shim for `vertice_agents.coordinator`.

Re-exports the coordinator facade from `vertice_core.agents.coordinator`.
"""

from __future__ import annotations

from vertice_core.agents.coordinator import (
    AgencyCoordinator,
    CoordinationDecision,
    CoordinationResult,
    OrchestratorType,
    TaskCategory,
    get_coordinator,
)

__all__ = [
    "AgencyCoordinator",
    "OrchestratorType",
    "TaskCategory",
    "CoordinationDecision",
    "CoordinationResult",
    "get_coordinator",
]
