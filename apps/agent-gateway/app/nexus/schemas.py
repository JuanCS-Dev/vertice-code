"""
NEXUS API Schemas.

Pydantic models for request/response validation in the NEXUS REST API.
Follows CODE_CONSTITUTION.md standards for type safety and documentation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# CORE NEXUS SCHEMAS
# =============================================================================


class NexusStatusResponse(BaseModel):
    """NEXUS status response."""

    active: bool
    model: str
    thinking_level: str
    total_insights: int
    total_healings: int
    total_evolutions: int
    uptime_seconds: float
    last_reflection: Optional[str] = None


class InsightResponse(BaseModel):
    """Insight response."""

    insight_id: str
    timestamp: str
    observation: str
    causal_analysis: str
    learning: str
    action: str
    confidence: float
    category: str


# =============================================================================
# REFLECTION SCHEMAS
# =============================================================================


class ReflectRequest(BaseModel):
    """Request for metacognitive reflection."""

    task: Dict[str, Any] = Field(..., description="Task details")
    outcome: Dict[str, Any] = Field(..., description="Task outcome")


class ReflectResponse(BaseModel):
    """Response from metacognitive reflection."""

    insight_id: str
    observation: str
    causal_analysis: str
    learning: str
    action: str
    confidence: float
    category: str
    applied: bool = False


# =============================================================================
# EVOLUTION SCHEMAS
# =============================================================================


class EvolveRequest(BaseModel):
    """Request for evolutionary optimization."""

    target: str = Field(..., description="What to optimize")
    goals: List[str] = Field(..., description="Optimization goals")
    seed_code: Optional[str] = Field(None, description="Optional seed code")
    generations: int = Field(30, ge=1, le=100, description="Number of generations")


class EvolveResponse(BaseModel):
    """Response from evolutionary optimization."""

    candidate_id: str
    fitness: float
    generation: int
    code_preview: str


# =============================================================================
# MEMORY SCHEMAS
# =============================================================================


class MemoryStoreRequest(BaseModel):
    """Request to store memory."""

    content: str = Field(..., description="Content to store")
    level: str = Field(
        "L2_EPISODIC",
        description="Memory level: L1_WORKING, L2_EPISODIC, L3_SEMANTIC, L4_PROCEDURAL",
    )
    importance: float = Field(0.5, ge=0.0, le=1.0, description="Importance score")


class MemoryRetrieveRequest(BaseModel):
    """Request to retrieve memories."""

    level: str = Field(
        "L2_EPISODIC",
        description="Memory level to retrieve from",
    )
    limit: int = Field(10, ge=1, le=100, description="Max memories to return")


class SemanticSearchRequest(BaseModel):
    """Request for semantic memory search."""

    query: str = Field(..., description="Search query")
    level: Optional[str] = Field(None, description="Memory level to search")
    limit: int = Field(10, ge=1, le=100, description="Max results")
    min_similarity: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity")


class InsightSearchRequest(BaseModel):
    """Request for semantic insight search."""

    query: str = Field(..., description="Search query")
    limit: int = Field(10, ge=1, le=50, description="Max results")
    min_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Minimum confidence")


class MemoryQueryRequest(BaseModel):
    """Request for Prometheus memory query."""

    query: str = Field(..., description="Query string")
    memory_type: str = Field("all", description="Memory type to query")


# =============================================================================
# PROMETHEUS BRIDGE SCHEMAS
# =============================================================================


class SimulateRequest(BaseModel):
    """Request for world model simulation."""

    action: str = Field(..., description="Action to simulate")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ReflectionRequest(BaseModel):
    """Request for Prometheus reflection."""

    task: str = Field(..., description="Task that was executed")
    outcome: Dict[str, Any] = Field(..., description="Task outcome")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ToolCreationRequest(BaseModel):
    """Request for dynamic tool creation."""

    description: str = Field(..., description="Tool description")
    requirements: Optional[List[str]] = Field(None, description="Tool requirements")


class DelegateRequest(BaseModel):
    """Request for task delegation to Prometheus."""

    task: str = Field(..., description="Task to delegate")
    use_world_model: bool = Field(True, description="Use world model simulation")
    use_memory: bool = Field(True, description="Use memory system")


# =============================================================================
# HEALING SCHEMAS
# =============================================================================


class HealingRequest(BaseModel):
    """Request for healing diagnosis."""

    symptoms: List[str] = Field(..., description="Observed symptoms")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class HealingResponse(BaseModel):
    """Response from healing diagnosis."""

    diagnosis: str
    recommended_actions: List[str]
    confidence: float
    executed: bool = False


# =============================================================================
# NERVOUS SYSTEM SCHEMAS
# =============================================================================


class NervousEventRequest(BaseModel):
    """Request to process event through nervous system."""

    event_id: str = Field(..., description="Unique event ID")
    source: str = Field("manual", description="Event source")
    event_type: str = Field(..., description="Event type")
    severity: str = Field("INFO", description="Severity level")
    resource_type: str = Field("unknown", description="Resource type")
    resource_name: str = Field("unknown", description="Resource name")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event payload")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Event metrics")


# =============================================================================
# EVENTARC SCHEMAS
# =============================================================================


class CloudEventData(BaseModel):
    """CloudEvents data structure."""

    specversion: str = Field(default="1.0", description="CloudEvents spec version")
    id: str = Field(..., description="Event ID")
    source: str = Field(..., description="Event source URI")
    type: str = Field(..., description="Event type")
    time: Optional[str] = Field(None, description="Event timestamp")
    datacontenttype: Optional[str] = Field(None, description="Content type")
    data: Optional[Dict[str, Any]] = Field(None, description="Event payload")
    subject: Optional[str] = Field(None, description="Event subject")


class EventarcResponse(BaseModel):
    """Response from Eventarc handler."""

    event_id: str
    processed: bool
    autonomy_level: str
    latency_ms: float
    actions_taken: List[str]
    escalated: bool = False
    details: Optional[Dict[str, Any]] = None


class NervousSystemStatsResponse(BaseModel):
    """Statistics from the Nervous System."""

    total_events: int
    autonomous_resolution_rate: float
    reflex_rate: float
    innate_rate: float
    adaptive_rate: float
    human_escalation_rate: float
    homeostasis_achieved: bool
    by_layer: Dict[str, int]
