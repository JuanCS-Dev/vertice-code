"""
Knowledge Graph

Graph structure for entity and concept relationships.

References:
- arXiv:2501.00309 (GraphRAG Survey)
- arXiv:2404.16130 (KG²RAG)
- PageRank (Page et al., 1999)
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .types import (
    KnowledgeNode,
    KnowledgeEdge,
    NodeType,
    EdgeType,
    GraphContext,
    KnowledgeConfig,
)

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """
    Knowledge graph for enhanced retrieval.

    Implements:
    - Node and edge management
    - PageRank for node importance
    - Multi-hop path finding
    - Subgraph extraction

    References:
    - arXiv:2501.00309: GraphRAG components
    - arXiv:2404.16130: KG²RAG chunk expansion
    """

    def __init__(
        self,
        config: Optional[KnowledgeConfig] = None,
        persistence_path: Optional[Path] = None,
    ):
        """
        Initialize knowledge graph.

        Args:
            config: Knowledge configuration
            persistence_path: Path for graph persistence
        """
        self._config = config or KnowledgeConfig()
        self._persistence_path = persistence_path

        # Graph structure
        self._nodes: Dict[str, KnowledgeNode] = {}
        self._edges: Dict[str, KnowledgeEdge] = {}
        self._adjacency: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_adjacency: Dict[str, Set[str]] = defaultdict(set)

        # Edge lookup by source-target
        self._edge_lookup: Dict[Tuple[str, str], str] = {}

        # PageRank scores
        self._pagerank_computed = False

        if persistence_path and persistence_path.exists():
            self._load_from_disk()

    def add_node(self, node: KnowledgeNode) -> None:
        """
        Add a node to the graph.

        Args:
            node: Node to add
        """
        self._nodes[node.id] = node
        self._pagerank_computed = False

    def add_edge(self, edge: KnowledgeEdge) -> None:
        """
        Add an edge to the graph.

        Args:
            edge: Edge to add
        """
        self._edges[edge.id] = edge
        self._adjacency[edge.source_id].add(edge.target_id)
        self._reverse_adjacency[edge.target_id].add(edge.source_id)
        self._edge_lookup[(edge.source_id, edge.target_id)] = edge.id

        # Update node degrees
        if edge.source_id in self._nodes:
            self._nodes[edge.source_id].out_degree += 1
        if edge.target_id in self._nodes:
            self._nodes[edge.target_id].in_degree += 1

        self._pagerank_computed = False

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get a node by ID."""
        return self._nodes.get(node_id)

    def get_edge(self, source_id: str, target_id: str) -> Optional[KnowledgeEdge]:
        """Get an edge by source and target."""
        edge_id = self._edge_lookup.get((source_id, target_id))
        if edge_id:
            return self._edges.get(edge_id)
        return None

    def get_neighbors(
        self,
        node_id: str,
        max_hops: int = 1,
        edge_types: Optional[List[EdgeType]] = None,
    ) -> List[str]:
        """
        Get neighbor node IDs within max_hops.

        Args:
            node_id: Starting node
            max_hops: Maximum hop distance
            edge_types: Filter by edge types

        Returns:
            List of neighbor node IDs
        """
        if max_hops < 1:
            return []

        visited = {node_id}
        current_level = {node_id}
        all_neighbors = []

        for _ in range(max_hops):
            next_level = set()

            for current_id in current_level:
                # Outgoing edges
                for neighbor_id in self._adjacency.get(current_id, set()):
                    if neighbor_id not in visited:
                        # Check edge type filter
                        if edge_types:
                            edge = self.get_edge(current_id, neighbor_id)
                            if edge and edge.edge_type not in edge_types:
                                continue

                        visited.add(neighbor_id)
                        next_level.add(neighbor_id)
                        all_neighbors.append(neighbor_id)

                # Incoming edges (undirected traversal)
                for neighbor_id in self._reverse_adjacency.get(current_id, set()):
                    if neighbor_id not in visited:
                        if edge_types:
                            edge = self.get_edge(neighbor_id, current_id)
                            if edge and edge.edge_type not in edge_types:
                                continue

                        visited.add(neighbor_id)
                        next_level.add(neighbor_id)
                        all_neighbors.append(neighbor_id)

            current_level = next_level

        return all_neighbors

    def get_node_importance(self, node_id: str) -> float:
        """
        Get importance score for a node (PageRank).

        Args:
            node_id: Node ID

        Returns:
            Importance score (0-1)
        """
        if not self._pagerank_computed:
            self._compute_pagerank()

        node = self._nodes.get(node_id)
        return node.pagerank if node else 0.0

    def get_subgraph(
        self,
        node_ids: List[str],
        include_edges: bool = True,
    ) -> Tuple[List[KnowledgeNode], List[KnowledgeEdge]]:
        """
        Extract a subgraph containing specified nodes.

        Args:
            node_ids: Node IDs to include
            include_edges: Whether to include connecting edges

        Returns:
            Tuple of (nodes, edges)
        """
        nodes = [self._nodes[nid] for nid in node_ids if nid in self._nodes]
        edges = []

        if include_edges:
            node_set = set(node_ids)
            for edge in self._edges.values():
                if edge.source_id in node_set and edge.target_id in node_set:
                    edges.append(edge)

        return nodes, edges

    def get_graph_context(
        self,
        node_id: str,
        max_hops: int = 1,
    ) -> GraphContext:
        """
        Get graph context around a node (KG²RAG style).

        Args:
            node_id: Central node
            max_hops: Context radius

        Returns:
            GraphContext with neighborhood
        """
        neighbor_ids = self.get_neighbors(node_id, max_hops)
        nodes, edges = self.get_subgraph([node_id] + neighbor_ids)

        # Build expanded context text
        context_parts = []
        central_node = self._nodes.get(node_id)
        if central_node:
            context_parts.append(f"[Central] {central_node.content}")

        for node in nodes:
            if node.id != node_id:
                context_parts.append(f"[Related] {node.content}")

        # Compute subgraph metrics
        n_nodes = len(nodes)
        n_edges = len(edges)
        max_edges = n_nodes * (n_nodes - 1) / 2 if n_nodes > 1 else 1
        density = n_edges / max_edges if max_edges > 0 else 0.0

        return GraphContext(
            central_node_id=node_id,
            neighborhood_nodes=nodes,
            connecting_edges=edges,
            expanded_context="\n".join(context_parts),
            subgraph_density=density,
        )

    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_length: int = 5,
    ) -> Optional[List[str]]:
        """
        Find shortest path between two nodes (BFS).

        Args:
            source_id: Starting node
            target_id: Target node
            max_length: Maximum path length

        Returns:
            List of node IDs in path, or None if no path
        """
        if source_id not in self._nodes or target_id not in self._nodes:
            return None

        if source_id == target_id:
            return [source_id]

        # BFS
        queue = [(source_id, [source_id])]
        visited = {source_id}

        while queue:
            current_id, path = queue.pop(0)

            if len(path) > max_length:
                continue

            for neighbor_id in self._adjacency.get(current_id, set()):
                if neighbor_id == target_id:
                    return path + [neighbor_id]

                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))

        return None

    def _compute_pagerank(
        self,
        damping: float = 0.85,
        max_iterations: int = 100,
        tolerance: float = 1e-6,
    ) -> None:
        """
        Compute PageRank scores for all nodes.

        Args:
            damping: Damping factor
            max_iterations: Maximum iterations
            tolerance: Convergence tolerance
        """
        n = len(self._nodes)
        if n == 0:
            return

        # Initialize
        initial_score = 1.0 / n
        for node in self._nodes.values():
            node.pagerank = initial_score

        # Iterate
        for _ in range(max_iterations):
            new_scores = {}
            max_diff = 0.0

            for node_id, node in self._nodes.items():
                # Sum of incoming PageRank
                incoming_sum = 0.0
                for source_id in self._reverse_adjacency.get(node_id, set()):
                    source_node = self._nodes.get(source_id)
                    if source_node and source_node.out_degree > 0:
                        incoming_sum += source_node.pagerank / source_node.out_degree

                # PageRank formula
                new_score = (1 - damping) / n + damping * incoming_sum
                new_scores[node_id] = new_score
                max_diff = max(max_diff, abs(new_score - node.pagerank))

            # Update scores
            for node_id, score in new_scores.items():
                self._nodes[node_id].pagerank = score

            # Check convergence
            if max_diff < tolerance:
                break

        self._pagerank_computed = True
        logger.debug(f"[Graph] Computed PageRank for {n} nodes")

    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            "num_nodes": len(self._nodes),
            "num_edges": len(self._edges),
            "avg_degree": (
                sum(n.in_degree + n.out_degree for n in self._nodes.values()) / len(self._nodes)
                if self._nodes
                else 0.0
            ),
            "density": (
                len(self._edges) / (len(self._nodes) * (len(self._nodes) - 1))
                if len(self._nodes) > 1
                else 0.0
            ),
        }

    def save(self) -> None:
        """Save graph to disk."""
        if not self._persistence_path:
            return

        data = {
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [e.to_dict() for e in self._edges.values()],
        }

        self._persistence_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._persistence_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"[Graph] Saved to {self._persistence_path}")

    def _load_from_disk(self) -> None:
        """Load graph from disk."""
        with open(self._persistence_path) as f:
            data = json.load(f)

        for node_data in data.get("nodes", []):
            node = KnowledgeNode(
                id=node_data["id"],
                node_type=NodeType(node_data["type"]),
                content=node_data.get("content", ""),
                label=node_data.get("label", ""),
                pagerank=node_data.get("pagerank", 0.0),
            )
            self._nodes[node.id] = node

        for edge_data in data.get("edges", []):
            edge = KnowledgeEdge(
                id=edge_data["id"],
                source_id=edge_data["source"],
                target_id=edge_data["target"],
                edge_type=EdgeType(edge_data["type"]),
                weight=edge_data.get("weight", 1.0),
            )
            self.add_edge(edge)

        logger.info(f"[Graph] Loaded {len(self._nodes)} nodes, {len(self._edges)} edges")
