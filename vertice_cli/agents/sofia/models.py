"""
Sofia Models - Type-Safe Data Structures for Counsel.

This module provides the data models for Sofia:
- CounselMetrics: Metrics for tracking counsel quality
- CounselRequest: Request for counsel
- CounselResponse: Response with counsel and transparency

Philosophy:
    "You don't replace human wisdom - you cultivate it."
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class CounselMetrics(BaseModel):
    """
    Metrics for counsel provided by Sofia.

    Tracks the quality and impact of counsel over time.
    """

    agent_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Counsel stats
    total_counsels: int = 0
    total_questions_asked: int = 0
    total_deliberations: int = 0

    # Quality metrics
    avg_confidence: float = 0.0
    avg_processing_time_ms: float = 0.0
    system2_activation_rate: float = 0.0

    # Virtue tracking
    virtues_expressed: Dict[str, int] = Field(default_factory=dict)

    # Counsel types distribution
    counsel_types: Dict[str, int] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "executor-1",
                "total_counsels": 42,
                "avg_confidence": 0.73,
                "system2_activation_rate": 0.35,
            }
        }


class CounselRequest(BaseModel):
    """Request for counsel from Sofia."""

    query: str = Field(..., description="The question or situation requiring counsel")
    session_id: Optional[str] = Field(None, description="Session ID for continuity")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    force_system2: bool = Field(False, description="Force System 2 deliberation")


class CounselResponse(BaseModel):
    """Response from Sofia with counsel."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Request
    original_query: str
    session_id: Optional[str] = None

    # Counsel
    counsel: str
    counsel_type: str
    thinking_mode: str

    # Process transparency
    questions_asked: List[str] = Field(default_factory=list)
    virtues_expressed: List[str] = Field(default_factory=list)

    # Meta
    confidence: float = 0.5
    processing_time_ms: float = 0.0
    community_suggested: bool = False
    requires_professional: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "counsel": "Let me ask you: what are the core values that would guide this decision?",
                "counsel_type": "EXPLORING",
                "thinking_mode": "SYSTEM_2",
                "confidence": 0.65,
            }
        }


__all__ = [
    "CounselMetrics",
    "CounselRequest",
    "CounselResponse",
]
