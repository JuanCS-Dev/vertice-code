"""
NEXUS Core Routes.

Core endpoints for NEXUS Meta-Agent: status, stats, reflection, evolution, memory.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from nexus.agent import get_nexus
from nexus.types import MemoryLevel
from nexus.schemas import (
    ReflectRequest,
    ReflectResponse,
    EvolveRequest,
    EvolveResponse,
    MemoryStoreRequest,
    MemoryRetrieveRequest,
    NexusStatusResponse,
    InsightResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["nexus-core"])


@router.get("/status", response_model=NexusStatusResponse)
async def get_status():
    """Get current NEXUS status."""
    nexus = get_nexus()
    status = await nexus.get_status()
    return NexusStatusResponse(
        active=status.active,
        model=status.model,
        thinking_level=status.thinking_level,
        total_insights=status.total_insights,
        total_healings=status.total_healings,
        total_evolutions=status.total_evolutions,
        uptime_seconds=status.uptime_seconds,
        last_reflection=status.last_reflection,
    )


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """Get comprehensive NEXUS statistics."""
    nexus = get_nexus()
    return await nexus.get_comprehensive_stats()


@router.post("/start")
async def start_nexus():
    """Start NEXUS Meta-Agent."""
    nexus = get_nexus()
    await nexus.start()
    return {"status": "started", "active": True}


@router.post("/stop")
async def stop_nexus():
    """Stop NEXUS Meta-Agent."""
    nexus = get_nexus()
    await nexus.stop()
    return {"status": "stopped", "active": False}


@router.post("/reflect", response_model=ReflectResponse)
async def reflect_on_task(request: ReflectRequest):
    """
    Trigger metacognitive reflection on a completed task.

    Uses Gemini 3 Pro to analyze task outcome and generate insights.
    """
    nexus = get_nexus()

    insight = await nexus.metacognitive.reflect_on_task(
        task=request.task,
        outcome=request.outcome,
    )

    return ReflectResponse(
        insight_id=insight.insight_id,
        observation=insight.observation,
        causal_analysis=insight.causal_analysis,
        learning=insight.learning,
        action=insight.action,
        confidence=insight.confidence,
        category=insight.category,
        applied=insight.applied,
    )


@router.post("/evolve", response_model=EvolveResponse)
async def evolve_code(request: EvolveRequest):
    """
    Start evolutionary optimization of code or configuration.

    Uses genetic algorithms with Gemini 3 Pro fitness evaluation.
    """
    nexus = get_nexus()

    candidate = await nexus.evolution.evolve(
        target=request.target,
        goals=request.goals,
        seed_code=request.seed_code,
        generations=request.generations,
    )

    return EvolveResponse(
        candidate_id=candidate.candidate_id,
        fitness=candidate.fitness,
        generation=candidate.generation,
        code_preview=candidate.code[:500] if candidate.code else "",
    )


@router.get("/insights")
async def get_recent_insights(
    limit: int = 10,
    min_confidence: float = 0.0,
) -> List[InsightResponse]:
    """Get recent metacognitive insights."""
    nexus = get_nexus()

    insights = await nexus.metacognitive.get_recent_insights(
        limit=limit,
        min_confidence=min_confidence,
    )

    return [
        InsightResponse(
            insight_id=i.insight_id,
            timestamp=i.timestamp.isoformat(),
            observation=i.observation,
            causal_analysis=i.causal_analysis,
            learning=i.learning,
            action=i.action,
            confidence=i.confidence,
            category=i.category,
        )
        for i in insights
    ]


@router.post("/memory/store")
async def store_memory(request: MemoryStoreRequest) -> Dict[str, Any]:
    """Store content in NEXUS memory system."""
    nexus = get_nexus()

    try:
        level = MemoryLevel(request.level)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid memory level: {request.level}",
        )

    memory_id = await nexus.memory.store(
        content=request.content,
        level=level,
        importance=request.importance,
    )

    return {"memory_id": memory_id, "level": level.value}


@router.post("/memory/retrieve")
async def retrieve_memories(request: MemoryRetrieveRequest) -> List[Dict[str, Any]]:
    """Retrieve memories from specified level."""
    nexus = get_nexus()

    try:
        level = MemoryLevel(request.level)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid memory level: {request.level}",
        )

    memories = await nexus.memory.retrieve(
        level=level,
        limit=request.limit,
    )

    return [m.to_dict() for m in memories]


@router.get("/healing/history")
async def get_healing_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent self-healing history."""
    nexus = get_nexus()
    history = await nexus.healing.get_history(limit=limit)
    return [h.to_dict() for h in history]


@router.post("/mcp/connect")
async def connect_to_mcp() -> Dict[str, Any]:
    """Connect NEXUS to MCP collective."""
    nexus = get_nexus()
    success = await nexus.mcp.connect()
    return {"connected": success, "mcp_active": nexus.mcp.is_connected}


@router.post("/mcp/disconnect")
async def disconnect_from_mcp():
    """Disconnect NEXUS from MCP collective."""
    nexus = get_nexus()
    await nexus.mcp.disconnect()
    return {"connected": False}


@router.post("/mcp/broadcast")
async def broadcast_to_collective(message: Dict[str, Any]) -> Dict[str, Any]:
    """Broadcast message to MCP collective."""
    nexus = get_nexus()
    return await nexus.mcp.broadcast(message)


@router.get("/mcp/collective/status")
async def get_collective_status() -> Dict[str, Any]:
    """Get status of the MCP collective."""
    nexus = get_nexus()
    return await nexus.mcp.get_collective_status()
