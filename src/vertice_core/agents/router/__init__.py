"""
Router Module - Semantic routing for agent selection.
"""

import asyncio
from typing import Optional

from .cache import RouterCacheMixin
from .router import SemanticRouter
from .similarity import SimilarityEngine
from .stats import RouterStatsMixin
from .types import (
    AgentType,
    RouteDefinition,
    RoutingDecision,
    TaskComplexity,
)


async def get_router() -> SemanticRouter:
    """Get initialized router instance."""
    router = SemanticRouter()
    await router.initialize()
    return router


__all__ = [
    # Main classes
    "SemanticRouter",
    # Mixins
    "RouterCacheMixin",
    "RouterStatsMixin",
    # Utilities
    "SimilarityEngine",
    # Types
    "AgentType",
    "TaskComplexity",
    "RouteDefinition",
    "RoutingDecision",
    # Functions
    "get_router",
]
