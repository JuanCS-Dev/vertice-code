"""
Knowledge Mixin

Mixin class for integrating knowledge graph capabilities into agents.

References:
- arXiv:2501.00309 (GraphRAG Survey)
- arXiv:2410.05983 (GNN-RAG for Multi-Hop)
- arXiv:2404.16130 (KG²RAG)
- arXiv:2312.10997 (Self-RAG)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .types import (
    DocumentChunk,
    RetrievalQuery,
    RetrievalResult,
    RetrievalStrategy,
    KnowledgeConfig,
    GraphContext,
)
from .chunker import SemanticChunker
from .embedder import HybridEmbedder
from .retriever import GraphRetriever
from .graph import KnowledgeGraph

logger = logging.getLogger(__name__)


class KnowledgeMixin:
    """
    Mixin providing knowledge graph capabilities to agents.

    Implements the five GraphRAG components (arXiv:2501.00309):
    1. Query Processor: Query decomposition and rewriting
    2. Retriever: Hybrid + graph-enhanced retrieval
    3. Organizer: Knowledge organization and ranking
    4. Generator: Context-aware response generation
    5. Data Source: Multi-source knowledge management

    Also integrates:
    - GNN-RAG multi-hop reasoning (arXiv:2410.05983)
    - KG²RAG chunk expansion (arXiv:2404.16130)
    - Self-RAG adaptive retrieval (arXiv:2312.10997)
    """

    def __init__(
        self,
        knowledge_config: Optional[KnowledgeConfig] = None,
        persistence_path: Optional[Path] = None,
        dense_encoder: Optional[Callable[[str], List[float]]] = None,
    ):
        """
        Initialize knowledge capabilities.

        Args:
            knowledge_config: Knowledge system configuration
            persistence_path: Path for graph persistence
            dense_encoder: Custom dense embedding function
        """
        self._knowledge_config = knowledge_config or KnowledgeConfig()

        # Initialize components
        self._chunker = SemanticChunker(self._knowledge_config)
        self._embedder = HybridEmbedder(self._knowledge_config, dense_encoder)
        self._graph = KnowledgeGraph(self._knowledge_config, persistence_path)
        self._retriever = GraphRetriever(
            self._knowledge_config,
            self._embedder,
            self._graph,
        )

        # Document tracking
        self._indexed_documents: Dict[str, int] = {}  # doc_id -> chunk_count

        # Query history for learning
        self._query_history: List[RetrievalQuery] = []

    def index_document(
        self,
        content: str,
        document_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Index a document for knowledge retrieval.

        Implements the Data Source component (arXiv:2501.00309).

        Args:
            content: Document content
            document_id: Document identifier
            metadata: Document metadata

        Returns:
            Number of chunks indexed
        """
        # Step 1: Semantic chunking
        chunks = self._chunker.chunk_document(
            content,
            document_id,
            metadata,
        )

        # Step 2: Add expanded context (KG²RAG style)
        chunks = self._chunker.rechunk_for_context(chunks, context_window=2)

        # Step 3: Index chunks with embeddings
        num_indexed = self._retriever.index_chunks(chunks)

        # Step 4: Build graph nodes for chunks
        self._build_chunk_graph(chunks)

        self._indexed_documents[document_id] = num_indexed

        logger.info(
            f"[Knowledge] Indexed document '{document_id}': "
            f"{len(content)} chars -> {num_indexed} chunks"
        )

        return num_indexed

    def retrieve(
        self,
        query: str,
        strategy: Optional[RetrievalStrategy] = None,
        top_k: Optional[int] = None,
        max_hops: int = 2,
        use_reflection: bool = True,
    ) -> RetrievalResult:
        """
        Retrieve relevant knowledge for a query.

        Implements Query Processor + Retriever components.

        Args:
            query: Query text
            strategy: Retrieval strategy
            top_k: Number of results
            max_hops: Maximum hops for multi-hop retrieval
            use_reflection: Enable Self-RAG reflection

        Returns:
            RetrievalResult with ranked chunks and graph context
        """
        # Build retrieval query
        retrieval_query = RetrievalQuery(
            text=query,
            strategy=strategy or self._knowledge_config.default_strategy,
            top_k=top_k or self._knowledge_config.default_top_k,
            max_hops=max_hops,
            use_reflection=use_reflection,
        )

        # Execute retrieval
        result = self._retriever.retrieve(retrieval_query)

        # Track query for learning
        self._query_history.append(retrieval_query)

        return result

    def retrieve_with_context(
        self,
        query: str,
        context_hops: int = 1,
    ) -> tuple[RetrievalResult, GraphContext]:
        """
        Retrieve with expanded graph context (KG²RAG style).

        Args:
            query: Query text
            context_hops: Number of hops for context expansion

        Returns:
            Tuple of (RetrievalResult, GraphContext)
        """
        result = self.retrieve(
            query,
            strategy=RetrievalStrategy.GRAPH,
            use_reflection=True,
        )

        # Get expanded graph context for top result
        graph_context = GraphContext()
        if result.chunks:
            top_chunk = result.chunks[0]
            graph_context = self._graph.get_graph_context(
                top_chunk.id,
                max_hops=context_hops,
            )

        return result, graph_context

    def multi_hop_retrieve(
        self,
        query: str,
        max_hops: int = 3,
    ) -> RetrievalResult:
        """
        Multi-hop retrieval using GNN-RAG approach.

        Implements reasoning over knowledge graph paths (arXiv:2410.05983).

        Args:
            query: Complex query requiring multi-hop reasoning
            max_hops: Maximum reasoning hops

        Returns:
            RetrievalResult with reasoning paths
        """
        return self.retrieve(
            query,
            strategy=RetrievalStrategy.MULTI_HOP,
            max_hops=max_hops,
            use_reflection=True,
        )

    def decompose_query(self, query: str) -> List[str]:
        """
        Decompose a complex query into sub-queries.

        Query Processor component (arXiv:2501.00309).

        Args:
            query: Complex query

        Returns:
            List of sub-queries
        """
        # Simple heuristic decomposition
        # In production, use LLM for semantic decomposition
        sub_queries = []

        # Split on conjunctions
        parts = query.replace(" and ", " | ").replace(" or ", " | ").split(" | ")

        for part in parts:
            part = part.strip()
            if part:
                sub_queries.append(part)

        # If no decomposition, return original
        if not sub_queries:
            sub_queries = [query]

        return sub_queries

    def aggregate_results(
        self,
        results: List[RetrievalResult],
    ) -> RetrievalResult:
        """
        Aggregate multiple retrieval results.

        Organizer component (arXiv:2501.00309).

        Args:
            results: List of retrieval results

        Returns:
            Aggregated result with deduplicated, ranked chunks
        """
        if not results:
            return RetrievalResult()

        # Collect all chunks with their scores
        chunk_scores: Dict[str, tuple[DocumentChunk, float]] = {}

        for result in results:
            for chunk in result.chunks:
                if chunk.id in chunk_scores:
                    # Combine scores (max pooling)
                    existing_chunk, existing_score = chunk_scores[chunk.id]
                    chunk_scores[chunk.id] = (
                        existing_chunk,
                        max(existing_score, chunk.relevance_score),
                    )
                else:
                    chunk_scores[chunk.id] = (chunk, chunk.relevance_score)

        # Sort by score
        ranked_chunks = sorted(
            [c for c, _ in chunk_scores.values()],
            key=lambda c: c.relevance_score,
            reverse=True,
        )

        # Aggregate graph context
        all_nodes = []
        all_edges = []
        for result in results:
            all_nodes.extend(result.nodes)
            all_edges.extend(result.edges)

        # Deduplicate nodes and edges
        seen_nodes = set()
        unique_nodes = []
        for node in all_nodes:
            if node.id not in seen_nodes:
                seen_nodes.add(node.id)
                unique_nodes.append(node)

        seen_edges = set()
        unique_edges = []
        for edge in all_edges:
            edge_key = (edge.source_id, edge.target_id)
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                unique_edges.append(edge)

        return RetrievalResult(
            query_id="aggregated",
            chunks=ranked_chunks[: self._knowledge_config.default_top_k],
            nodes=unique_nodes,
            edges=unique_edges,
            retrieval_score=sum(r.retrieval_score for r in results) / len(results),
            graph_coherence=sum(r.graph_coherence for r in results) / len(results),
        )

    def retrieve_complex(self, query: str) -> RetrievalResult:
        """
        Handle complex queries with decomposition and aggregation.

        Full pipeline: Query Processor -> Retriever -> Organizer.

        Args:
            query: Complex query

        Returns:
            Aggregated retrieval result
        """
        # Decompose query
        sub_queries = self.decompose_query(query)

        # Retrieve for each sub-query
        results = []
        for sub_query in sub_queries:
            result = self.retrieve(sub_query)
            results.append(result)

        # Aggregate results
        return self.aggregate_results(results)

    def _build_chunk_graph(self, chunks: List[DocumentChunk]) -> None:
        """
        Build knowledge graph from chunks.

        Creates nodes and edges based on semantic similarity and document structure.
        """
        from .types import KnowledgeNode, KnowledgeEdge, NodeType, EdgeType

        # Add chunk nodes
        for chunk in chunks:
            node = KnowledgeNode(
                id=chunk.id,
                node_type=NodeType.CHUNK,
                content=chunk.content,
                label=f"Chunk {chunk.chunk_index}",
                metadata=chunk.metadata,
            )
            self._graph.add_node(node)

        # Add sequential edges (FOLLOWS)
        for i in range(len(chunks) - 1):
            if chunks[i].document_id == chunks[i + 1].document_id:
                edge = KnowledgeEdge(
                    source_id=chunks[i].id,
                    target_id=chunks[i + 1].id,
                    edge_type=EdgeType.FOLLOWS,
                    weight=1.0,
                )
                self._graph.add_edge(edge)

        # Add similarity edges (RELATED_TO)
        # Only for chunks with embeddings
        for i, chunk_i in enumerate(chunks):
            if not chunk_i.dense_embedding:
                continue

            for j, chunk_j in enumerate(chunks[i + 1 :], i + 1):
                if not chunk_j.dense_embedding:
                    continue

                # Compute similarity
                similarity = self._embedder._cosine_similarity(
                    chunk_i.dense_embedding,
                    chunk_j.dense_embedding,
                )

                # Add edge if above threshold
                if similarity >= self._knowledge_config.min_edge_weight:
                    edge = KnowledgeEdge(
                        source_id=chunk_i.id,
                        target_id=chunk_j.id,
                        edge_type=EdgeType.RELATED_TO,
                        weight=similarity,
                    )
                    self._graph.add_edge(edge)

    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get comprehensive knowledge system statistics."""
        return {
            "documents_indexed": len(self._indexed_documents),
            "total_chunks": sum(self._indexed_documents.values()),
            "queries_processed": len(self._query_history),
            "graph": self._graph.get_stats(),
            "retriever": self._retriever.get_stats(),
            "embedder": self._embedder.get_stats(),
        }

    def save_knowledge(self) -> None:
        """Persist knowledge graph to disk."""
        self._graph.save()

    def clear_cache(self) -> None:
        """Clear embedding and retrieval caches."""
        self._embedder.clear_cache()
