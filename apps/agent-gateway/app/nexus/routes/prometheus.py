"""
NEXUS Prometheus Bridge Routes.

Endpoints for Prometheus world model integration, simulation, and memory sync.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter

from nexus.agent import get_nexus
from nexus.schemas import (
    SimulateRequest,
    MemoryQueryRequest,
    ReflectionRequest,
    ToolCreationRequest,
    DelegateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prometheus", tags=["prometheus"])


@router.post("/connect")
async def connect_to_prometheus() -> Dict[str, Any]:
    """Connect NEXUS to Prometheus meta-agent."""
    nexus = get_nexus()
    success = await nexus.prometheus.connect()
    return {
        "connected": success,
        "bridge_active": nexus.prometheus.is_connected,
    }


@router.post("/disconnect")
async def disconnect_from_prometheus():
    """Disconnect NEXUS from Prometheus."""
    nexus = get_nexus()
    await nexus.prometheus.disconnect()
    return {"connected": False}


@router.post("/simulate")
async def simulate_action(request: SimulateRequest) -> Dict[str, Any]:
    """
    Use Prometheus World Model to simulate an action.

    Returns predicted outcomes, risks, and alternatives.
    """
    nexus = get_nexus()
    return await nexus.prometheus.simulate_action(
        action=request.action,
        context=request.context,
    )


@router.post("/memory/query")
async def query_prometheus_memory(request: MemoryQueryRequest) -> Dict[str, Any]:
    """Query Prometheus 6-type memory system (MIRIX)."""
    nexus = get_nexus()
    return await nexus.prometheus.query_prometheus_memory(
        query=request.query,
        memory_type=request.memory_type,
    )


@router.post("/memory/sync")
async def sync_memories_to_prometheus() -> Dict[str, Any]:
    """Sync NEXUS insights to Prometheus memory."""
    nexus = get_nexus()
    insights = await nexus.metacognitive.get_recent_insights(limit=20, min_confidence=0.7)
    return await nexus.prometheus.sync_memories(insights)


@router.post("/reflect")
async def request_prometheus_reflection(request: ReflectionRequest) -> Dict[str, Any]:
    """Request Prometheus reflection on a task outcome."""
    nexus = get_nexus()
    return await nexus.prometheus.request_reflection(
        task=request.task,
        outcome=request.outcome,
        context=request.context,
    )


@router.post("/tools/create")
async def create_tool_via_prometheus(request: ToolCreationRequest) -> Dict[str, Any]:
    """Request Prometheus to create a new tool dynamically."""
    nexus = get_nexus()
    return await nexus.prometheus.request_tool_creation(
        description=request.description,
        requirements=request.requirements,
    )


@router.post("/delegate")
async def delegate_task_to_prometheus(request: DelegateRequest) -> Dict[str, Any]:
    """Delegate a task to Prometheus for execution."""
    nexus = get_nexus()
    return await nexus.prometheus.delegate_to_prometheus(
        task=request.task,
        use_world_model=request.use_world_model,
        use_memory=request.use_memory,
    )


@router.get("/stats")
async def get_prometheus_bridge_stats() -> Dict[str, Any]:
    """Get Prometheus bridge statistics."""
    nexus = get_nexus()
    return nexus.prometheus.get_stats()
