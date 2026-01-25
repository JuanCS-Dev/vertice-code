"""
Router - Semantic routing for agent selection.

Refactored into modular components for better maintainability.
"""

# Re-export everything from the modular structure for backward compatibility
from vertice_core.agents.router import (
    AgentType,
    RouteDefinition,
    RoutingDecision,
    SemanticRouter,
    TaskComplexity,
    get_router,
)

__all__ = [
    "AgentType",
    "TaskComplexity",
    "RouteDefinition",
    "RoutingDecision",
    "SemanticRouter",
    "get_router",
]
