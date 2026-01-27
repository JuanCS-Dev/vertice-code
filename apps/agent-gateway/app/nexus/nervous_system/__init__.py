"""
Digital Nervous System Package.

Bio-inspired homeostatic infrastructure for autonomous self-healing.
Integrates with GCloud Eventarc, Pub/Sub, Cloud Monitoring, and Cloud Logging.

Architecture:
- Layer 1: Reflex Arc (15-100ms) - Neuromorphic spike-based computation
- Layer 2: Innate Immunity (1-10s) - Swarm micro-agents
- Layer 3: Adaptive Immunity (10s-min) - NEXUS + Prometheus

Success rate: >95% autonomous resolution.
"""

from nexus.nervous_system.types import (
    SpikePattern,
    AutonomyLevel,
    CellType,
    ReflexResponse,
    InnateResponse,
    NervousSystemEvent,
    NervousSystemResult,
)
from nexus.nervous_system.reflex_arc import (
    GanglionNeuron,
    ReflexGanglion,
)
from nexus.nervous_system.innate_immunity import (
    InnateImmuneSystem,
)
from nexus.nervous_system.event_parsers import (
    parse_eventarc_event,
    parse_pubsub_message,
    parse_monitoring_alert,
)
from nexus.nervous_system.orchestrator import (
    DigitalNervousSystem,
)

__all__ = [
    # Types
    "SpikePattern",
    "AutonomyLevel",
    "CellType",
    "ReflexResponse",
    "InnateResponse",
    "NervousSystemEvent",
    "NervousSystemResult",
    # Reflex Arc
    "GanglionNeuron",
    "ReflexGanglion",
    # Innate Immunity
    "InnateImmuneSystem",
    # Event Parsers
    "parse_eventarc_event",
    "parse_pubsub_message",
    "parse_monitoring_alert",
    # Orchestrator
    "DigitalNervousSystem",
]
