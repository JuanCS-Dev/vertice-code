"""
Observability REST API Router.

Endpoints for:
- Feedback submission and retrieval
- Cost and usage tracking
- Telemetry metrics

Part of M10: Agentic Observability & Feedback Loop.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from observability.feedback import FeedbackService
from observability.cost_tracker import get_cost_tracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/observability", tags=["observability"])

# Global feedback service
_feedback_service: Optional[FeedbackService] = None


def get_feedback_service() -> FeedbackService:
    """Get or create feedback service."""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service


# ============================================================================
# Request/Response Models
# ============================================================================


class FeedbackRequest(BaseModel):
    """Request to submit feedback on a run."""

    score: int = Field(..., ge=-1, le=1, description="Score: -1 (bad), 0 (neutral), 1 (good)")
    comment: Optional[str] = Field(None, max_length=1000, description="Optional comment")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class FeedbackResponse(BaseModel):
    """Response from feedback submission."""

    feedback_id: str
    run_id: str
    score: int
    feedback_type: str
    timestamp: str


class UsageResponse(BaseModel):
    """Token usage response."""

    run_id: str
    operations: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    total_latency_ms: float
    avg_latency_ms: float


class AggregateStatsResponse(BaseModel):
    """Aggregate feedback statistics."""

    total_feedback: int
    positive_count: int
    negative_count: int
    neutral_count: int
    satisfaction_rate: float
    avg_score: float
    period_days: int


# ============================================================================
# Feedback Endpoints
# ============================================================================


@router.post("/runs/{run_id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    run_id: str,
    request: FeedbackRequest,
    user_id: str = "anonymous",  # TODO: Get from auth context
    org_id: str = "default",  # TODO: Get from tenant context
) -> FeedbackResponse:
    """
    Submit feedback for a run.

    Users can rate agent responses with:
    - 👍 (score=1): Positive feedback
    - 👎 (score=-1): Negative feedback
    - 😐 (score=0): Neutral

    This data is used for RLHF to improve agent responses.
    """
    service = get_feedback_service()

    try:
        record = await service.submit_feedback(
            run_id=run_id,
            user_id=user_id,
            org_id=org_id,
            score=request.score,
            comment=request.comment,
            metadata=request.metadata,
        )

        return FeedbackResponse(
            feedback_id=record.feedback_id,
            run_id=record.run_id,
            score=record.score,
            feedback_type=record.feedback_type.value,
            timestamp=record.timestamp.isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/feedback", response_model=List[FeedbackResponse])
async def get_run_feedback(run_id: str) -> List[FeedbackResponse]:
    """Get all feedback for a specific run."""
    service = get_feedback_service()
    records = await service.get_feedback_for_run(run_id)

    return [
        FeedbackResponse(
            feedback_id=r.feedback_id,
            run_id=r.run_id,
            score=r.score,
            feedback_type=r.feedback_type.value,
            timestamp=r.timestamp.isoformat(),
        )
        for r in records
    ]


@router.get("/feedback/stats", response_model=AggregateStatsResponse)
async def get_feedback_stats(
    org_id: Optional[str] = None,
    days: int = 30,
) -> AggregateStatsResponse:
    """Get aggregate feedback statistics."""
    service = get_feedback_service()
    stats = await service.get_aggregate_stats(org_id=org_id, days=days)

    return AggregateStatsResponse(
        total_feedback=stats["total_feedback"],
        positive_count=stats["positive_count"],
        negative_count=stats["negative_count"],
        neutral_count=stats["neutral_count"],
        satisfaction_rate=stats["satisfaction_rate"],
        avg_score=stats["avg_score"],
        period_days=stats["period_days"],
    )


# ============================================================================
# Cost & Usage Endpoints
# ============================================================================


@router.get("/runs/{run_id}/usage", response_model=UsageResponse)
async def get_run_usage(run_id: str) -> UsageResponse:
    """Get token usage and cost for a specific run."""
    tracker = get_cost_tracker()
    usage = tracker.get_run_cost(run_id)

    return UsageResponse(
        run_id=usage["run_id"],
        operations=usage["operations"],
        input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"],
        total_tokens=usage["total_tokens"],
        estimated_cost_usd=usage["estimated_cost_usd"],
        total_latency_ms=usage["total_latency_ms"],
        avg_latency_ms=usage["avg_latency_ms"],
    )


@router.get("/usage/total")
async def get_total_usage() -> Dict[str, Any]:
    """Get total token usage and cost across all operations."""
    tracker = get_cost_tracker()
    return tracker.get_total_cost()


@router.get("/usage/recent")
async def get_recent_usage(limit: int = 100) -> List[Dict[str, Any]]:
    """Get recent usage records."""
    tracker = get_cost_tracker()
    return tracker.get_recent_usage(limit=limit)


@router.get("/stats")
async def get_observability_stats() -> Dict[str, Any]:
    """Get observability system statistics."""
    feedback_service = get_feedback_service()
    tracker = get_cost_tracker()

    return {
        "feedback": feedback_service.get_stats(),
        "cost_tracker": tracker.get_stats(),
    }
