"""
NEXUS Meta-Agent Module for Vertice Agent Gateway

Self-Evolving Intelligence powered by Gemini 3 Pro.
Implements M12 from LAUNCH_ROADMAP_GOOGLE_STACK_2026.md

Components:
- MetacognitiveEngine: Intrinsic self-reflection and learning
- SelfHealingOrchestrator: Autonomous system repair
- EvolutionaryCodeOptimizer: Genetic algorithm-based code evolution
- HierarchicalMemory: L1-L4 memory system with Firestore persistence
- NexusMetaAgent: Main orchestrator

Model: gemini-3-pro-preview (Gemini 3 Pro)
SDK: google-genai >= 1.51.0
"""

from nexus.config import NexusConfig
from nexus.types import (
    MetacognitiveInsight,
    EvolutionaryCandidate,
    SystemState,
    HealingAction,
    MemoryLevel,
)
from nexus.memory import HierarchicalMemory
from nexus.metacognitive import MetacognitiveEngine
from nexus.healing import SelfHealingOrchestrator
from nexus.evolution import EvolutionaryCodeOptimizer
from nexus.agent import NexusMetaAgent
from nexus.mcp_integration import NexusMCPIntegration
from nexus.prometheus_bridge import PrometheusBridge
from nexus.alloydb import AlloyDBStore
from nexus.nervous_system import (
    DigitalNervousSystem,
    NervousSystemEvent,
    NervousSystemResult,
    ReflexGanglion,
    InnateImmuneSystem,
    AutonomyLevel,
    SpikePattern,
    CellType,
    GanglionNeuron,
    ReflexResponse,
    InnateResponse,
    parse_eventarc_event,
    parse_pubsub_message,
    parse_monitoring_alert,
)
from nexus.eventarc_handler import (
    router as eventarc_router,
    get_nervous_system,
    connect_nexus_components,
)

__all__ = [
    # Core config
    "NexusConfig",
    # Types
    "MetacognitiveInsight",
    "EvolutionaryCandidate",
    "SystemState",
    "HealingAction",
    "MemoryLevel",
    # Memory
    "HierarchicalMemory",
    # Engines
    "MetacognitiveEngine",
    "SelfHealingOrchestrator",
    "EvolutionaryCodeOptimizer",
    # Main agent
    "NexusMetaAgent",
    # Integrations
    "NexusMCPIntegration",
    "PrometheusBridge",
    "AlloyDBStore",
    # Digital Nervous System
    "DigitalNervousSystem",
    "NervousSystemEvent",
    "NervousSystemResult",
    "ReflexGanglion",
    "InnateImmuneSystem",
    "AutonomyLevel",
    "SpikePattern",
    "CellType",
    "GanglionNeuron",
    "ReflexResponse",
    "InnateResponse",
    "parse_eventarc_event",
    "parse_pubsub_message",
    "parse_monitoring_alert",
    # Eventarc
    "eventarc_router",
    "get_nervous_system",
    "connect_nexus_components",
]
