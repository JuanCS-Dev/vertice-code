"""
Knowledge Types

Type definitions for GraphRAG and knowledge management.

References:
- arXiv:2501.00309 (GraphRAG Survey)
- arXiv:2410.05983 (GNN-RAG)
- arXiv:2404.16130 (KG²RAG)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List
from enum import Enum
from datetime import datetime
import uuid


class NodeType(str, Enum):
    """Types of nodes in knowledge graph."""
    DOCUMENT = "document"
    CHUNK = "chunk"
    ENTITY = "entity"
    CONCEPT = "concept"
    QUERY = "query"


class EdgeType(str, Enum):
    """Types of edges in knowledge graph."""
    CONTAINS = "contains"        # Document contains chunk
    REFERENCES = "references"    # Chunk references entity
    RELATED_TO = "related_to"   # Semantic similarity
    FOLLOWS = "follows"          # Sequential relationship
    CAUSES = "causes"            # Causal relationship
    INSTANCE_OF = "instance_of"  # Type relationship


class RetrievalStrategy(str, Enum):
    """Retrieval strategies for different query types."""
    DENSE = "dense"              # Vector similarity
    SPARSE = "sparse"            # BM25/keyword
    HYBRID = "hybrid"            # Combined dense + sparse
    GRAPH = "graph"              # Graph traversal
    MULTI_HOP = "multi_hop"      # GNN-based multi-hop


@dataclass
class DocumentChunk:
    """
    A chunk of a document for retrieval.

    Implements semantic chunking with overlap.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    document_id: str = ""
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Position in document
    start_char: int = 0
    end_char: int = 0
    chunk_index: int = 0

    # Embeddings
    dense_embedding: List[float] = field(default_factory=list)
    sparse_embedding: Dict[str, float] = field(default_factory=dict)

    # Graph context (KG²RAG style)
    expanded_context: str = ""
    related_entities: List[str] = field(default_factory=list)

    # Scoring
    relevance_score: float = 0.0
    graph_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "content": self.content,
            "metadata": self.metadata,
            "chunk_index": self.chunk_index,
            "relevance_score": self.relevance_score,
        }


@dataclass
class KnowledgeNode:
    """
    A node in the knowledge graph.

    Represents entities, concepts, or chunks.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    node_type: NodeType = NodeType.CHUNK
    content: str = ""
    label: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Embedding
    embedding: List[float] = field(default_factory=list)

    # Graph properties
    in_degree: int = 0
    out_degree: int = 0
    pagerank: float = 0.0

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.node_type.value,
            "content": self.content,
            "label": self.label,
            "pagerank": self.pagerank,
        }


@dataclass
class KnowledgeEdge:
    """
    An edge in the knowledge graph.

    Represents relationships between nodes.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    source_id: str = ""
    target_id: str = ""
    edge_type: EdgeType = EdgeType.RELATED_TO
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    # For multi-hop reasoning
    hop_distance: int = 1
    path_score: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "source": self.source_id,
            "target": self.target_id,
            "type": self.edge_type.value,
            "weight": self.weight,
        }


@dataclass
class RetrievalQuery:
    """
    A query for knowledge retrieval.

    Supports multi-hop and graph-enhanced retrieval.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    text: str = ""
    embedding: List[float] = field(default_factory=list)

    # Query type
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    max_hops: int = 2              # For multi-hop queries
    top_k: int = 5                 # Number of results

    # Filters
    document_ids: List[str] = field(default_factory=list)
    node_types: List[NodeType] = field(default_factory=list)
    min_relevance: float = 0.0

    # Self-RAG settings
    use_reflection: bool = False
    verify_relevance: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "strategy": self.strategy.value,
            "max_hops": self.max_hops,
            "top_k": self.top_k,
        }


@dataclass
class RetrievalResult:
    """
    Result of a retrieval query.

    Includes chunks and graph context.
    """
    query_id: str = ""
    chunks: List[DocumentChunk] = field(default_factory=list)
    nodes: List[KnowledgeNode] = field(default_factory=list)
    edges: List[KnowledgeEdge] = field(default_factory=list)

    # Scores
    retrieval_score: float = 0.0
    graph_coherence: float = 0.0

    # Multi-hop paths (for explainability)
    reasoning_paths: List[List[str]] = field(default_factory=list)

    # Self-RAG reflection
    relevance_assessment: str = ""
    should_retrieve_more: bool = False

    # Timing
    retrieval_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query_id": self.query_id,
            "num_chunks": len(self.chunks),
            "num_nodes": len(self.nodes),
            "retrieval_score": self.retrieval_score,
            "graph_coherence": self.graph_coherence,
            "retrieval_time_ms": self.retrieval_time_ms,
        }


@dataclass
class GraphContext:
    """
    Graph context for a query (KG²RAG style).

    Expands chunk context using knowledge graph.
    """
    central_node_id: str = ""
    neighborhood_nodes: List[KnowledgeNode] = field(default_factory=list)
    connecting_edges: List[KnowledgeEdge] = field(default_factory=list)

    # Expanded text context
    expanded_context: str = ""

    # Graph metrics
    subgraph_density: float = 0.0
    avg_path_length: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "central_node": self.central_node_id,
            "num_neighbors": len(self.neighborhood_nodes),
            "num_edges": len(self.connecting_edges),
            "subgraph_density": self.subgraph_density,
        }


@dataclass
class KnowledgeConfig:
    """
    Configuration for knowledge system.

    Combines chunking, embedding, and retrieval settings.
    """
    # Chunking settings
    chunk_size: int = 512
    chunk_overlap: int = 64
    use_semantic_chunking: bool = True

    # Embedding settings
    embedding_model: str = "default"
    embedding_dim: int = 768
    use_hybrid_embedding: bool = True

    # Retrieval settings
    default_strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    default_top_k: int = 5
    dense_weight: float = 0.7
    sparse_weight: float = 0.3

    # Graph settings
    max_hops: int = 2
    min_edge_weight: float = 0.5
    use_pagerank: bool = True

    # Self-RAG settings
    use_self_rag: bool = True
    reflection_threshold: float = 0.7

    # Performance
    batch_size: int = 32
    cache_embeddings: bool = True
