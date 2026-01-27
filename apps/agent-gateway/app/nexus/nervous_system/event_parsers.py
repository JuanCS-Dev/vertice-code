"""
Digital Nervous System - Event Parsers.

Parsers for GCloud event sources:
- Eventarc CloudEvents
- Pub/Sub messages
- Cloud Monitoring alerts

Converts raw GCloud events to normalized NervousSystemEvent format.
"""

from __future__ import annotations

import base64
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict

from nexus.nervous_system.types import NervousSystemEvent

logger = logging.getLogger(__name__)


def parse_eventarc_event(cloud_event: Dict[str, Any]) -> NervousSystemEvent:
    """
    Parse CloudEvents format from Eventarc.

    Args:
        cloud_event: Raw CloudEvent dictionary

    Returns:
        Normalized NervousSystemEvent
    """
    data = cloud_event.get("data", {})

    # Extract resource info
    resource = data.get("resource", {})
    resource_type = resource.get("type", "unknown")
    resource_labels = resource.get("labels", {})

    # Extract severity
    severity = data.get("severity", "INFO")

    # Extract metrics if available
    metrics = {}
    if "jsonPayload" in data:
        json_payload = data["jsonPayload"]
        metrics = {
            "cpu_utilization": json_payload.get("cpu_utilization", 0),
            "memory_utilization": json_payload.get("memory_utilization", 0),
            "request_latency_ms": json_payload.get("request_latency_ms", 0),
        }

    return NervousSystemEvent(
        event_id=cloud_event.get("id", str(time.time())),
        source="eventarc",
        event_type=cloud_event.get("type", "unknown"),
        severity=severity,
        resource_type=resource_type,
        resource_name=resource_labels.get("service_name", "unknown"),
        timestamp=datetime.now(timezone.utc),
        payload=data,
        metrics=metrics,
    )


def parse_pubsub_message(message: Dict[str, Any]) -> NervousSystemEvent:
    """
    Parse Pub/Sub message.

    Args:
        message: Raw Pub/Sub message dictionary

    Returns:
        Normalized NervousSystemEvent
    """
    data = message.get("data", "")

    if data:
        try:
            decoded = base64.b64decode(data).decode("utf-8")
            payload = json.loads(decoded)
        except Exception:
            payload = {"raw": data}
    else:
        payload = message.get("attributes", {})

    return NervousSystemEvent(
        event_id=message.get("messageId", str(time.time())),
        source="pubsub",
        event_type=message.get("attributes", {}).get("type", "pubsub.message"),
        severity=payload.get("severity", "INFO"),
        resource_type=payload.get("resource_type", "unknown"),
        resource_name=payload.get("resource_name", "unknown"),
        timestamp=datetime.now(timezone.utc),
        payload=payload,
        metrics=payload.get("metrics", {}),
    )


def parse_monitoring_alert(alert: Dict[str, Any]) -> NervousSystemEvent:
    """
    Parse Cloud Monitoring alert.

    Args:
        alert: Raw Cloud Monitoring alert dictionary

    Returns:
        Normalized NervousSystemEvent
    """
    incident = alert.get("incident", {})

    # Determine severity from alert policy
    severity = "WARNING"
    if incident.get("state") == "open":
        severity = "ERROR"
    if "critical" in incident.get("policy_name", "").lower():
        severity = "CRITICAL"

    return NervousSystemEvent(
        event_id=incident.get("incident_id", str(time.time())),
        source="monitoring",
        event_type="google.cloud.monitoring.alert.fired",
        severity=severity,
        resource_type=incident.get("resource_type_display_name", "unknown"),
        resource_name=incident.get("resource_name", "unknown"),
        timestamp=datetime.now(timezone.utc),
        payload=alert,
        metrics={
            "threshold_value": incident.get("threshold_value", 0),
            "observed_value": incident.get("observed_value", 0),
        },
    )
