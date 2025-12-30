"""
Vertice Core - Agency Foundation

Central module for the Vertice multi-agent system.

Phase 3 Integration:
- Hybrid Mesh Coordination
- A2A Protocol (Agent-to-Agent)
- Meta-Cognitive Reflection
- Comprehensive Benchmarks

Usage:
    from core import Agency, get_agency
    from core.mesh import HybridMeshMixin
    from core.protocols import A2AProtocolMixin
    from core.metacognition import MetaCognitiveMixin
    from core.benchmarks import BenchmarkMixin
"""

from .agency import Agency, AgencyConfig, get_agency

# Phase 3 modules
from .mesh import (
    HybridMeshMixin,
    CoordinationTopology,
    CoordinationPlane,
    MeshNode,
    TaskRoute,
    TopologySelector,
)
from .protocols import (
    A2AProtocolMixin,
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    A2ATask,
    TaskStatus,
)
from .metacognition import (
    MetaCognitiveMixin,
    ReflectionEngine,
    ExperienceMemory,
    ConfidenceCalibrator,
    ReflectionLevel,
    ReflectionOutcome,
)
from .benchmarks import (
    BenchmarkMixin,
    BenchmarkRunner,
    BenchmarkSuite,
    BenchmarkTask,
    BenchmarkResult,
    BenchmarkCategory,
)

__all__ = [
    # Agency
    "Agency",
    "AgencyConfig",
    "get_agency",
    # Mesh
    "HybridMeshMixin",
    "CoordinationTopology",
    "CoordinationPlane",
    "MeshNode",
    "TaskRoute",
    "TopologySelector",
    # A2A Protocol
    "A2AProtocolMixin",
    "AgentCard",
    "AgentCapabilities",
    "AgentSkill",
    "A2ATask",
    "TaskStatus",
    # Metacognition
    "MetaCognitiveMixin",
    "ReflectionEngine",
    "ExperienceMemory",
    "ConfidenceCalibrator",
    "ReflectionLevel",
    "ReflectionOutcome",
    # Benchmarks
    "BenchmarkMixin",
    "BenchmarkRunner",
    "BenchmarkSuite",
    "BenchmarkTask",
    "BenchmarkResult",
    "BenchmarkCategory",
]
