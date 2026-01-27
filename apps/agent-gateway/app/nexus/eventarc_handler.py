"""
NEXUS Eventarc Handler - CloudEvents Integration

Handles incoming CloudEvents from GCP Eventarc triggers:
- Cloud Logging log entries
- Cloud Monitoring alerts
- Pub/Sub messages
- Cloud Run service events

Routes events through the Digital Nervous System for autonomous healing.

GCloud Integration:
- Project: vertice-ai
- Region: us-central1
- Service: vertice-agent-gateway
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks

from nexus.schemas import (
    EventarcResponse,
    NervousSystemStatsResponse,
)
from nexus.nervous_system import (
    DigitalNervousSystem,
    NervousSystemEvent,
    NervousSystemResult,
    parse_eventarc_event,
    parse_pubsub_message,
    parse_monitoring_alert,
)
from nexus.config import NexusConfig

logger = logging.getLogger(__name__)

# GCloud Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "vertice-ai")
REGION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# Global nervous system instance
_nervous_system: Optional[DigitalNervousSystem] = None
_nervous_system_lock = asyncio.Lock()


# =============================================================================
# NERVOUS SYSTEM LIFECYCLE
# =============================================================================


async def get_nervous_system() -> DigitalNervousSystem:
    """Get or create the global Nervous System instance."""
    global _nervous_system

    async with _nervous_system_lock:
        if _nervous_system is None:
            config = NexusConfig()
            _nervous_system = DigitalNervousSystem(config)
            logger.info("🧬 Digital Nervous System initialized")

        return _nervous_system


async def connect_nexus_components(
    metacognitive=None,
    prometheus_bridge=None,
    alloydb_store=None,
) -> None:
    """Connect NEXUS components to the Nervous System."""
    ns = await get_nervous_system()
    ns.set_nexus_components(
        metacognitive=metacognitive,
        prometheus_bridge=prometheus_bridge,
        alloydb_store=alloydb_store,
    )
    logger.info("🔗 NEXUS components connected to Nervous System")


# =============================================================================
# FASTAPI ROUTER
# =============================================================================


router = APIRouter(prefix="/v1/eventarc", tags=["eventarc", "nervous-system"])


@router.post("/webhook", response_model=EventarcResponse)
async def eventarc_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> EventarcResponse:
    """
    Main Eventarc webhook endpoint.

    Receives CloudEvents from GCP Eventarc triggers and routes them
    through the Digital Nervous System for autonomous processing.

    Supported event types:
    - google.cloud.logging.logEntry.written
    - google.cloud.monitoring.alert.fired
    - google.cloud.pubsub.topic.v1.messagePublished
    - google.cloud.run.service.v1.updated
    """
    # Parse CloudEvent from request
    try:
        cloud_event = await _parse_cloud_event(request)
    except Exception as e:
        logger.error(f"Failed to parse CloudEvent: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid CloudEvent: {e}")

    # Get nervous system
    ns = await get_nervous_system()

    # Convert to NervousSystemEvent
    ns_event = _cloud_event_to_nervous_event(cloud_event)

    # Process through nervous system
    result = await ns.on_stimulus(ns_event)

    # Log result
    logger.info(
        f"🧬 Event {ns_event.event_id} processed: "
        f"{result.autonomy_level.value} ({result.latency_ms:.1f}ms)"
    )

    # Background task: sync to MCP if connected
    background_tasks.add_task(_sync_to_mcp, ns_event, result)

    return EventarcResponse(
        event_id=result.event_id,
        processed=result.resolved,
        autonomy_level=result.autonomy_level.value,
        latency_ms=result.latency_ms,
        actions_taken=result.actions_taken,
        escalated=result.escalated_to_human,
        details=result.details,
    )


@router.post("/logging", response_model=EventarcResponse)
async def handle_logging_event(
    request: Request,
    background_tasks: BackgroundTasks,
) -> EventarcResponse:
    """
    Handle Cloud Logging log entries.

    Triggered by: google.cloud.logging.logEntry.written
    """
    cloud_event = await _parse_cloud_event(request)

    # Ensure it's a logging event
    if "logging" not in cloud_event.get("type", ""):
        logger.warning(f"Non-logging event received: {cloud_event.get('type')}")

    ns = await get_nervous_system()
    ns_event = parse_eventarc_event(cloud_event)
    result = await ns.on_stimulus(ns_event)

    background_tasks.add_task(_sync_to_mcp, ns_event, result)

    return EventarcResponse(
        event_id=result.event_id,
        processed=result.resolved,
        autonomy_level=result.autonomy_level.value,
        latency_ms=result.latency_ms,
        actions_taken=result.actions_taken,
        escalated=result.escalated_to_human,
    )


@router.post("/monitoring", response_model=EventarcResponse)
async def handle_monitoring_alert(
    request: Request,
    background_tasks: BackgroundTasks,
) -> EventarcResponse:
    """
    Handle Cloud Monitoring alerts.

    Triggered by: google.cloud.monitoring.alert.fired
    """
    body = await request.json()

    ns = await get_nervous_system()
    ns_event = parse_monitoring_alert(body)
    result = await ns.on_stimulus(ns_event)

    background_tasks.add_task(_sync_to_mcp, ns_event, result)

    return EventarcResponse(
        event_id=result.event_id,
        processed=result.resolved,
        autonomy_level=result.autonomy_level.value,
        latency_ms=result.latency_ms,
        actions_taken=result.actions_taken,
        escalated=result.escalated_to_human,
    )


@router.post("/pubsub", response_model=EventarcResponse)
async def handle_pubsub_message(
    request: Request,
    background_tasks: BackgroundTasks,
) -> EventarcResponse:
    """
    Handle Pub/Sub messages.

    Triggered by: google.cloud.pubsub.topic.v1.messagePublished
    """
    body = await request.json()
    message = body.get("message", body)

    ns = await get_nervous_system()
    ns_event = parse_pubsub_message(message)
    result = await ns.on_stimulus(ns_event)

    background_tasks.add_task(_sync_to_mcp, ns_event, result)

    return EventarcResponse(
        event_id=result.event_id,
        processed=result.resolved,
        autonomy_level=result.autonomy_level.value,
        latency_ms=result.latency_ms,
        actions_taken=result.actions_taken,
        escalated=result.escalated_to_human,
    )


@router.get("/stats", response_model=NervousSystemStatsResponse)
async def get_nervous_system_stats() -> NervousSystemStatsResponse:
    """Get Nervous System homeostasis metrics."""
    ns = await get_nervous_system()
    metrics = ns.get_homeostasis_metrics()

    return NervousSystemStatsResponse(
        total_events=metrics["total_events"],
        autonomous_resolution_rate=metrics["autonomous_resolution_rate"],
        reflex_rate=metrics["reflex_rate"],
        innate_rate=metrics["innate_rate"],
        adaptive_rate=metrics["adaptive_rate"],
        human_escalation_rate=metrics["human_escalation_rate"],
        homeostasis_achieved=metrics["homeostasis_achieved"],
        by_layer=metrics["by_layer"],
    )


@router.get("/health")
async def nervous_system_health() -> Dict[str, Any]:
    """Health check for Nervous System."""
    ns = await get_nervous_system()
    stats = ns.get_stats()

    return {
        "status": "healthy",
        "homeostasis": stats["homeostasis"],
        "reflex_arc_active": True,
        "innate_immunity_active": True,
        "adaptive_immunity_active": stats["nexus_connected"],
        "prometheus_connected": stats["prometheus_connected"],
        "alloydb_connected": stats["alloydb_connected"],
    }


@router.post("/test-stimulus")
async def test_stimulus(
    severity: str = "WARNING",
    event_type: str = "test_event",
    metrics: Optional[Dict[str, float]] = None,
) -> EventarcResponse:
    """
    Send a test stimulus to the Nervous System.

    Useful for testing and validation.
    """
    ns = await get_nervous_system()

    test_event = NervousSystemEvent(
        event_id=f"test_{int(time.time() * 1000)}",
        source="test",
        event_type=event_type,
        severity=severity,
        resource_type="test_resource",
        resource_name="test",
        timestamp=datetime.now(timezone.utc),
        payload={"test": True},
        metrics=metrics or {"cpu_utilization": 0.5, "memory_utilization": 0.5},
    )

    result = await ns.on_stimulus(test_event)

    return EventarcResponse(
        event_id=result.event_id,
        processed=result.resolved,
        autonomy_level=result.autonomy_level.value,
        latency_ms=result.latency_ms,
        actions_taken=result.actions_taken,
        escalated=result.escalated_to_human,
        details=result.details,
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


async def _parse_cloud_event(request: Request) -> Dict[str, Any]:
    """Parse CloudEvent from HTTP request."""
    # Check for CloudEvents headers
    ce_id = request.headers.get("ce-id")
    ce_source = request.headers.get("ce-source")
    ce_type = request.headers.get("ce-type")
    ce_time = request.headers.get("ce-time")
    ce_specversion = request.headers.get("ce-specversion", "1.0")

    body = await request.json()

    if ce_id and ce_source and ce_type:
        # CloudEvents binary mode
        return {
            "specversion": ce_specversion,
            "id": ce_id,
            "source": ce_source,
            "type": ce_type,
            "time": ce_time,
            "data": body,
        }
    elif "specversion" in body:
        # CloudEvents structured mode
        return body
    else:
        # Raw event (e.g., Pub/Sub push)
        return {
            "specversion": "1.0",
            "id": str(time.time()),
            "source": "direct",
            "type": "direct.push",
            "time": datetime.now(timezone.utc).isoformat(),
            "data": body,
        }


def _cloud_event_to_nervous_event(cloud_event: Dict[str, Any]) -> NervousSystemEvent:
    """Convert CloudEvent to NervousSystemEvent."""
    event_type = cloud_event.get("type", "unknown")
    data = cloud_event.get("data", {})

    # Determine severity
    severity = "INFO"
    if "severity" in data:
        severity = data["severity"]
    elif "alert" in event_type.lower():
        severity = "ERROR"
    elif "critical" in str(data).lower():
        severity = "CRITICAL"

    # Extract resource info
    resource = data.get("resource", {})
    resource_type = resource.get("type", "unknown")
    resource_labels = resource.get("labels", {})
    resource_name = resource_labels.get(
        "service_name",
        resource_labels.get("pod_name", resource_labels.get("instance_id", "unknown")),
    )

    # Extract metrics
    metrics = {}
    if "jsonPayload" in data:
        jp = data["jsonPayload"]
        metrics = {
            "cpu_utilization": jp.get("cpu_utilization", 0),
            "memory_utilization": jp.get("memory_utilization", 0),
            "request_latency_ms": jp.get("request_latency_ms", 0),
        }

    return NervousSystemEvent(
        event_id=cloud_event.get("id", str(time.time())),
        source=cloud_event.get("source", "eventarc"),
        event_type=event_type,
        severity=severity,
        resource_type=resource_type,
        resource_name=resource_name,
        timestamp=datetime.now(timezone.utc),
        payload=data,
        metrics=metrics,
    )


async def _sync_to_mcp(event: NervousSystemEvent, result: NervousSystemResult) -> None:
    """Sync nervous system event to MCP (background task)."""
    try:
        # Import here to avoid circular imports
        from nexus.agent import get_nexus

        nexus = get_nexus()
        if nexus and nexus.mcp.is_connected:
            # Share as skill/insight
            from nexus.types import MetacognitiveInsight, InsightCategory

            insight = MetacognitiveInsight(
                observation=f"Nervous System processed event: {event.event_type}",
                causal_analysis=f"Resolved at {result.autonomy_level.value} layer",
                learning=f"Actions: {', '.join(result.actions_taken) or 'none'}",
                action=result.actions_taken[0] if result.actions_taken else "monitor",
                confidence=1.0 if result.resolved else 0.5,
                category=InsightCategory.HEALING,
            )

            await nexus.mcp.share_insight(insight)
            logger.debug(f"Synced event {event.event_id} to MCP")

    except Exception as e:
        logger.warning(f"Failed to sync to MCP: {e}")


# =============================================================================
# PUBSUB PUSH HANDLER (for direct Pub/Sub push subscriptions)
# =============================================================================


@router.post("/pubsub-push")
async def pubsub_push_handler(request: Request) -> Dict[str, str]:
    """
    Handle direct Pub/Sub push subscriptions.

    This endpoint receives messages pushed directly from Pub/Sub
    subscriptions (not via Eventarc).

    Expected format:
    {
        "message": {
            "data": "base64-encoded-data",
            "messageId": "...",
            "attributes": {...}
        },
        "subscription": "projects/PROJECT/subscriptions/SUB"
    }
    """
    body = await request.json()
    message = body.get("message", {})

    # Decode data
    data_b64 = message.get("data", "")
    if data_b64:
        try:
            data_decoded = base64.b64decode(data_b64).decode("utf-8")
            payload = json.loads(data_decoded)
        except Exception:
            payload = {"raw": data_b64}
    else:
        payload = message.get("attributes", {})

    # Create nervous system event
    ns = await get_nervous_system()

    ns_event = NervousSystemEvent(
        event_id=message.get("messageId", str(time.time())),
        source="pubsub_push",
        event_type=payload.get("type", "pubsub.push"),
        severity=payload.get("severity", "INFO"),
        resource_type=payload.get("resource_type", "pubsub"),
        resource_name=payload.get("resource_name", "unknown"),
        timestamp=datetime.now(timezone.utc),
        payload=payload,
        metrics=payload.get("metrics", {}),
    )

    result = await ns.on_stimulus(ns_event)

    logger.info(
        f"🧬 Pub/Sub push processed: {result.autonomy_level.value} " f"({result.latency_ms:.1f}ms)"
    )

    # Return 200 to acknowledge message
    return {"status": "ok", "event_id": result.event_id}


# =============================================================================
# CLOUD RUN SERVICE EVENT HANDLER
# =============================================================================


@router.post("/cloud-run-events")
async def cloud_run_events_handler(
    request: Request,
    background_tasks: BackgroundTasks,
) -> EventarcResponse:
    """
    Handle Cloud Run service lifecycle events.

    Triggered by:
    - google.cloud.run.service.v1.created
    - google.cloud.run.service.v1.updated
    - google.cloud.run.service.v1.deleted
    """
    cloud_event = await _parse_cloud_event(request)

    ns = await get_nervous_system()
    ns_event = _cloud_event_to_nervous_event(cloud_event)

    # Cloud Run events are typically INFO level unless there's an error
    if ns_event.severity == "INFO":
        # Just log, don't process through full nervous system
        logger.info(f"📦 Cloud Run event: {cloud_event.get('type')}")
        return EventarcResponse(
            event_id=ns_event.event_id,
            processed=True,
            autonomy_level="L1_REFLEX",
            latency_ms=0.0,
            actions_taken=["logged"],
            escalated=False,
        )

    result = await ns.on_stimulus(ns_event)
    background_tasks.add_task(_sync_to_mcp, ns_event, result)

    return EventarcResponse(
        event_id=result.event_id,
        processed=result.resolved,
        autonomy_level=result.autonomy_level.value,
        latency_ms=result.latency_ms,
        actions_taken=result.actions_taken,
        escalated=result.escalated_to_human,
    )
