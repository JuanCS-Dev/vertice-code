"""
Mesh Coordination Types

Type definitions for hybrid mesh coordination.

Reference:
- arXiv:2512.08296 (Scaling Agent Systems)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set
from enum import Enum
from datetime import datetime


class CoordinationTopology(str, Enum):
    """
    Coordination topology patterns.

    Based on arXiv:2512.08296 findings.
    """

    INDEPENDENT = "independent"  # No inter-agent communication (17.2x error)
    CENTRALIZED = "centralized"  # Hub-and-spoke with orchestrator (4.4x error)
    DECENTRALIZED = "decentralized"  # Peer-to-peer mesh
    HYBRID = "hybrid"  # Strategic + tactical coordination


class CoordinationPlane(str, Enum):
    """Dual-plane architecture layers."""

    CONTROL = "control"  # Strategic orchestration
    WORKER = "worker"  # Tactical execution


class TaskCharacteristic(str, Enum):
    """Task characteristics for topology selection."""

    PARALLELIZABLE = "parallelizable"  # Best: Centralized (+80.8%)
    SEQUENTIAL = "sequential"  # Caution: MAS degrades -39% to -70%
    EXPLORATORY = "exploratory"  # Best: Decentralized (+9.2%)
    COMPLEX = "complex"  # Best: Hybrid


@dataclass
class MeshNode:
    """
    A node in the coordination mesh.

    Represents an agent with its connectivity.
    """

    id: str
    agent_id: str
    plane: CoordinationPlane
    connections: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    health_status: str = "healthy"
    last_heartbeat: str = field(default_factory=lambda: datetime.now().isoformat())

    def connect_to(self, node_id: str) -> None:
        """Establish connection to another node."""
        self.connections.add(node_id)

    def disconnect_from(self, node_id: str) -> None:
        """Remove connection to another node."""
        self.connections.discard(node_id)


@dataclass
class TaskRoute:
    """Routing decision for a task."""

    task_id: str
    topology: CoordinationTopology
    target_nodes: List[str]
    reasoning: str
    estimated_error_factor: float
    parallel: bool = False
    dependencies: List[str] = field(default_factory=list)
