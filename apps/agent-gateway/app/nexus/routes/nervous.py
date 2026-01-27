"""
NEXUS Nervous System Routes.

Endpoints for Digital Nervous System: homeostasis, event processing, Eventarc.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from nexus.agent import get_nexus
from nexus.schemas import NervousEventRequest
from nexus.nervous_system import NervousSystemEvent, parse_eventarc_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nervous", tags=["nervous-system"])


@router.get("/status")
async def get_nervous_system_status() -> Dict[str, Any]:
    """Get Digital Nervous System status and homeostasis metrics."""
    nexus = get_nexus()
    return nexus.nervous_system.get_stats()


@router.get("/homeostasis")
async def get_homeostasis_metrics() -> Dict[str, Any]:
    """
    Get homeostasis metrics.

    Target: >95% autonomous resolution rate.
    """
    nexus = get_nexus()
    return nexus.nervous_system.get_homeostasis_metrics()


@router.post("/process")
async def process_nervous_event(request: NervousEventRequest) -> Dict[str, Any]:
    """
    Process an event through the Digital Nervous System.

    The event flows through three layers:
    1. Reflex Arc (15-100ms) - Instant deterministic responses
    2. Innate Immunity (1-10s) - Swarm micro-agents
    3. Adaptive Immunity (10s-min) - NEXUS + Prometheus
    """
    nexus = get_nexus()

    event = NervousSystemEvent(
        event_id=request.event_id,
        source=request.source,
        event_type=request.event_type,
        severity=request.severity,
        resource_type=request.resource_type,
        resource_name=request.resource_name,
        timestamp=datetime.now(timezone.utc),
        payload=request.payload,
        metrics=request.metrics,
    )

    result = await nexus.nervous_system.on_stimulus(event)

    return {
        "event_id": result.event_id,
        "resolved": result.resolved,
        "autonomy_level": result.autonomy_level.value,
        "latency_ms": result.latency_ms,
        "actions_taken": result.actions_taken,
        "memory_formed": result.memory_formed,
        "escalated_to_human": result.escalated_to_human,
        "details": result.details,
    }


@router.post("/eventarc")
async def process_eventarc_event(cloud_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Webhook endpoint for Eventarc triggers.

    Configure Eventarc to send Cloud Logging and Monitoring events here.
    """
    nexus = get_nexus()

    event = parse_eventarc_event(cloud_event)
    result = await nexus.nervous_system.on_stimulus(event)

    return {
        "event_id": result.event_id,
        "resolved": result.resolved,
        "autonomy_level": result.autonomy_level.value,
        "latency_ms": result.latency_ms,
    }
