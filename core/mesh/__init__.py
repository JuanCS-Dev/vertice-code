"""
Vertice Mesh - Hybrid Multi-Agent Coordination

Phase 3 Integration:
- Hybrid Mesh Architecture (strategic + tactical)
- Dual-Plane Coordination (control plane + worker plane)
- Dynamic Topology Selection

Reference:
- arXiv:2512.08296 (Scaling Agent Systems)
- McKinsey Agentic AI Mesh Architecture
"""

from .types import (
    CoordinationTopology,
    CoordinationPlane,
    TaskCharacteristic,
    MeshNode,
    TaskRoute,
)
from .topology import TopologySelector
from .mixin import HybridMeshMixin

__all__ = [
    "HybridMeshMixin",
    "CoordinationTopology",
    "CoordinationPlane",
    "TaskCharacteristic",
    "MeshNode",
    "TaskRoute",
    "TopologySelector",
]
