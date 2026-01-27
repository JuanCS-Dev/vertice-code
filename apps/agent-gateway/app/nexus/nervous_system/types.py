"""
Digital Nervous System - Types and Data Structures.

Contains all enums and dataclasses for the nervous system.
Follows CODE_CONSTITUTION.md standards for type safety and documentation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class SpikePattern(Enum):
    """
    Neuromorphic spike patterns (biological neural network inspired).

    Based on: Loihi chip (Intel) and TrueNorth (IBM) research.
    """

    BURST = "burst"  # Multiple rapid spikes = IMMINENT DANGER
    TONIC = "tonic"  # Regular spikes = Normal state
    IRREGULAR = "irregular"  # Chaotic patterns = Anomaly
    SILENT = "silent"  # No spikes = System dead/quiet


class AutonomyLevel(Enum):
    """Level at which incident was resolved."""

    L0_HUMAN = "human_required"
    L1_REFLEX = "reflex_arc"
    L2_INNATE = "innate_immunity"
    L3_ADAPTIVE = "adaptive_immunity"


class CellType(Enum):
    """Immune cell types for innate immunity layer."""

    NEUTROPHIL = "neutrophil"  # Fast cleanup
    MACROPHAGE = "macrophage"  # Log digestion
    NK_CELL = "nk_cell"  # Process termination


@dataclass
class ReflexResponse:
    """
    Deterministic reflex response (no consciousness needed).

    Attributes:
        action: The action to execute (e.g., scale_horizontal, circuit_break)
        target: Target resource for the action
        confidence: Confidence level (0-1)
        latency_ms: Response latency in milliseconds
        reason: Human-readable explanation
        bypass_nexus: Whether to skip higher cognitive layers
        executed: Whether the action was executed
        timestamp: When the response was created
    """

    action: str
    target: str
    confidence: float
    latency_ms: float
    reason: str
    bypass_nexus: bool = True
    executed: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class InnateResponse:
    """
    Response from innate immune system.

    Attributes:
        cell_type: Type of immune cell that responded
        action_taken: Description of action taken
        success: Whether the action succeeded
        latency_seconds: Response latency in seconds
        contained: Whether the threat was contained
        learning: Extracted learning for adaptive layer (optional)
    """

    cell_type: CellType
    action_taken: str
    success: bool
    latency_seconds: float
    contained: bool
    learning: Optional[str] = None


@dataclass
class NervousSystemEvent:
    """
    Normalized event from GCloud (Eventarc, Pub/Sub, Monitoring).

    Attributes:
        event_id: Unique event identifier
        source: Event source (eventarc, pubsub, monitoring, logging)
        event_type: CloudEvent type
        severity: Event severity (INFO, WARNING, ERROR, CRITICAL)
        resource_type: GCP resource type
        resource_name: Name of affected resource
        timestamp: Event timestamp
        payload: Raw event payload
        metrics: Extracted numeric metrics
    """

    event_id: str
    source: str  # eventarc, pubsub, monitoring, logging
    event_type: str
    severity: str  # INFO, WARNING, ERROR, CRITICAL
    resource_type: str
    resource_name: str
    timestamp: datetime
    payload: Dict[str, Any]
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class NervousSystemResult:
    """
    Result of nervous system processing.

    Attributes:
        event_id: Original event ID
        resolved: Whether the event was resolved autonomously
        autonomy_level: Level at which resolution occurred
        latency_ms: Total processing latency
        actions_taken: List of actions executed
        memory_formed: Whether immunological memory was created
        escalated_to_human: Whether human intervention is required
        details: Additional result details
    """

    event_id: str
    resolved: bool
    autonomy_level: AutonomyLevel
    latency_ms: float
    actions_taken: List[str]
    memory_formed: bool = False
    escalated_to_human: bool = False
    details: Dict[str, Any] = field(default_factory=dict)
