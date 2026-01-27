"""
NEXUS REST API Router.

Main router that aggregates all domain-specific routers.
Follows CODE_CONSTITUTION.md standards for modular design.

Endpoints:
- /v1/nexus/status, /stats, /start, /stop - Core endpoints
- /v1/nexus/reflect, /evolve, /insights - Metacognition
- /v1/nexus/memory/* - Memory operations
- /v1/nexus/mcp/* - MCP collective
- /v1/nexus/prometheus/* - Prometheus bridge
- /v1/nexus/alloydb/* - AlloyDB store
- /v1/nexus/nervous/* - Digital Nervous System
- /v1/nexus/v1/eventarc/* - Eventarc webhooks
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from nexus.routes.core import router as core_router
from nexus.routes.prometheus import router as prometheus_router
from nexus.routes.alloydb import router as alloydb_router
from nexus.routes.nervous import router as nervous_router
from nexus.eventarc_handler import router as eventarc_router

logger = logging.getLogger(__name__)

# Main NEXUS router
router = APIRouter(prefix="/v1/nexus", tags=["nexus"])

# Include domain-specific routers
router.include_router(core_router)
router.include_router(prometheus_router)
router.include_router(alloydb_router)
router.include_router(nervous_router)
router.include_router(eventarc_router, tags=["eventarc"])
