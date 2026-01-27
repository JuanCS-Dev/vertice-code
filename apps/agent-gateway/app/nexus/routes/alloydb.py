"""
NEXUS AlloyDB Routes.

Endpoints for AlloyDB persistent store: memories, insights, evolution candidates.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter

from nexus.agent import get_nexus
from nexus.types import MemoryLevel
from nexus.schemas import (
    SemanticSearchRequest,
    InsightSearchRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alloydb", tags=["alloydb"])


@router.get("/status")
async def get_alloydb_status() -> Dict[str, Any]:
    """Get AlloyDB persistent store status and statistics."""
    nexus = get_nexus()
    return await nexus.alloydb.get_stats()


@router.post("/initialize")
async def initialize_alloydb():
    """Initialize AlloyDB connection and schema."""
    nexus = get_nexus()
    success = await nexus.alloydb.initialize()
    return {
        "initialized": success,
        "project_id": nexus.alloydb.project_id,
        "cluster": nexus.alloydb.cluster,
    }


@router.post("/memories/search")
async def search_memories_semantic(request: SemanticSearchRequest) -> List[Dict[str, Any]]:
    """
    Semantic search across memories using Vertex AI embeddings.

    Uses pgvector for efficient vector similarity search.
    """
    nexus = get_nexus()

    level = MemoryLevel(request.level) if request.level else None

    results = await nexus.alloydb.search_memories(
        query=request.query,
        level=level,
        limit=request.limit,
        min_similarity=request.min_similarity,
    )

    return [
        {
            "memory": block.to_dict(),
            "similarity": similarity,
        }
        for block, similarity in results
    ]


@router.post("/insights/search")
async def search_insights_semantic(request: InsightSearchRequest) -> List[Dict[str, Any]]:
    """
    Semantic search across metacognitive insights.

    Find similar past insights for pattern recognition.
    """
    nexus = get_nexus()

    results = await nexus.alloydb.search_insights(
        query=request.query,
        limit=request.limit,
        min_confidence=request.min_confidence,
    )

    return [
        {
            "insight": insight.to_dict(),
            "similarity": similarity,
        }
        for insight, similarity in results
    ]


@router.get("/evolution/best")
async def get_best_evolution_candidates(limit: int = 10) -> List[Dict[str, Any]]:
    """Get best evolutionary candidates by fitness score."""
    nexus = get_nexus()
    candidates = await nexus.alloydb.get_best_candidates(limit=limit)
    return [c.to_dict() for c in candidates]


@router.post("/state/save")
async def save_system_state():
    """Manually save current system state to AlloyDB."""
    nexus = get_nexus()
    success = await nexus.alloydb.save_state(nexus.state)
    return {"saved": success}


@router.get("/state/load")
async def load_latest_state() -> Dict[str, Any]:
    """Load most recent system state from AlloyDB."""
    nexus = get_nexus()
    state = await nexus.alloydb.load_latest_state()
    if state:
        return {"found": True, "state": state.to_dict()}
    return {"found": False}
