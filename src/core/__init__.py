"""
Vertice Core - Backward Compatibility Layer

Re-exports everything from vertice_core for backward compatibility.
This module is deprecated; import from vertice_core directly.

Usage:
    from core import Agency, get_agency  # Still works, but deprecated
    # Preferred: from vertice_core import Agency, get_agency
"""

# Re-export everything from vertice_core
from vertice_core import *

# Additional imports for backward compatibility
from vertice_core.agency import Agency, AgencyConfig, get_agency
from vertice_core.simple_agents import Agent as SimpleAgent, AgentConfig, Handoff
from vertice_core.a2a import A2AProtocolMixin, AgentCard, AgentCapabilities, AgentSkill, A2ATask
from vertice_core.mesh import (
    HybridMeshMixin,
    CoordinationTopology,
    CoordinationPlane,
    MeshNode,
    TaskRoute,
    TopologySelector,
)
from vertice_core.metacognition import (
    MetaCognitiveMixin,
    ReflectionEngine,
    ExperienceMemory,
    ConfidenceCalibrator,
    ReflectionLevel,
    ReflectionOutcome,
)
from vertice_core.benchmarks import (
    BenchmarkMixin,
    BenchmarkRunner,
    BenchmarkSuite,
    BenchmarkTask,
    BenchmarkResult,
    BenchmarkCategory,
)
