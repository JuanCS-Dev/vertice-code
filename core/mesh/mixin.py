"""
Hybrid Mesh Mixin

Mixin providing hybrid mesh coordination capabilities.

Reference:
- arXiv:2512.08296 (Scaling Agent Systems)
- McKinsey Agentic AI Mesh Architecture
"""

from __future__ import annotations

import uuid
import logging
from typing import Any, Callable, Dict, List, Optional

from .types import (
    CoordinationTopology,
    CoordinationPlane,
    TaskCharacteristic,
    MeshNode,
    TaskRoute,
)
from .topology import TopologySelector

logger = logging.getLogger(__name__)


class HybridMeshMixin:
    """
    Mixin providing hybrid mesh coordination capabilities.

    Implements dual-plane architecture:
    - Control Plane: Strategic orchestration, goal decomposition
    - Worker Plane: Tactical execution, peer-to-peer collaboration
    """

    def _init_mesh(self) -> None:
        """Initialize hybrid mesh coordination."""
        self._mesh_nodes: Dict[str, MeshNode] = {}
        self._topology_selector = TopologySelector()
        self._active_routes: Dict[str, TaskRoute] = {}
        self._mesh_initialized = True

        self_node = MeshNode(
            id=str(uuid.uuid4()),
            agent_id=getattr(self, "name", "orchestrator"),
            plane=CoordinationPlane.CONTROL,
        )
        self._mesh_nodes[self_node.id] = self_node
        self._control_node_id = self_node.id

        logger.info("[HybridMesh] Initialized control plane")

    def register_worker(
        self,
        agent_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MeshNode:
        """Register a worker agent in the mesh."""
        if not hasattr(self, "_mesh_nodes"):
            self._init_mesh()

        node = MeshNode(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            plane=CoordinationPlane.WORKER,
            metadata=metadata or {},
        )

        node.connect_to(self._control_node_id)
        self._mesh_nodes[self._control_node_id].connect_to(node.id)
        self._mesh_nodes[node.id] = node

        logger.info(f"[HybridMesh] Registered worker: {agent_id}")
        return node

    def create_tactical_mesh(
        self,
        agent_ids: List[str],
        full_mesh: bool = False,
    ) -> List[MeshNode]:
        """
        Create a tactical mesh between worker agents.

        Args:
            agent_ids: Agents to include in the mesh
            full_mesh: If True, connect all agents to each other
        """
        if not hasattr(self, "_mesh_nodes"):
            self._init_mesh()

        nodes = []
        for agent_id in agent_ids:
            node = self._find_node_by_agent(agent_id)
            if not node:
                node = self.register_worker(agent_id)
            nodes.append(node)

        if full_mesh:
            for i, node_a in enumerate(nodes):
                for node_b in nodes[i + 1:]:
                    node_a.connect_to(node_b.id)
                    node_b.connect_to(node_a.id)
        else:
            for i in range(len(nodes)):
                next_idx = (i + 1) % len(nodes)
                nodes[i].connect_to(nodes[next_idx].id)
                nodes[next_idx].connect_to(nodes[i].id)

        logger.info(
            f"[HybridMesh] Created tactical mesh with {len(nodes)} nodes "
            f"({'full' if full_mesh else 'ring'} connectivity)"
        )
        return nodes

    def _find_node_by_agent(self, agent_id: str) -> Optional[MeshNode]:
        """Find a mesh node by agent ID."""
        if not hasattr(self, "_mesh_nodes"):
            return None
        for node in self._mesh_nodes.values():
            if node.agent_id == agent_id:
                return node
        return None

    def route_task(
        self,
        task_id: str,
        task_description: str,
        target_agents: List[str],
        prefer_parallel: bool = True,
    ) -> TaskRoute:
        """Route a task through the mesh with optimal topology."""
        if not hasattr(self, "_mesh_nodes"):
            self._init_mesh()

        characteristic = self._classify_task(task_description)
        topology = self._topology_selector.select(
            task_characteristic=characteristic,
            prefer_error_containment=True,
        )

        target_nodes = []
        for agent_id in target_agents:
            node = self._find_node_by_agent(agent_id)
            if node:
                target_nodes.append(node.id)

        route = TaskRoute(
            task_id=task_id,
            topology=topology,
            target_nodes=target_nodes,
            reasoning=f"Task classified as {characteristic.value}, "
                      f"selected {topology.value} topology",
            estimated_error_factor=self._topology_selector.get_error_factor(topology),
            parallel=prefer_parallel and characteristic == TaskCharacteristic.PARALLELIZABLE,
        )

        self._active_routes[task_id] = route
        logger.info(f"[HybridMesh] Routed task {task_id} via {topology.value}")
        return route

    def _classify_task(self, description: str) -> TaskCharacteristic:
        """
        Classify task characteristic from description.

        Uses word boundary matching to avoid false positives
        (e.g., "authentication" containing "then").
        """
        import re
        desc_lower = description.lower()

        def has_word(keywords: list) -> bool:
            """Check if any keyword exists as a whole word."""
            for kw in keywords:
                # Use word boundaries for single words, exact match for phrases
                if ' ' in kw:
                    if kw in desc_lower:
                        return True
                else:
                    if re.search(rf'\b{re.escape(kw)}\b', desc_lower):
                        return True
            return False

        if has_word(["parallel", "batch", "concurrent", "multiple"]):
            return TaskCharacteristic.PARALLELIZABLE
        if has_word(["step by step", "sequential", "then ", " then", "after that"]):
            return TaskCharacteristic.SEQUENTIAL
        if has_word(["explore", "search", "find", "navigate", "discover"]):
            return TaskCharacteristic.EXPLORATORY
        if has_word(["complex", "multi-step", "architecture", "design"]):
            return TaskCharacteristic.COMPLEX

        return TaskCharacteristic.PARALLELIZABLE

    async def execute_via_mesh(
        self,
        task_id: str,
        execute_fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute a task through the mesh."""
        if not hasattr(self, "_active_routes"):
            raise ValueError(f"No route found for task {task_id}")

        route = self._active_routes.get(task_id)
        if not route:
            raise ValueError(f"No route found for task {task_id}")

        if route.topology == CoordinationTopology.CENTRALIZED:
            result = await self._execute_centralized(execute_fn, route, *args, **kwargs)
        elif route.topology == CoordinationTopology.DECENTRALIZED:
            result = await self._execute_decentralized(execute_fn, route, *args, **kwargs)
        elif route.topology == CoordinationTopology.HYBRID:
            result = await self._execute_hybrid(execute_fn, route, *args, **kwargs)
        else:
            result = await execute_fn(*args, **kwargs)

        return result

    async def _execute_centralized(
        self, execute_fn: Callable[..., Any], route: TaskRoute, *args: Any, **kwargs: Any
    ) -> Any:
        """Execute with centralized coordination."""
        logger.info(f"[HybridMesh] Centralized execution for {route.task_id}")
        return await execute_fn(*args, **kwargs)

    async def _execute_decentralized(
        self, execute_fn: Callable[..., Any], route: TaskRoute, *args: Any, **kwargs: Any
    ) -> Any:
        """Execute with decentralized coordination."""
        logger.info(f"[HybridMesh] Decentralized execution for {route.task_id}")
        return await execute_fn(*args, **kwargs)

    async def _execute_hybrid(
        self, execute_fn: Callable[..., Any], route: TaskRoute, *args: Any, **kwargs: Any
    ) -> Any:
        """Execute with hybrid coordination."""
        logger.info(f"[HybridMesh] Hybrid execution for {route.task_id}")
        return await execute_fn(*args, **kwargs)

    def get_mesh_status(self) -> Dict[str, Any]:
        """Get mesh status."""
        if not hasattr(self, "_mesh_nodes"):
            return {"initialized": False}

        workers = [
            n for n in self._mesh_nodes.values()
            if n.plane == CoordinationPlane.WORKER
        ]

        return {
            "initialized": True,
            "total_nodes": len(self._mesh_nodes),
            "control_nodes": 1,
            "worker_nodes": len(workers),
            "active_routes": len(getattr(self, "_active_routes", {})),
            "topology_stats": {
                t.value: len([
                    r for r in getattr(self, "_active_routes", {}).values()
                    if r.topology == t
                ])
                for t in CoordinationTopology
            },
        }

    def get_topology_recommendation(
        self,
        task_description: str,
        agent_baseline: float = 0.3,
    ) -> Dict[str, Any]:
        """Get topology recommendation for a task."""
        if not hasattr(self, "_topology_selector"):
            self._init_mesh()

        characteristic = self._classify_task(task_description)
        topology = self._topology_selector.select(
            task_characteristic=characteristic,
            agent_baseline_performance=agent_baseline,
        )
        error_factor = self._topology_selector.get_error_factor(topology)

        return {
            "task_characteristic": characteristic.value,
            "recommended_topology": topology.value,
            "error_amplification_factor": error_factor,
            "parallel_execution": characteristic == TaskCharacteristic.PARALLELIZABLE,
            "warning": (
                "Sequential task - MAS may degrade performance by 39-70%"
                if characteristic == TaskCharacteristic.SEQUENTIAL
                else None
            ),
        }
