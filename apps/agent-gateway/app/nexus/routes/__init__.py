"""
NEXUS Routes Package.

Domain-specific routers for the NEXUS Meta-Agent API.
Each router handles a specific concern following single-responsibility principle.
"""

from nexus.routes.core import router as core_router
from nexus.routes.prometheus import router as prometheus_router
from nexus.routes.alloydb import router as alloydb_router
from nexus.routes.nervous import router as nervous_router

__all__ = [
    "core_router",
    "prometheus_router",
    "alloydb_router",
    "nervous_router",
]
