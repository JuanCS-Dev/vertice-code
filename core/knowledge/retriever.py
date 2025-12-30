"""
Graph Retriever

Multi-hop retrieval with knowledge graph enhancement.

References:
- arXiv:2501.00309 (GraphRAG Survey)
- arXiv:2410.05983 (GNN-RAG for Multi-Hop)
- arXiv:2312.10997 (Self-RAG)
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from .types import (
    DocumentChunk,
    RetrievalQuery,
    RetrievalResult,
    RetrievalStrategy,
    KnowledgeNode,
    KnowledgeEdge,
    KnowledgeConfig,
)
from .embedder import HybridEmbedder

logger = logging.getLogger(__name__)


class GraphRetriever:
    """
    Graph-enhanced retrieval system.

    Implements multiple retrieval strategies:
    - Dense: Vector similarity search
    - Sparse: BM25 keyword search
    - Hybrid: Combined dense + sparse
    - Graph: Knowledge graph traversal
    - Multi-hop: GNN-based multi-hop reasoning

    References:
    - arXiv:2501.00309: Five components (Query Processor, Retriever, Organizer, Generator, Data Source)
    - arXiv:2410.05983: GNN-RAG for complex queries
    - arXiv:2312.10997: Self-RAG for adaptive retrieval
    """

    def __init__(
        self,
        config: Optional[KnowledgeConfig] = None,
        embedder: Optional[HybridEmbedder] = None,
        graph: Optional[Any] = None,  # KnowledgeGraph
    ):
        """
        Initialize retriever.

        Args:
            config: Knowledge configuration
            embedder: Hybrid embedder
            graph: Knowledge graph
        """
        self._config = config or KnowledgeConfig()
        self._embedder = embedder or HybridEmbedder(self._config)
        self._graph = graph

        # Chunk index
        self._chunks: Dict[str, DocumentChunk] = {}
        self._chunk_list: List[DocumentChunk] = []

        # Retrieval history for learning
        self._retrieval_history: List[RetrievalResult] = []

    def index_chunks(self, chunks: List[DocumentChunk]) -> int:
        """
        Index chunks for retrieval.

        Args:
            chunks: Chunks to index

        Returns:
            Number of chunks indexed
        """
        # Compute embeddings
        embedded_chunks = self._embedder.embed_chunks(chunks)

        for chunk in embedded_chunks:
            self._chunks[chunk.id] = chunk
            self._chunk_list.append(chunk)

        logger.info(f"[Retriever] Indexed {len(chunks)} chunks")
        return len(chunks)

    def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: Retrieval query

        Returns:
            RetrievalResult with ranked chunks
        """
        start_time = time.perf_counter()

        # Get query embeddings
        query.embedding, sparse_query = self._embedder.embed_query(query.text)

        # Choose retrieval strategy
        if query.strategy == RetrievalStrategy.DENSE:
            chunks = self._dense_retrieve(query)
        elif query.strategy == RetrievalStrategy.SPARSE:
            chunks = self._sparse_retrieve(query, sparse_query)
        elif query.strategy == RetrievalStrategy.HYBRID:
            chunks = self._hybrid_retrieve(query, sparse_query)
        elif query.strategy == RetrievalStrategy.GRAPH:
            chunks = self._graph_retrieve(query)
        elif query.strategy == RetrievalStrategy.MULTI_HOP:
            chunks = self._multi_hop_retrieve(query)
        else:
            chunks = self._hybrid_retrieve(query, sparse_query)

        # Apply Self-RAG reflection if enabled
        if self._config.use_self_rag and query.use_reflection:
            chunks = self._self_rag_filter(query, chunks)

        result = RetrievalResult(
            query_id=query.id,
            chunks=chunks[:query.top_k],
            retrieval_score=self._compute_result_score(chunks[:query.top_k]),
            retrieval_time_ms=(time.perf_counter() - start_time) * 1000,
        )

        # Add graph context if available
        if self._graph and chunks:
            result.nodes, result.edges = self._get_graph_context(chunks)
            result.graph_coherence = self._compute_graph_coherence(result.nodes, result.edges)

        self._retrieval_history.append(result)

        logger.debug(
            f"[Retriever] Query '{query.text[:50]}...' -> {len(result.chunks)} chunks "
            f"in {result.retrieval_time_ms:.1f}ms"
        )

        return result

    def _dense_retrieve(self, query: RetrievalQuery) -> List[DocumentChunk]:
        """Dense vector similarity retrieval."""
        scored_chunks = []

        for chunk in self._chunk_list:
            if chunk.dense_embedding:
                score = self._embedder._cosine_similarity(
                    query.embedding,
                    chunk.dense_embedding,
                )
                if score >= query.min_relevance:
                    chunk.relevance_score = score
                    scored_chunks.append((score, chunk))

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored_chunks]

    def _sparse_retrieve(
        self,
        query: RetrievalQuery,
        sparse_query: Dict[str, float],
    ) -> List[DocumentChunk]:
        """Sparse BM25-style retrieval."""
        scored_chunks = []

        for chunk in self._chunk_list:
            if chunk.sparse_embedding:
                score = self._embedder._sparse_similarity(
                    sparse_query,
                    chunk.sparse_embedding,
                )
                if score >= query.min_relevance:
                    chunk.relevance_score = score
                    scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored_chunks]

    def _hybrid_retrieve(
        self,
        query: RetrievalQuery,
        sparse_query: Dict[str, float],
    ) -> List[DocumentChunk]:
        """Hybrid dense + sparse retrieval."""
        scored_chunks = []

        for chunk in self._chunk_list:
            score = self._embedder.compute_similarity(
                query.embedding,
                sparse_query,
                chunk,
            )
            if score >= query.min_relevance:
                chunk.relevance_score = score
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored_chunks]

    def _graph_retrieve(self, query: RetrievalQuery) -> List[DocumentChunk]:
        """Graph-enhanced retrieval using knowledge graph structure."""
        if not self._graph:
            return self._hybrid_retrieve(
                query,
                self._embedder._compute_query_sparse_embedding(query.text),
            )

        # Start with hybrid retrieval to get seed nodes
        seed_chunks = self._hybrid_retrieve(
            query,
            self._embedder._compute_query_sparse_embedding(query.text),
        )[:3]

        if not seed_chunks:
            return []

        # Expand through graph
        expanded_chunk_ids = set(c.id for c in seed_chunks)

        for chunk in seed_chunks:
            # Get neighbors from graph
            neighbors = self._graph.get_neighbors(chunk.id, max_hops=1)
            for neighbor_id in neighbors:
                if neighbor_id in self._chunks:
                    expanded_chunk_ids.add(neighbor_id)

        # Score expanded chunks
        expanded_chunks = []
        for chunk_id in expanded_chunk_ids:
            chunk = self._chunks.get(chunk_id)
            if chunk:
                # Combine relevance with graph score
                graph_score = self._graph.get_node_importance(chunk_id)
                chunk.graph_score = graph_score
                chunk.relevance_score = 0.7 * chunk.relevance_score + 0.3 * graph_score
                expanded_chunks.append(chunk)

        expanded_chunks.sort(key=lambda c: c.relevance_score, reverse=True)
        return expanded_chunks

    def _multi_hop_retrieve(self, query: RetrievalQuery) -> List[DocumentChunk]:
        """
        Multi-hop retrieval using graph traversal.

        Implements GNN-RAG style reasoning (arXiv:2410.05983).
        """
        if not self._graph:
            return self._graph_retrieve(query)

        # Initial retrieval
        initial_chunks = self._hybrid_retrieve(
            query,
            self._embedder._compute_query_sparse_embedding(query.text),
        )[:query.top_k]

        if not initial_chunks:
            return []

        # Multi-hop expansion
        all_chunks = list(initial_chunks)
        visited = set(c.id for c in initial_chunks)
        reasoning_paths = []

        for hop in range(query.max_hops):
            new_chunks = []

            for chunk in all_chunks[-query.top_k:]:
                # Get connected chunks through graph
                neighbors = self._graph.get_neighbors(chunk.id, max_hops=1)

                for neighbor_id in neighbors:
                    if neighbor_id not in visited and neighbor_id in self._chunks:
                        neighbor_chunk = self._chunks[neighbor_id]

                        # Score neighbor based on query relevance
                        score = self._embedder.compute_similarity(
                            query.embedding,
                            self._embedder._compute_query_sparse_embedding(query.text),
                            neighbor_chunk,
                        )

                        if score >= query.min_relevance:
                            neighbor_chunk.relevance_score = score
                            neighbor_chunk.graph_score = 1.0 / (hop + 2)  # Decay with hops
                            new_chunks.append(neighbor_chunk)
                            visited.add(neighbor_id)

                            # Track reasoning path
                            reasoning_paths.append([chunk.id, neighbor_id])

            all_chunks.extend(new_chunks)

        # Re-score with combined relevance and graph scores
        for chunk in all_chunks:
            chunk.relevance_score = (
                0.6 * chunk.relevance_score +
                0.4 * chunk.graph_score
            )

        all_chunks.sort(key=lambda c: c.relevance_score, reverse=True)
        return all_chunks

    def _self_rag_filter(
        self,
        query: RetrievalQuery,
        chunks: List[DocumentChunk],
    ) -> List[DocumentChunk]:
        """
        Self-RAG relevance filtering (arXiv:2312.10997).

        Filters chunks based on self-assessed relevance.
        """
        filtered = []

        for chunk in chunks:
            # Self-assess relevance (simplified)
            # In production, use LLM for relevance assessment
            relevance_score = chunk.relevance_score

            if relevance_score >= self._config.reflection_threshold:
                filtered.append(chunk)

        if len(filtered) < 2 and chunks:
            # Ensure minimum results
            filtered = chunks[:2]

        return filtered

    def _get_graph_context(
        self,
        chunks: List[DocumentChunk],
    ) -> Tuple[List[KnowledgeNode], List[KnowledgeEdge]]:
        """Get graph context for retrieved chunks."""
        if not self._graph:
            return [], []

        nodes = []
        edges = []
        chunk_ids = set(c.id for c in chunks)

        for chunk in chunks:
            node = self._graph.get_node(chunk.id)
            if node:
                nodes.append(node)

            # Get edges between retrieved chunks
            for other_id in chunk_ids:
                if other_id != chunk.id:
                    edge = self._graph.get_edge(chunk.id, other_id)
                    if edge:
                        edges.append(edge)

        return nodes, edges

    def _compute_result_score(self, chunks: List[DocumentChunk]) -> float:
        """Compute overall retrieval result score."""
        if not chunks:
            return 0.0
        return sum(c.relevance_score for c in chunks) / len(chunks)

    def _compute_graph_coherence(
        self,
        nodes: List[KnowledgeNode],
        edges: List[KnowledgeEdge],
    ) -> float:
        """Compute coherence of retrieved graph subgraph."""
        if len(nodes) < 2:
            return 1.0

        # Density: actual edges / possible edges
        max_edges = len(nodes) * (len(nodes) - 1) / 2
        density = len(edges) / max_edges if max_edges > 0 else 0.0

        return density

    def get_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics."""
        if not self._retrieval_history:
            return {"total_retrievals": 0}

        avg_time = sum(r.retrieval_time_ms for r in self._retrieval_history) / len(self._retrieval_history)
        avg_chunks = sum(len(r.chunks) for r in self._retrieval_history) / len(self._retrieval_history)
        avg_score = sum(r.retrieval_score for r in self._retrieval_history) / len(self._retrieval_history)

        return {
            "total_retrievals": len(self._retrieval_history),
            "indexed_chunks": len(self._chunks),
            "avg_retrieval_time_ms": avg_time,
            "avg_chunks_returned": avg_chunks,
            "avg_retrieval_score": avg_score,
        }
