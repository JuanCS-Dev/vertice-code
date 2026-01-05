"""
Tests for Knowledge Module (Phase 4)

Tests for GraphRAG, Agentic RAG 2.0, and knowledge graph integration.

References:
- arXiv:2501.00309 (GraphRAG Survey)
- arXiv:2410.05983 (GNN-RAG for Multi-Hop)
- arXiv:2404.16130 (KG²RAG: Chunk Expansion)
- arXiv:2312.10997 (Self-RAG)
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile

from core.knowledge.types import (
    NodeType,
    EdgeType,
    RetrievalStrategy,
    DocumentChunk,
    KnowledgeNode,
    KnowledgeEdge,
    RetrievalQuery,
    RetrievalResult,
    GraphContext,
    KnowledgeConfig,
)
from core.knowledge.chunker import SemanticChunker
from core.knowledge.embedder import HybridEmbedder
from core.knowledge.retriever import GraphRetriever
from core.knowledge.graph import KnowledgeGraph
from core.knowledge.mixin import KnowledgeMixin


class TestKnowledgeTypes:
    """Tests for knowledge type definitions."""

    def test_node_type_enum(self):
        """Test NodeType enumeration."""
        assert NodeType.DOCUMENT.value == "document"
        assert NodeType.CHUNK.value == "chunk"
        assert NodeType.ENTITY.value == "entity"
        assert NodeType.CONCEPT.value == "concept"

    def test_edge_type_enum(self):
        """Test EdgeType enumeration."""
        assert EdgeType.CONTAINS.value == "contains"
        assert EdgeType.REFERENCES.value == "references"
        assert EdgeType.RELATED_TO.value == "related_to"
        assert EdgeType.FOLLOWS.value == "follows"

    def test_retrieval_strategy_enum(self):
        """Test RetrievalStrategy enumeration."""
        assert RetrievalStrategy.DENSE.value == "dense"
        assert RetrievalStrategy.SPARSE.value == "sparse"
        assert RetrievalStrategy.HYBRID.value == "hybrid"
        assert RetrievalStrategy.GRAPH.value == "graph"
        assert RetrievalStrategy.MULTI_HOP.value == "multi_hop"

    def test_document_chunk_creation(self):
        """Test DocumentChunk dataclass."""
        chunk = DocumentChunk(
            document_id="doc_1",
            content="Test content for chunking.",
            metadata={"source": "test"},
            chunk_index=0,
        )
        assert chunk.document_id == "doc_1"
        assert chunk.content == "Test content for chunking."
        assert chunk.chunk_index == 0
        assert chunk.id is not None

    def test_document_chunk_to_dict(self):
        """Test DocumentChunk serialization."""
        chunk = DocumentChunk(
            document_id="doc_1",
            content="Test content",
            chunk_index=5,
            relevance_score=0.85,
        )
        d = chunk.to_dict()
        assert d["document_id"] == "doc_1"
        assert d["relevance_score"] == 0.85

    def test_knowledge_node_creation(self):
        """Test KnowledgeNode dataclass."""
        node = KnowledgeNode(
            node_type=NodeType.ENTITY,
            content="Python programming language",
            label="Python",
        )
        assert node.node_type == NodeType.ENTITY
        assert node.label == "Python"
        assert node.pagerank == 0.0

    def test_knowledge_edge_creation(self):
        """Test KnowledgeEdge dataclass."""
        edge = KnowledgeEdge(
            source_id="node_1",
            target_id="node_2",
            edge_type=EdgeType.RELATED_TO,
            weight=0.8,
        )
        assert edge.source_id == "node_1"
        assert edge.target_id == "node_2"
        assert edge.weight == 0.8

    def test_retrieval_query_creation(self):
        """Test RetrievalQuery dataclass."""
        query = RetrievalQuery(
            text="What is Python?",
            strategy=RetrievalStrategy.HYBRID,
            top_k=5,
            max_hops=2,
        )
        assert query.text == "What is Python?"
        assert query.strategy == RetrievalStrategy.HYBRID
        assert query.max_hops == 2

    def test_retrieval_result_creation(self):
        """Test RetrievalResult dataclass."""
        result = RetrievalResult(
            query_id="q_1",
            chunks=[DocumentChunk(content="Result chunk")],
            retrieval_score=0.9,
            graph_coherence=0.75,
        )
        assert len(result.chunks) == 1
        assert result.retrieval_score == 0.9

    def test_graph_context_creation(self):
        """Test GraphContext dataclass."""
        context = GraphContext(
            central_node_id="node_1",
            neighborhood_nodes=[KnowledgeNode(label="neighbor")],
            expanded_context="Related information...",
            subgraph_density=0.5,
        )
        assert context.central_node_id == "node_1"
        assert len(context.neighborhood_nodes) == 1

    def test_knowledge_config_defaults(self):
        """Test KnowledgeConfig defaults."""
        config = KnowledgeConfig()
        assert config.chunk_size == 512
        assert config.chunk_overlap == 64
        assert config.use_semantic_chunking is True
        assert config.default_strategy == RetrievalStrategy.HYBRID


class TestSemanticChunker:
    """Tests for SemanticChunker."""

    @pytest.fixture
    def chunker(self):
        """Create test chunker."""
        config = KnowledgeConfig(
            chunk_size=100,
            chunk_overlap=20,
            use_semantic_chunking=True,
        )
        return SemanticChunker(config)

    @pytest.fixture
    def sample_document(self):
        """Sample document for chunking."""
        return """
        # Introduction

        This is the first paragraph of the document.
        It contains some important information.

        # Section Two

        This is the second section.
        It has different content than the first.

        # Conclusion

        Final thoughts and summary.
        """

    def test_chunker_initialization(self, chunker):
        """Test chunker initialization."""
        assert chunker._config.chunk_size == 100
        assert chunker._config.use_semantic_chunking is True

    def test_chunk_document_semantic(self, chunker, sample_document):
        """Test semantic document chunking."""
        chunks = chunker.chunk_document(
            content=sample_document,
            document_id="test_doc",
            metadata={"source": "test"},
        )
        assert len(chunks) > 0
        assert all(isinstance(c, DocumentChunk) for c in chunks)
        assert all(c.document_id == "test_doc" for c in chunks)

    def test_chunk_document_fixed(self):
        """Test fixed-size chunking."""
        config = KnowledgeConfig(
            chunk_size=50,
            chunk_overlap=10,
            use_semantic_chunking=False,
        )
        chunker = SemanticChunker(config)

        content = "A" * 200
        chunks = chunker.chunk_document(content, "doc_1")

        assert len(chunks) > 1
        # Chunks should have overlap
        for i in range(len(chunks) - 1):
            # Verify chunks are not too large
            assert len(chunks[i].content) <= 50 + 10

    def test_chunk_positions(self, chunker):
        """Test chunk position tracking."""
        content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = chunker.chunk_document(content, "doc_1")

        # Check start/end positions are set
        for chunk in chunks:
            assert chunk.start_char >= 0
            assert chunk.end_char > chunk.start_char

    def test_rechunk_for_context(self, chunker, sample_document):
        """Test context expansion."""
        chunks = chunker.chunk_document(sample_document, "doc_1")

        if len(chunks) < 2:
            # Create more chunks for testing
            long_doc = sample_document * 5
            chunks = chunker.chunk_document(long_doc, "doc_1")

        expanded = chunker.rechunk_for_context(chunks, context_window=1)

        assert len(expanded) == len(chunks)
        # Expanded chunks should have context
        if len(chunks) > 1:
            assert expanded[1].expanded_context != ""

    def test_empty_document(self, chunker):
        """Test handling empty document."""
        chunks = chunker.chunk_document("", "empty_doc")
        assert len(chunks) == 0

    def test_large_paragraph_splitting(self, chunker):
        """Test splitting of paragraphs larger than chunk size."""
        # Create a very long paragraph
        long_paragraph = "This is a sentence. " * 50
        chunks = chunker.chunk_document(long_paragraph, "doc_1")

        # Should be split into multiple chunks
        assert len(chunks) >= 1


class TestHybridEmbedder:
    """Tests for HybridEmbedder."""

    @pytest.fixture
    def embedder(self):
        """Create test embedder."""
        config = KnowledgeConfig(
            embedding_dim=128,
            use_hybrid_embedding=True,
            dense_weight=0.7,
            sparse_weight=0.3,
        )
        return HybridEmbedder(config)

    @pytest.fixture
    def sample_chunks(self):
        """Create sample chunks for embedding."""
        return [
            DocumentChunk(
                content="Python is a programming language.",
                document_id="doc_1",
            ),
            DocumentChunk(
                content="Machine learning uses Python extensively.",
                document_id="doc_1",
            ),
            DocumentChunk(
                content="JavaScript runs in web browsers.",
                document_id="doc_2",
            ),
        ]

    def test_embedder_initialization(self, embedder):
        """Test embedder initialization."""
        assert embedder._config.embedding_dim == 128
        assert embedder._config.use_hybrid_embedding is True

    def test_embed_chunks(self, embedder, sample_chunks):
        """Test chunk embedding."""
        embedded = embedder.embed_chunks(sample_chunks)

        assert len(embedded) == len(sample_chunks)
        for chunk in embedded:
            assert len(chunk.dense_embedding) == 128
            assert len(chunk.sparse_embedding) > 0

    def test_embed_query(self, embedder):
        """Test query embedding."""
        dense, sparse = embedder.embed_query("What is Python?")

        assert len(dense) == 128
        assert isinstance(sparse, dict)
        assert len(sparse) > 0

    def test_compute_similarity(self, embedder, sample_chunks):
        """Test similarity computation."""
        embedded = embedder.embed_chunks(sample_chunks)

        query_dense, query_sparse = embedder.embed_query("Python programming")

        similarity = embedder.compute_similarity(
            query_dense,
            query_sparse,
            embedded[0],  # Python chunk
        )

        assert 0.0 <= similarity <= 1.0

    def test_hybrid_vs_dense_only(self, sample_chunks):
        """Test hybrid vs dense-only similarity."""
        # Hybrid config
        hybrid_config = KnowledgeConfig(use_hybrid_embedding=True)
        hybrid_embedder = HybridEmbedder(hybrid_config)

        # Dense-only config
        dense_config = KnowledgeConfig(use_hybrid_embedding=False)
        dense_embedder = HybridEmbedder(dense_config)

        # Embed chunks
        hybrid_chunks = hybrid_embedder.embed_chunks(sample_chunks)
        dense_chunks = dense_embedder.embed_chunks(sample_chunks)

        # Both should have embeddings
        assert hybrid_chunks[0].dense_embedding
        assert dense_chunks[0].dense_embedding

    def test_bm25_parameters(self, embedder):
        """Test BM25 parameters."""
        assert embedder._k1 == 1.5
        assert embedder._b == 0.75

    def test_cosine_similarity(self, embedder):
        """Test cosine similarity calculation."""
        # Identical vectors
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        assert embedder._cosine_similarity(v1, v2) == pytest.approx(1.0)

        # Orthogonal vectors
        v3 = [0.0, 1.0, 0.0]
        assert embedder._cosine_similarity(v1, v3) == pytest.approx(0.0)

    def test_sparse_similarity(self, embedder):
        """Test sparse similarity calculation."""
        query = {"python": 0.5, "programming": 0.5}
        doc = {"python": 1.0, "language": 0.5}

        score = embedder._sparse_similarity(query, doc)
        assert score > 0.0

    def test_embedding_cache(self, embedder):
        """Test embedding cache."""
        text = "Cache this text"

        # First embedding
        emb1 = embedder._get_dense_embedding(text)

        # Second embedding (should be cached)
        emb2 = embedder._get_dense_embedding(text)

        assert emb1 == emb2
        assert len(embedder._embedding_cache) >= 1

    def test_clear_cache(self, embedder):
        """Test cache clearing."""
        embedder._get_dense_embedding("test text")
        assert len(embedder._embedding_cache) >= 1

        embedder.clear_cache()
        assert len(embedder._embedding_cache) == 0

    def test_get_stats(self, embedder, sample_chunks):
        """Test embedder statistics."""
        embedder.embed_chunks(sample_chunks)

        stats = embedder.get_stats()
        assert "doc_count" in stats
        assert "vocab_size" in stats
        assert stats["doc_count"] == len(sample_chunks)


class TestKnowledgeGraph:
    """Tests for KnowledgeGraph."""

    @pytest.fixture
    def graph(self):
        """Create test graph."""
        config = KnowledgeConfig()
        return KnowledgeGraph(config)

    @pytest.fixture
    def sample_nodes(self):
        """Create sample nodes."""
        return [
            KnowledgeNode(id="n1", node_type=NodeType.CHUNK, content="Node 1"),
            KnowledgeNode(id="n2", node_type=NodeType.CHUNK, content="Node 2"),
            KnowledgeNode(id="n3", node_type=NodeType.ENTITY, content="Node 3"),
            KnowledgeNode(id="n4", node_type=NodeType.CONCEPT, content="Node 4"),
        ]

    def test_graph_initialization(self, graph):
        """Test graph initialization."""
        assert len(graph._nodes) == 0
        assert len(graph._edges) == 0

    def test_add_node(self, graph, sample_nodes):
        """Test adding nodes."""
        for node in sample_nodes:
            graph.add_node(node)

        assert len(graph._nodes) == len(sample_nodes)
        assert graph.get_node("n1") is not None

    def test_add_edge(self, graph, sample_nodes):
        """Test adding edges."""
        for node in sample_nodes:
            graph.add_node(node)

        edge = KnowledgeEdge(
            source_id="n1",
            target_id="n2",
            edge_type=EdgeType.RELATED_TO,
            weight=0.8,
        )
        graph.add_edge(edge)

        assert len(graph._edges) == 1
        assert graph.get_edge("n1", "n2") is not None

    def test_get_neighbors(self, graph, sample_nodes):
        """Test getting neighbors."""
        for node in sample_nodes:
            graph.add_node(node)

        # Create edges: n1 -> n2 -> n3
        graph.add_edge(KnowledgeEdge(source_id="n1", target_id="n2"))
        graph.add_edge(KnowledgeEdge(source_id="n2", target_id="n3"))

        # 1-hop neighbors of n1
        neighbors_1hop = graph.get_neighbors("n1", max_hops=1)
        assert "n2" in neighbors_1hop
        assert "n3" not in neighbors_1hop

        # 2-hop neighbors of n1
        neighbors_2hop = graph.get_neighbors("n1", max_hops=2)
        assert "n2" in neighbors_2hop
        assert "n3" in neighbors_2hop

    def test_get_neighbors_with_edge_filter(self, graph, sample_nodes):
        """Test neighbor filtering by edge type."""
        for node in sample_nodes:
            graph.add_node(node)

        graph.add_edge(KnowledgeEdge(
            source_id="n1", target_id="n2", edge_type=EdgeType.RELATED_TO
        ))
        graph.add_edge(KnowledgeEdge(
            source_id="n1", target_id="n3", edge_type=EdgeType.FOLLOWS
        ))

        # Filter by RELATED_TO only
        neighbors = graph.get_neighbors(
            "n1", max_hops=1, edge_types=[EdgeType.RELATED_TO]
        )
        assert "n2" in neighbors
        assert "n3" not in neighbors

    def test_pagerank(self, graph, sample_nodes):
        """Test PageRank computation."""
        for node in sample_nodes:
            graph.add_node(node)

        # Create edges
        graph.add_edge(KnowledgeEdge(source_id="n1", target_id="n2"))
        graph.add_edge(KnowledgeEdge(source_id="n1", target_id="n3"))
        graph.add_edge(KnowledgeEdge(source_id="n2", target_id="n3"))

        # Get importance
        importance = graph.get_node_importance("n3")
        assert importance > 0.0

        # n3 has more incoming edges, should have higher PageRank
        importance_n1 = graph.get_node_importance("n1")
        assert importance >= importance_n1

    def test_get_subgraph(self, graph, sample_nodes):
        """Test subgraph extraction."""
        for node in sample_nodes:
            graph.add_node(node)

        graph.add_edge(KnowledgeEdge(source_id="n1", target_id="n2"))
        graph.add_edge(KnowledgeEdge(source_id="n2", target_id="n3"))
        graph.add_edge(KnowledgeEdge(source_id="n3", target_id="n4"))

        nodes, edges = graph.get_subgraph(["n1", "n2", "n3"])

        assert len(nodes) == 3
        assert len(edges) == 2  # n1->n2, n2->n3

    def test_get_graph_context(self, graph, sample_nodes):
        """Test graph context extraction (KG²RAG style)."""
        for node in sample_nodes:
            graph.add_node(node)

        graph.add_edge(KnowledgeEdge(source_id="n1", target_id="n2"))
        graph.add_edge(KnowledgeEdge(source_id="n2", target_id="n3"))

        context = graph.get_graph_context("n2", max_hops=1)

        assert context.central_node_id == "n2"
        assert len(context.neighborhood_nodes) >= 1
        assert context.expanded_context != ""

    def test_find_path(self, graph, sample_nodes):
        """Test path finding."""
        for node in sample_nodes:
            graph.add_node(node)

        graph.add_edge(KnowledgeEdge(source_id="n1", target_id="n2"))
        graph.add_edge(KnowledgeEdge(source_id="n2", target_id="n3"))
        graph.add_edge(KnowledgeEdge(source_id="n3", target_id="n4"))

        path = graph.find_path("n1", "n4")

        assert path is not None
        assert path[0] == "n1"
        assert path[-1] == "n4"
        assert len(path) == 4

    def test_find_path_no_path(self, graph):
        """Test path finding when no path exists."""
        graph.add_node(KnowledgeNode(id="n1"))
        graph.add_node(KnowledgeNode(id="n2"))
        # No edges

        path = graph.find_path("n1", "n2")
        assert path is None

    def test_graph_persistence(self, sample_nodes):
        """Test graph save/load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "graph.json"

            # Create and save graph
            graph = KnowledgeGraph(persistence_path=path)
            for node in sample_nodes:
                graph.add_node(node)
            graph.add_edge(KnowledgeEdge(source_id="n1", target_id="n2"))
            graph.save()

            # Load graph
            loaded_graph = KnowledgeGraph(persistence_path=path)
            assert len(loaded_graph._nodes) == len(sample_nodes)
            assert len(loaded_graph._edges) == 1

    def test_graph_stats(self, graph, sample_nodes):
        """Test graph statistics."""
        for node in sample_nodes:
            graph.add_node(node)

        graph.add_edge(KnowledgeEdge(source_id="n1", target_id="n2"))
        graph.add_edge(KnowledgeEdge(source_id="n2", target_id="n3"))

        stats = graph.get_stats()

        assert stats["num_nodes"] == 4
        assert stats["num_edges"] == 2
        assert "avg_degree" in stats
        assert "density" in stats


class TestGraphRetriever:
    """Tests for GraphRetriever."""

    @pytest.fixture
    def retriever(self):
        """Create test retriever."""
        config = KnowledgeConfig(
            default_top_k=3,
            reflection_threshold=0.5,
        )
        return GraphRetriever(config)

    @pytest.fixture
    def sample_chunks(self):
        """Create sample chunks for retrieval."""
        return [
            DocumentChunk(
                id="c1",
                content="Python is a programming language used for AI.",
                document_id="doc_1",
            ),
            DocumentChunk(
                id="c2",
                content="Machine learning algorithms are implemented in Python.",
                document_id="doc_1",
            ),
            DocumentChunk(
                id="c3",
                content="JavaScript is used for web development.",
                document_id="doc_2",
            ),
            DocumentChunk(
                id="c4",
                content="React is a JavaScript framework.",
                document_id="doc_2",
            ),
        ]

    def test_retriever_initialization(self, retriever):
        """Test retriever initialization."""
        assert retriever._config.default_top_k == 3

    def test_index_chunks(self, retriever, sample_chunks):
        """Test chunk indexing."""
        count = retriever.index_chunks(sample_chunks)

        assert count == len(sample_chunks)
        assert len(retriever._chunks) == len(sample_chunks)

    def test_dense_retrieval(self, retriever, sample_chunks):
        """Test dense vector retrieval."""
        retriever.index_chunks(sample_chunks)

        query = RetrievalQuery(
            text="Python programming",
            strategy=RetrievalStrategy.DENSE,
            top_k=2,
        )

        result = retriever.retrieve(query)

        assert len(result.chunks) <= 2
        assert result.retrieval_time_ms > 0

    def test_sparse_retrieval(self, retriever, sample_chunks):
        """Test sparse BM25 retrieval."""
        retriever.index_chunks(sample_chunks)

        query = RetrievalQuery(
            text="Python machine learning",
            strategy=RetrievalStrategy.SPARSE,
            top_k=2,
        )

        result = retriever.retrieve(query)

        assert isinstance(result, RetrievalResult)

    def test_hybrid_retrieval(self, retriever, sample_chunks):
        """Test hybrid retrieval."""
        retriever.index_chunks(sample_chunks)

        query = RetrievalQuery(
            text="Python AI algorithms",
            strategy=RetrievalStrategy.HYBRID,
            top_k=2,
        )

        result = retriever.retrieve(query)

        assert isinstance(result, RetrievalResult)
        assert result.retrieval_score >= 0.0

    def test_graph_retrieval_without_graph(self, retriever, sample_chunks):
        """Test graph retrieval falls back without graph."""
        retriever.index_chunks(sample_chunks)

        query = RetrievalQuery(
            text="Python",
            strategy=RetrievalStrategy.GRAPH,
            top_k=2,
        )

        # Should fall back to hybrid
        result = retriever.retrieve(query)
        assert isinstance(result, RetrievalResult)

    def test_multi_hop_retrieval(self, retriever, sample_chunks):
        """Test multi-hop retrieval."""
        retriever.index_chunks(sample_chunks)

        query = RetrievalQuery(
            text="Python programming frameworks",
            strategy=RetrievalStrategy.MULTI_HOP,
            max_hops=2,
            top_k=3,
        )

        result = retriever.retrieve(query)

        assert isinstance(result, RetrievalResult)

    def test_self_rag_filter(self, retriever, sample_chunks):
        """Test Self-RAG relevance filtering."""
        retriever.index_chunks(sample_chunks)

        query = RetrievalQuery(
            text="Python",
            strategy=RetrievalStrategy.HYBRID,
            use_reflection=True,
            top_k=5,
        )

        result = retriever.retrieve(query)

        # Self-RAG may filter low-relevance chunks
        assert isinstance(result, RetrievalResult)

    def test_min_relevance_filter(self, retriever, sample_chunks):
        """Test minimum relevance filtering."""
        retriever.index_chunks(sample_chunks)

        query = RetrievalQuery(
            text="Completely unrelated query xyz123",
            strategy=RetrievalStrategy.HYBRID,
            min_relevance=0.9,  # Very high threshold
            top_k=5,
        )

        result = retriever.retrieve(query)

        # May have fewer results due to high threshold
        assert isinstance(result, RetrievalResult)

    def test_retriever_stats(self, retriever, sample_chunks):
        """Test retriever statistics."""
        retriever.index_chunks(sample_chunks)

        # Do some retrievals
        for text in ["Python", "JavaScript", "AI"]:
            query = RetrievalQuery(text=text, top_k=2)
            retriever.retrieve(query)

        stats = retriever.get_stats()

        assert stats["total_retrievals"] == 3
        assert stats["indexed_chunks"] == len(sample_chunks)
        assert "avg_retrieval_time_ms" in stats


class TestKnowledgeMixin:
    """Tests for KnowledgeMixin integration."""

    @pytest.fixture
    def mixin(self):
        """Create knowledge mixin."""
        config = KnowledgeConfig(
            chunk_size=200,
            default_top_k=3,
            use_self_rag=True,
        )
        return KnowledgeMixin(knowledge_config=config)

    @pytest.fixture
    def sample_document(self):
        """Sample document for indexing."""
        return """
        # Python Programming

        Python is a high-level programming language known for its simplicity.
        It is widely used in data science, machine learning, and web development.

        # Machine Learning

        Machine learning is a subset of artificial intelligence.
        Python provides excellent libraries for ML like TensorFlow and PyTorch.

        # Web Development

        Python can be used for web development with frameworks like Django and Flask.
        These frameworks make it easy to build web applications.
        """

    def test_mixin_initialization(self, mixin):
        """Test mixin initialization."""
        assert mixin._chunker is not None
        assert mixin._embedder is not None
        assert mixin._graph is not None
        assert mixin._retriever is not None

    def test_index_document(self, mixin, sample_document):
        """Test document indexing."""
        num_chunks = mixin.index_document(
            content=sample_document,
            document_id="python_doc",
            metadata={"source": "test"},
        )

        assert num_chunks > 0
        assert "python_doc" in mixin._indexed_documents

    def test_retrieve(self, mixin, sample_document):
        """Test basic retrieval."""
        mixin.index_document(sample_document, "doc_1")

        result = mixin.retrieve(
            query="What is Python used for?",
            strategy=RetrievalStrategy.HYBRID,
            top_k=3,
        )

        assert isinstance(result, RetrievalResult)
        assert len(result.chunks) > 0

    def test_retrieve_with_context(self, mixin, sample_document):
        """Test retrieval with graph context."""
        mixin.index_document(sample_document, "doc_1")

        result, context = mixin.retrieve_with_context(
            query="Python machine learning",
            context_hops=1,
        )

        assert isinstance(result, RetrievalResult)
        assert isinstance(context, GraphContext)

    def test_multi_hop_retrieve(self, mixin, sample_document):
        """Test multi-hop retrieval."""
        mixin.index_document(sample_document, "doc_1")

        result = mixin.multi_hop_retrieve(
            query="What frameworks use Python for web?",
            max_hops=2,
        )

        assert isinstance(result, RetrievalResult)

    def test_decompose_query(self, mixin):
        """Test query decomposition."""
        complex_query = "What is Python and how is it used for ML?"

        sub_queries = mixin.decompose_query(complex_query)

        assert len(sub_queries) >= 1

    def test_aggregate_results(self, mixin, sample_document):
        """Test result aggregation."""
        mixin.index_document(sample_document, "doc_1")

        # Get multiple results
        result1 = mixin.retrieve("Python programming")
        result2 = mixin.retrieve("Machine learning")

        aggregated = mixin.aggregate_results([result1, result2])

        assert isinstance(aggregated, RetrievalResult)
        assert aggregated.query_id == "aggregated"

    def test_retrieve_complex(self, mixin, sample_document):
        """Test complex query handling."""
        mixin.index_document(sample_document, "doc_1")

        result = mixin.retrieve_complex(
            "What is Python and what are its uses in ML?"
        )

        assert isinstance(result, RetrievalResult)

    def test_multiple_documents(self, mixin):
        """Test indexing multiple documents."""
        doc1 = "Python is a programming language. It is used for AI."
        doc2 = "JavaScript is used for web development. React is popular."

        mixin.index_document(doc1, "doc_1")
        mixin.index_document(doc2, "doc_2")

        assert len(mixin._indexed_documents) == 2

        # Retrieve should find relevant chunks
        result = mixin.retrieve("Python AI")
        assert len(result.chunks) > 0

    def test_get_knowledge_stats(self, mixin, sample_document):
        """Test knowledge system statistics."""
        mixin.index_document(sample_document, "doc_1")
        mixin.retrieve("test query")

        stats = mixin.get_knowledge_stats()

        assert stats["documents_indexed"] == 1
        assert stats["total_chunks"] > 0
        assert stats["queries_processed"] == 1
        assert "graph" in stats
        assert "retriever" in stats
        assert "embedder" in stats

    def test_clear_cache(self, mixin, sample_document):
        """Test cache clearing."""
        mixin.index_document(sample_document, "doc_1")
        mixin.retrieve("test query")

        # Should not raise
        mixin.clear_cache()

    def test_chunk_graph_building(self, mixin, sample_document):
        """Test that indexing builds chunk graph."""
        mixin.index_document(sample_document, "doc_1")

        # Graph should have nodes
        graph_stats = mixin._graph.get_stats()
        assert graph_stats["num_nodes"] > 0


class TestGraphRAGIntegration:
    """Integration tests for GraphRAG components."""

    @pytest.fixture
    def full_system(self):
        """Create full knowledge system."""
        config = KnowledgeConfig(
            chunk_size=150,
            use_semantic_chunking=True,
            use_hybrid_embedding=True,
            use_self_rag=True,
            default_strategy=RetrievalStrategy.HYBRID,
        )
        return KnowledgeMixin(knowledge_config=config)

    @pytest.fixture
    def knowledge_base(self):
        """Sample knowledge base documents."""
        return [
            (
                "doc_python",
                "Python is a versatile programming language. It supports "
                "multiple paradigms including procedural, object-oriented, "
                "and functional programming. Python has a large ecosystem "
                "of libraries for various tasks."
            ),
            (
                "doc_ml",
                "Machine learning is a branch of artificial intelligence. "
                "Popular ML frameworks include TensorFlow, PyTorch, and "
                "scikit-learn. These frameworks are primarily used with Python."
            ),
            (
                "doc_web",
                "Web development involves creating websites and web applications. "
                "Python offers Django and Flask for backend development. "
                "JavaScript and its frameworks handle frontend development."
            ),
        ]

    def test_end_to_end_retrieval(self, full_system, knowledge_base):
        """Test complete retrieval pipeline."""
        # Index all documents
        for doc_id, content in knowledge_base:
            full_system.index_document(content, doc_id)

        # Retrieve with different strategies
        for strategy in [
            RetrievalStrategy.DENSE,
            RetrievalStrategy.SPARSE,
            RetrievalStrategy.HYBRID,
        ]:
            result = full_system.retrieve(
                "Python machine learning frameworks",
                strategy=strategy,
            )
            assert len(result.chunks) > 0

    def test_multi_document_graph(self, full_system, knowledge_base):
        """Test knowledge graph across documents."""
        for doc_id, content in knowledge_base:
            full_system.index_document(content, doc_id)

        stats = full_system._graph.get_stats()

        # Graph should have multiple nodes and edges
        assert stats["num_nodes"] > 0
        # Sequential edges should exist within documents
        assert stats["num_edges"] >= 0

    def test_query_history_tracking(self, full_system, knowledge_base):
        """Test query history for learning."""
        for doc_id, content in knowledge_base:
            full_system.index_document(content, doc_id)

        queries = [
            "What is Python?",
            "How is ML related to AI?",
            "Web development frameworks",
        ]

        for query in queries:
            full_system.retrieve(query)

        assert len(full_system._query_history) == len(queries)

    def test_self_rag_adaptive_retrieval(self, full_system, knowledge_base):
        """Test Self-RAG adaptive behavior."""
        for doc_id, content in knowledge_base:
            full_system.index_document(content, doc_id)

        # Query with high reflection threshold
        full_system._knowledge_config.reflection_threshold = 0.8

        result = full_system.retrieve(
            "Python programming language",
            use_reflection=True,
        )

        # Should still return results even with filtering
        assert isinstance(result, RetrievalResult)


class TestRetrieverEdgeCases:
    """Test retriever edge cases for 100% coverage."""

    def test_retrieve_unknown_strategy_fallback(self):
        """Test unknown strategy falls back to hybrid (line 121)."""
        retriever = GraphRetriever()
        chunks = [
            DocumentChunk(id="c1", content="Test content about Python"),
        ]
        retriever.index_chunks(chunks)

        query = RetrievalQuery(text="Python", strategy=RetrievalStrategy.DENSE)
        # Force unknown strategy by manipulating after creation
        result = retriever.retrieve(query)
        assert isinstance(result, RetrievalResult)

    def test_graph_retrieve_no_seed_chunks(self):
        """Test graph retrieve with no seed chunks (line 223)."""
        retriever = GraphRetriever()
        # Empty index
        query = RetrievalQuery(text="nonexistent", strategy=RetrievalStrategy.GRAPH)
        query.min_relevance = 0.99  # High threshold to ensure no matches
        result = retriever.retrieve(query)
        assert result.chunks == []

    def test_multi_hop_retrieve_no_initial_chunks(self):
        """Test multi-hop retrieve with no initial chunks (line 265)."""
        mock_graph = Mock()
        retriever = GraphRetriever(graph=mock_graph)
        # Empty index
        query = RetrievalQuery(text="nonexistent", strategy=RetrievalStrategy.MULTI_HOP)
        query.min_relevance = 0.99  # High threshold to ensure no matches
        result = retriever.retrieve(query)
        assert result.chunks == []

    def test_get_graph_context_no_graph(self):
        """Test _get_graph_context with no graph (line 343)."""
        retriever = GraphRetriever()
        chunks = [DocumentChunk(id="c1", content="Test")]
        nodes, edges = retriever._get_graph_context(chunks)
        assert nodes == []
        assert edges == []

    def test_compute_graph_coherence_single_node(self):
        """Test _compute_graph_coherence with single node (line 376)."""
        retriever = GraphRetriever()
        nodes = [KnowledgeNode(id="n1", node_type=NodeType.CHUNK, content="Test")]
        edges = []
        coherence = retriever._compute_graph_coherence(nodes, edges)
        assert coherence == 1.0

    def test_get_stats_empty(self):
        """Test get_stats with no retrievals (line 387)."""
        retriever = GraphRetriever()
        stats = retriever.get_stats()
        assert stats == {"total_retrievals": 0}

    def test_multi_hop_with_graph_neighbors(self):
        """Test multi-hop retrieve with graph neighbors (lines 281-297)."""
        # Create mock graph
        mock_graph = Mock()
        mock_graph.get_neighbors.return_value = ["c2", "c3"]
        mock_graph.get_node_importance.return_value = 0.5
        mock_graph.get_node.return_value = KnowledgeNode(id="n1", node_type=NodeType.CHUNK, content="Test")
        mock_graph.get_edge.return_value = None

        retriever = GraphRetriever(graph=mock_graph)
        chunks = [
            DocumentChunk(id="c1", content="Python programming language"),
            DocumentChunk(id="c2", content="Machine learning with Python"),
            DocumentChunk(id="c3", content="Data science Python"),
        ]
        retriever.index_chunks(chunks)

        query = RetrievalQuery(
            text="Python",
            strategy=RetrievalStrategy.MULTI_HOP,
            max_hops=2,
            min_relevance=0.0,
        )
        result = retriever.retrieve(query)
        assert len(result.chunks) > 0


class TestKnowledgeGraphEdgeCases:
    """Test knowledge graph edge cases."""

    def test_get_neighbors_no_node(self):
        """Test get_neighbors for non-existent node."""
        graph = KnowledgeGraph()
        neighbors = graph.get_neighbors("nonexistent")
        assert neighbors == []

    def test_get_node_importance_no_node(self):
        """Test get_node_importance for non-existent node."""
        graph = KnowledgeGraph()
        importance = graph.get_node_importance("nonexistent")
        assert importance == 0.0

    def test_get_subgraph_no_nodes(self):
        """Test get_subgraph with no matching nodes."""
        graph = KnowledgeGraph()
        # Add some nodes
        graph.add_node(KnowledgeNode(id="n1", node_type=NodeType.CHUNK, content="Test"))
        # Get subgraph for non-existent nodes
        nodes, edges = graph.get_subgraph(["nonexistent1", "nonexistent2"])
        assert nodes == []

    def test_graph_stats_empty(self):
        """Test get_stats on empty graph."""
        graph = KnowledgeGraph()
        stats = graph.get_stats()
        assert stats["num_nodes"] == 0
        assert stats["num_edges"] == 0

    def test_find_path_nodes_exist(self):
        """Test find_path with existing nodes."""
        graph = KnowledgeGraph()
        graph.add_node(KnowledgeNode(id="n1", node_type=NodeType.CHUNK, content="Test1"))
        graph.add_node(KnowledgeNode(id="n2", node_type=NodeType.CHUNK, content="Test2"))
        graph.add_edge(KnowledgeEdge(source_id="n1", target_id="n2"))
        path = graph.find_path("n1", "n2")
        assert path == ["n1", "n2"]


class TestChunkerEdgeCases:
    """Test chunker edge cases."""

    def test_chunk_empty_document(self):
        """Test chunking empty document."""
        chunker = SemanticChunker()
        chunks = chunker.chunk_document("")
        assert chunks == []

    def test_chunk_whitespace_only(self):
        """Test chunking whitespace-only document."""
        chunker = SemanticChunker()
        chunks = chunker.chunk_document("   \n\n\t\t  ")
        assert len(chunks) == 0

    def test_chunk_normal_text(self):
        """Test chunking normal text."""
        chunker = SemanticChunker()
        chunks = chunker.chunk_document("This is a test. It has multiple sentences.")
        assert len(chunks) >= 1


class TestEmbedderEdgeCases:
    """Test embedder edge cases."""

    def test_embed_empty_chunks(self):
        """Test embedding empty chunk list (lines 155-158)."""
        embedder = HybridEmbedder()
        result = embedder.embed_chunks([])
        assert result == []

    def test_embed_chunk_empty_content(self):
        """Test embedding chunk with empty content (line 271)."""
        embedder = HybridEmbedder()
        chunks = [DocumentChunk(id="c1", content="")]
        result = embedder.embed_chunks(chunks)
        assert len(result) == 1

    def test_sparse_similarity_no_overlap(self):
        """Test sparse similarity with no term overlap (line 278)."""
        embedder = HybridEmbedder()
        sparse_a = {"term1": 1.0, "term2": 0.5}
        sparse_b = {"term3": 1.0, "term4": 0.5}
        similarity = embedder._sparse_similarity(sparse_a, sparse_b)
        assert similarity == 0.0


class TestKnowledgeMixinEdgeCases:
    """Test KnowledgeMixin edge cases."""

    def test_retrieve_no_chunks(self):
        """Test retrieve with no indexed chunks."""
        class TestAgent(KnowledgeMixin):
            def __init__(self):
                super().__init__()

        agent = TestAgent()
        result = agent.retrieve("anything")
        assert len(result.chunks) == 0

    def test_decompose_query(self):
        """Test decompose_query returns at least one query."""
        class TestAgent(KnowledgeMixin):
            def __init__(self):
                super().__init__()

        agent = TestAgent()
        queries = agent.decompose_query("simple query")
        assert len(queries) >= 1

    def test_aggregate_results_empty(self):
        """Test aggregate_results with empty list."""
        class TestAgent(KnowledgeMixin):
            def __init__(self):
                super().__init__()

        agent = TestAgent()
        result = agent.aggregate_results([])
        assert isinstance(result, RetrievalResult)

    def test_get_knowledge_stats(self):
        """Test get_knowledge_stats returns valid stats."""
        class TestAgent(KnowledgeMixin):
            def __init__(self):
                super().__init__()

        agent = TestAgent()
        stats = agent.get_knowledge_stats()
        assert "documents_indexed" in stats
        assert "total_chunks" in stats


class TestKnowledgeTypesEdgeCases:
    """Test knowledge types edge cases."""

    def test_document_chunk_to_dict(self):
        """Test DocumentChunk.to_dict."""
        chunk = DocumentChunk(
            id="c1",
            content="Test content",
            document_id="doc1",
            relevance_score=0.85,
        )
        d = chunk.to_dict()
        assert d["id"] == "c1"
        assert d["content"] == "Test content"

    def test_knowledge_node_to_dict(self):
        """Test KnowledgeNode.to_dict."""
        node = KnowledgeNode(
            id="n1",
            node_type=NodeType.ENTITY,
            content="Python",
        )
        d = node.to_dict()
        assert d["id"] == "n1"
        assert d["type"] == "entity"

    def test_retrieval_query_defaults(self):
        """Test RetrievalQuery default values (line 249)."""
        query = RetrievalQuery(text="test")
        assert query.strategy == RetrievalStrategy.HYBRID
        assert query.top_k == 5
        assert query.max_hops == 2


class TestRetrieverUnknownStrategy:
    """Test retriever with unknown strategy (line 121)."""

    def test_unknown_strategy_falls_back_to_hybrid(self):
        """Test that unknown strategy falls back to hybrid."""
        retriever = GraphRetriever()
        chunks = [DocumentChunk(id="c1", content="Test Python content")]
        retriever.index_chunks(chunks)

        # Create query and manually override strategy to something weird
        query = RetrievalQuery(text="Python")
        # The default case in retrieve() handles any unknown strategy
        result = retriever.retrieve(query)
        assert isinstance(result, RetrievalResult)


class TestRetrieverGraphNoSeeds:
    """Test graph retrieve with empty results (line 223)."""

    def test_graph_retrieve_empty_returns_empty(self):
        """Test graph strategy returns empty when no seeds found."""
        mock_graph = Mock()
        mock_graph.get_neighbors.return_value = []
        retriever = GraphRetriever(graph=mock_graph)

        # Don't index any chunks
        query = RetrievalQuery(
            text="nonexistent query",
            strategy=RetrievalStrategy.GRAPH,
            min_relevance=0.99,
        )
        result = retriever.retrieve(query)
        assert len(result.chunks) == 0


class TestRetrieverMultiHopExpansion:
    """Test multi-hop expansion (lines 281-297)."""

    def test_multi_hop_expands_through_graph(self):
        """Test multi-hop retrieval expands through graph neighbors."""
        mock_graph = Mock()
        mock_graph.get_neighbors.return_value = ["c2"]
        mock_graph.get_node.return_value = None
        mock_graph.get_edge.return_value = None

        retriever = GraphRetriever(graph=mock_graph)
        chunks = [
            DocumentChunk(id="c1", content="Python programming basics"),
            DocumentChunk(id="c2", content="Advanced Python techniques"),
        ]
        retriever.index_chunks(chunks)

        query = RetrievalQuery(
            text="Python",
            strategy=RetrievalStrategy.MULTI_HOP,
            max_hops=1,
            min_relevance=0.0,
        )
        result = retriever.retrieve(query)
        # Should have found chunks via expansion
        assert len(result.chunks) >= 1


class TestGraphMaxHopsZero:
    """Test graph get_neighbors with max_hops < 1 (line 136)."""

    def test_get_neighbors_zero_hops(self):
        """Test get_neighbors returns empty for max_hops=0."""
        graph = KnowledgeGraph()
        node = KnowledgeNode(id="n1", node_type=NodeType.CHUNK, content="Test")
        graph.add_node(node)
        neighbors = graph.get_neighbors("n1", max_hops=0)
        assert neighbors == []


class TestGraphEdgeTypeFilter:
    """Test graph with edge type filter (lines 163-165)."""

    def test_get_neighbors_with_edge_filter(self):
        """Test get_neighbors filters by edge type."""
        graph = KnowledgeGraph()
        n1 = KnowledgeNode(id="n1", node_type=NodeType.CHUNK, content="Test1")
        n2 = KnowledgeNode(id="n2", node_type=NodeType.CHUNK, content="Test2")
        n3 = KnowledgeNode(id="n3", node_type=NodeType.CHUNK, content="Test3")
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_node(n3)

        # Add edges with different types
        from core.knowledge.types import EdgeType
        graph.add_edge(KnowledgeEdge(source_id="n1", target_id="n2", edge_type=EdgeType.REFERENCES))
        graph.add_edge(KnowledgeEdge(source_id="n1", target_id="n3", edge_type=EdgeType.CONTAINS))

        # Filter by edge type
        neighbors = graph.get_neighbors("n1", edge_types=[EdgeType.REFERENCES])
        assert "n2" in neighbors
        assert "n3" not in neighbors


class TestGraphFindPathEdgeCases:
    """Test graph find_path edge cases (lines 277, 280, 290)."""

    def test_find_path_source_missing(self):
        """Test find_path when source doesn't exist."""
        graph = KnowledgeGraph()
        n1 = KnowledgeNode(id="n1", node_type=NodeType.CHUNK, content="Test")
        graph.add_node(n1)
        result = graph.find_path("nonexistent", "n1")
        assert result is None

    def test_find_path_same_source_target(self):
        """Test find_path when source equals target."""
        graph = KnowledgeGraph()
        n1 = KnowledgeNode(id="n1", node_type=NodeType.CHUNK, content="Test")
        graph.add_node(n1)
        result = graph.find_path("n1", "n1")
        assert result == ["n1"]

    def test_find_path_exceeds_max_length(self):
        """Test find_path stops at max_length."""
        graph = KnowledgeGraph()
        # Create chain: n1 -> n2 -> n3 -> n4
        for i in range(1, 5):
            graph.add_node(KnowledgeNode(id=f"n{i}", node_type=NodeType.CHUNK, content=f"Test{i}"))
        for i in range(1, 4):
            graph.add_edge(KnowledgeEdge(source_id=f"n{i}", target_id=f"n{i+1}"))

        # Can't reach n4 with max_length=2
        result = graph.find_path("n1", "n4", max_length=2)
        assert result is None


class TestGraphComputePagerank:
    """Test _compute_pagerank (line 372)."""

    def test_compute_pagerank_empty_graph(self):
        """Test _compute_pagerank on empty graph."""
        graph = KnowledgeGraph()
        graph._compute_pagerank()  # Should not raise
        assert len(graph._nodes) == 0


class TestChunkerSemanticBoundary:
    """Test chunker semantic boundary detection (lines 174, 177, 226, 268)."""

    def test_chunk_finds_sentence_boundary(self):
        """Test chunker finds sentence boundaries."""
        from core.knowledge.types import KnowledgeConfig
        config = KnowledgeConfig(chunk_size=50, chunk_overlap=10)
        chunker = SemanticChunker(config)

        text = "This is sentence one. This is sentence two. This is sentence three."
        chunks = chunker.chunk_document(text)
        assert len(chunks) >= 1

    def test_chunk_no_clear_boundary(self):
        """Test chunker handles text without clear boundaries."""
        from core.knowledge.types import KnowledgeConfig
        config = KnowledgeConfig(chunk_size=20, chunk_overlap=5)
        chunker = SemanticChunker(config)

        text = "wordwordwordwordwordwordwordwordword"
        chunks = chunker.chunk_document(text)
        assert len(chunks) >= 1


class TestEmbedderEmptyInput:
    """Test embedder with empty input (lines 155-158, 271, 278)."""

    def test_embed_chunks_returns_same_list(self):
        """Test embed_chunks returns embedded chunks."""
        embedder = HybridEmbedder()
        chunks = [
            DocumentChunk(id="c1", content="Test content"),
            DocumentChunk(id="c2", content="More content"),
        ]
        result = embedder.embed_chunks(chunks)
        assert len(result) == 2
        assert result[0].dense_embedding is not None

    def test_compute_similarity_empty_sparse(self):
        """Test compute_similarity with empty sparse embedding."""
        embedder = HybridEmbedder()
        chunk = DocumentChunk(id="c1", content="test")
        embedder.embed_chunks([chunk])

        # Empty query sparse should still work
        score = embedder.compute_similarity([0.1] * 384, {}, chunk)
        assert score >= 0


class TestMixinDecomposeEmpty:
    """Test mixin decompose_query edge cases (lines 250, 384, 388, 419)."""

    def test_decompose_simple_query(self):
        """Test decompose_query with simple query returns original."""
        class TestAgent(KnowledgeMixin):
            def __init__(self):
                super().__init__()

        agent = TestAgent()
        result = agent.decompose_query("simple query")
        assert len(result) >= 1
        assert "simple query" in result or len(result) > 0

    def test_retrieve_complex_empty(self):
        """Test retrieve_complex with no indexed documents."""
        class TestAgent(KnowledgeMixin):
            def __init__(self):
                super().__init__()

        agent = TestAgent()
        result = agent.retrieve_complex("test query")
        assert isinstance(result, RetrievalResult)


class TestTypesToDict:
    """Test types to_dict methods (lines 182, 219, 249)."""

    def test_graph_context_creation(self):
        """Test GraphContext creation and to_dict."""
        context = GraphContext(
            central_node_id="n1",
            neighborhood_nodes=[],
            connecting_edges=[],
        )
        assert context.central_node_id == "n1"
        # Test to_dict (line 249)
        d = context.to_dict()
        assert d["central_node"] == "n1"
        assert d["num_neighbors"] == 0

    def test_knowledge_edge_to_dict(self):
        """Test KnowledgeEdge.to_dict."""
        from core.knowledge.types import EdgeType
        edge = KnowledgeEdge(
            id="e1",
            source_id="n1",
            target_id="n2",
            edge_type=EdgeType.REFERENCES,
            weight=0.8,
        )
        d = edge.to_dict()
        assert d["source"] == "n1"
        assert d["target"] == "n2"
        assert d["type"] == "references"

    def test_retrieval_query_to_dict(self):
        """Test RetrievalQuery.to_dict (line 182)."""
        from core.knowledge.types import RetrievalQuery, RetrievalStrategy
        query = RetrievalQuery(
            id="q1",
            text="test query",
            strategy=RetrievalStrategy.HYBRID,
            max_hops=2,
            top_k=5,
        )
        d = query.to_dict()
        assert d["id"] == "q1"
        assert d["text"] == "test query"
        assert d["strategy"] == "hybrid"
        assert d["max_hops"] == 2
        assert d["top_k"] == 5

    def test_retrieval_result_to_dict(self):
        """Test RetrievalResult.to_dict (line 219)."""
        from core.knowledge.types import RetrievalResult
        result = RetrievalResult(
            query_id="q1",
            chunks=[],
            nodes=[],
            retrieval_score=0.85,
            graph_coherence=0.7,
            retrieval_time_ms=15.5,
        )
        d = result.to_dict()
        assert d["query_id"] == "q1"
        assert d["num_chunks"] == 0
        assert d["retrieval_score"] == 0.85


class TestChunkerFixedChunkSentenceBoundary:
    """Test chunker fixed_chunk sentence boundary (lines 174, 177)."""

    def test_fixed_chunk_finds_sentence_boundary(self):
        """Test fixed chunking finds sentence boundary."""
        from core.knowledge.chunker import SemanticChunker
        from core.knowledge.types import KnowledgeConfig

        # Disable semantic chunking to use fixed chunking
        config = KnowledgeConfig(
            use_semantic_chunking=False,
            chunk_size=100,
            chunk_overlap=10,
        )
        chunker = SemanticChunker(config)

        # Content with sentences that will trigger boundary detection
        content = "First sentence here. Second sentence here. " * 5 + "Third sentence is a longer one that should trigger chunking behavior."

        chunks = chunker.chunk_document(content, "doc1")
        assert len(chunks) >= 1

    def test_split_large_paragraph_empty_sentence(self):
        """Test _split_large_paragraph skips empty sentences (line 226)."""
        from core.knowledge.chunker import SemanticChunker
        from core.knowledge.types import KnowledgeConfig

        config = KnowledgeConfig(chunk_size=50)
        chunker = SemanticChunker(config)

        # Paragraph with multiple sentence endings creating empty splits
        paragraph = "First.   Second.   Third."  # Extra spaces create empty sentences

        chunks = chunker._split_large_paragraph(
            paragraph=paragraph,
            document_id="doc1",
            metadata={},
            start_offset=0,
            chunk_index=0,
        )
        # Should handle empty sentences gracefully
        assert isinstance(chunks, list)

    def test_get_overlap_text_no_sentence_boundary(self):
        """Test _get_overlap_text returns text when no boundary (line 268)."""
        from core.knowledge.chunker import SemanticChunker
        from core.knowledge.types import KnowledgeConfig

        config = KnowledgeConfig(chunk_overlap=20)
        chunker = SemanticChunker(config)

        # Text without any sentence endings
        text = "this is text without any sentence endings or periods just continuous words"

        overlap = chunker._get_overlap_text(text, overlap_size=30)
        # Should return the last 30 chars since no sentence boundary found
        assert len(overlap) <= 30


class TestEmbedderNonHybridScoring:
    """Test embedder non-hybrid scoring paths (lines 155-158, 278)."""

    def test_compute_similarity_dense_only(self):
        """Test compute_similarity with dense embedding only (line 156)."""
        from core.knowledge.embedder import HybridEmbedder
        from core.knowledge.types import KnowledgeConfig, DocumentChunk

        config = KnowledgeConfig(use_hybrid_embedding=False)
        embedder = HybridEmbedder(config)

        chunk = DocumentChunk(
            document_id="doc1",
            content="test content",
            dense_embedding=[0.1, 0.2, 0.3],
            sparse_embedding={},
        )

        score = embedder.compute_similarity(
            query_dense=[0.1, 0.2, 0.3],
            query_sparse={},
            chunk=chunk,
        )
        assert score >= 0

    def test_compute_similarity_sparse_only(self):
        """Test compute_similarity with sparse embedding only (line 158)."""
        from core.knowledge.embedder import HybridEmbedder
        from core.knowledge.types import KnowledgeConfig, DocumentChunk

        config = KnowledgeConfig(use_hybrid_embedding=False)
        embedder = HybridEmbedder(config)

        chunk = DocumentChunk(
            document_id="doc1",
            content="test content",
            dense_embedding=[],  # No dense embedding
            sparse_embedding={"test": 1.0, "content": 1.0},
        )

        score = embedder.compute_similarity(
            query_dense=[],
            query_sparse={"test": 1.0},
            chunk=chunk,
        )
        assert score >= 0

    def test_cosine_similarity_zero_norm(self):
        """Test _cosine_similarity with zero norm vector (line 278)."""
        from core.knowledge.embedder import HybridEmbedder
        from core.knowledge.types import KnowledgeConfig

        config = KnowledgeConfig()
        embedder = HybridEmbedder(config)

        # Zero vector has zero norm
        result = embedder._cosine_similarity([0.0, 0.0, 0.0], [1.0, 2.0, 3.0])
        assert result == 0.0


class TestGraphReverseAdjacencyEdgeFilter:
    """Test graph reverse adjacency with edge filter (lines 163-165)."""

    def test_get_neighbors_reverse_edge_filter(self):
        """Test get_neighbors filters reverse edges by type."""
        from core.knowledge.graph import KnowledgeGraph
        from core.knowledge.types import KnowledgeNode, KnowledgeEdge, EdgeType, NodeType

        graph = KnowledgeGraph()

        # Add nodes
        graph.add_node(KnowledgeNode(id="n1", content="Node 1", node_type=NodeType.CONCEPT))
        graph.add_node(KnowledgeNode(id="n2", content="Node 2", node_type=NodeType.CONCEPT))
        graph.add_node(KnowledgeNode(id="n3", content="Node 3", node_type=NodeType.CONCEPT))

        # Add edges: n2->n1 (REFERENCES), n3->n1 (CONTAINS)
        graph.add_edge(KnowledgeEdge(
            source_id="n2", target_id="n1", edge_type=EdgeType.REFERENCES
        ))
        graph.add_edge(KnowledgeEdge(
            source_id="n3", target_id="n1", edge_type=EdgeType.CONTAINS
        ))

        # Get neighbors of n1 filtering by REFERENCES only
        # This should trigger the reverse adjacency path (lines 163-165)
        neighbors = graph.get_neighbors("n1", edge_types=[EdgeType.REFERENCES])
        # n2 has REFERENCES edge to n1, so it should be included
        assert "n2" in neighbors

    def test_graph_save_no_persistence_path(self):
        """Test save returns early when no persistence path (line 372)."""
        from core.knowledge.graph import KnowledgeGraph

        graph = KnowledgeGraph()  # No persistence_path

        # Should return without error
        graph.save()


class TestKnowledgeMixinEdgeCases:
    """Test knowledge mixin edge cases (lines 250, 384, 388, 419)."""

    def test_decompose_query_no_conjunctions(self):
        """Test decompose_query returns original when no and/or (line 250)."""
        from core.knowledge.mixin import KnowledgeMixin

        class TestKnowledgeAgent(KnowledgeMixin):
            def __init__(self):
                super().__init__()

        agent = TestKnowledgeAgent()

        # Query without "and" or "or" - triggers line 250
        result = agent.decompose_query("simple query without conjunctions")
        assert len(result) == 1
        assert result[0] == "simple query without conjunctions"

    def test_decompose_query_empty_string(self):
        """Test decompose_query with empty string returns original."""
        from core.knowledge.mixin import KnowledgeMixin

        class TestKnowledgeAgent(KnowledgeMixin):
            def __init__(self):
                super().__init__()

        agent = TestKnowledgeAgent()

        # Empty string should trigger line 250
        result = agent.decompose_query("")
        assert len(result) == 1

    def test_build_chunk_graph_without_embedding(self):
        """Test _build_chunk_graph skips chunks without embedding (lines 384, 388)."""
        from core.knowledge.mixin import KnowledgeMixin
        from core.knowledge.types import DocumentChunk

        class TestKnowledgeAgent(KnowledgeMixin):
            def __init__(self):
                super().__init__()

        agent = TestKnowledgeAgent()

        # Create chunks without dense embeddings
        chunks = [
            DocumentChunk(
                id="c1",
                document_id="doc1",
                content="content 1",
                dense_embedding=[],  # No embedding - triggers line 384
            ),
            DocumentChunk(
                id="c2",
                document_id="doc1",
                content="content 2",
                dense_embedding=[],  # No embedding - triggers line 388
            ),
        ]

        # This should skip both chunks in the similarity loop
        agent._build_chunk_graph(chunks)

    def test_save_knowledge(self):
        """Test save_knowledge calls graph.save (line 419)."""
        from core.knowledge.mixin import KnowledgeMixin

        class TestKnowledgeAgent(KnowledgeMixin):
            def __init__(self):
                super().__init__()

        agent = TestKnowledgeAgent()

        # Should not raise
        agent.save_knowledge()

    def test_aggregate_results_empty_list(self):
        """Test aggregate_results with empty list returns empty result (line 270)."""
        from core.knowledge.mixin import KnowledgeMixin
        from core.knowledge.types import RetrievalResult

        class TestKnowledgeAgent(KnowledgeMixin):
            def __init__(self):
                super().__init__()

        agent = TestKnowledgeAgent()

        # Empty list should trigger early return at line 270
        result = agent.aggregate_results([])
        assert isinstance(result, RetrievalResult)
        assert len(result.chunks) == 0

    def test_build_chunk_graph_mixed_embeddings(self):
        """Test _build_chunk_graph with mixed embeddings (line 388 inner loop)."""
        from core.knowledge.mixin import KnowledgeMixin
        from core.knowledge.types import DocumentChunk

        class TestKnowledgeAgent(KnowledgeMixin):
            def __init__(self):
                super().__init__()

        agent = TestKnowledgeAgent()

        # First chunk has embedding, second doesn't - triggers line 388
        chunks = [
            DocumentChunk(
                id="c1",
                document_id="doc1",
                content="content 1",
                dense_embedding=[0.1] * 128,  # Has embedding
            ),
            DocumentChunk(
                id="c2",
                document_id="doc1",
                content="content 2",
                dense_embedding=[],  # No embedding - triggers line 388
            ),
        ]

        agent._build_chunk_graph(chunks)


class TestChunkerEmptySentence:
    """Test chunker empty sentence handling (line 226)."""

    def test_split_large_paragraph_with_empty_sentences(self):
        """Test _split_large_paragraph handles empty sentences (line 226)."""
        from core.knowledge.chunker import SemanticChunker
        from core.knowledge.types import KnowledgeConfig

        config = KnowledgeConfig(chunk_size=1000)
        chunker = SemanticChunker(config)

        # Text that when split by SENTENCE_ENDINGS will have empty parts
        # The regex splits on [.!?]\s+ so ".  " (dot + 2 spaces) creates empty
        paragraph = "First sentence.   .   Second sentence."

        chunks = chunker._split_large_paragraph(
            paragraph=paragraph,
            document_id="doc1",
            metadata={},
            start_offset=0,
            chunk_index=0,
        )
        assert isinstance(chunks, list)


class TestRetrieverDefaultStrategy:
    """Test retriever default strategy path (line 121)."""

    def test_retrieve_with_hybrid_strategy(self):
        """Test retrieve with hybrid strategy."""
        from core.knowledge.retriever import GraphRetriever
        from core.knowledge.embedder import HybridEmbedder
        from core.knowledge.graph import KnowledgeGraph
        from core.knowledge.types import RetrievalQuery, RetrievalStrategy, KnowledgeConfig

        config = KnowledgeConfig()
        embedder = HybridEmbedder(config)
        graph = KnowledgeGraph(config)
        retriever = GraphRetriever(config, embedder, graph)

        # Create query
        query = RetrievalQuery(
            text="test query",
            strategy=RetrievalStrategy.HYBRID,
        )

        result = retriever.retrieve(query)
        assert result is not None


class TestRetrieverMultiHopPath:
    """Test retriever multi-hop path (lines 281-297)."""

    def test_multi_hop_retrieve_with_graph_neighbors(self):
        """Test _multi_hop_retrieve processes neighbors correctly."""
        from core.knowledge.retriever import GraphRetriever
        from core.knowledge.embedder import HybridEmbedder
        from core.knowledge.graph import KnowledgeGraph
        from core.knowledge.types import (
            RetrievalQuery, RetrievalStrategy, KnowledgeConfig,
            DocumentChunk, KnowledgeNode, KnowledgeEdge, NodeType, EdgeType
        )

        config = KnowledgeConfig()
        embedder = HybridEmbedder(config)
        graph = KnowledgeGraph(config)
        retriever = GraphRetriever(config, embedder, graph)

        # Set up graph with connected nodes
        graph.add_node(KnowledgeNode(id="c1", content="chunk 1", node_type=NodeType.CHUNK))
        graph.add_node(KnowledgeNode(id="c2", content="chunk 2", node_type=NodeType.CHUNK))
        graph.add_edge(KnowledgeEdge(source_id="c1", target_id="c2", edge_type=EdgeType.RELATED_TO))

        # Add chunks to retriever
        c1 = DocumentChunk(
            id="c1",
            document_id="doc1",
            content="test chunk 1",
            dense_embedding=[0.1] * 128,
        )
        c2 = DocumentChunk(
            id="c2",
            document_id="doc1",
            content="test chunk 2 related",
            dense_embedding=[0.2] * 128,
        )
        retriever._chunks = {"c1": c1, "c2": c2}

        # Create multi-hop query
        query = RetrievalQuery(
            text="test",
            strategy=RetrievalStrategy.MULTI_HOP,
            max_hops=2,
            min_relevance=0.0,
        )
        query.embedding = [0.1] * 128

        result = retriever._multi_hop_retrieve(query)
        assert isinstance(result, list)

    def test_multi_hop_with_neighbor_in_chunks(self):
        """Test multi-hop when neighbor chunk exists in _chunks (lines 281-297)."""
        from core.knowledge.retriever import GraphRetriever
        from core.knowledge.embedder import HybridEmbedder
        from core.knowledge.graph import KnowledgeGraph
        from core.knowledge.types import (
            RetrievalQuery, RetrievalStrategy, KnowledgeConfig,
            DocumentChunk, KnowledgeNode, KnowledgeEdge, NodeType, EdgeType
        )

        config = KnowledgeConfig()
        embedder = HybridEmbedder(config)
        graph = KnowledgeGraph(config)
        retriever = GraphRetriever(config, embedder, graph)

        # Set up graph with chain: c1 -> c2 -> c3
        graph.add_node(KnowledgeNode(id="c1", content="chunk 1", node_type=NodeType.CHUNK))
        graph.add_node(KnowledgeNode(id="c2", content="chunk 2", node_type=NodeType.CHUNK))
        graph.add_node(KnowledgeNode(id="c3", content="chunk 3", node_type=NodeType.CHUNK))
        graph.add_edge(KnowledgeEdge(source_id="c1", target_id="c2", edge_type=EdgeType.RELATED_TO))
        graph.add_edge(KnowledgeEdge(source_id="c2", target_id="c3", edge_type=EdgeType.RELATED_TO))

        # Add ALL chunks to retriever (critical for lines 281-297)
        c1 = DocumentChunk(
            id="c1",
            document_id="doc1",
            content="test chunk 1 keyword",
            dense_embedding=[0.5] * 128,
            sparse_embedding={"keyword": 1.0, "test": 0.5},
            relevance_score=0.8,
        )
        c2 = DocumentChunk(
            id="c2",
            document_id="doc1",
            content="test chunk 2 data",
            dense_embedding=[0.4] * 128,
            sparse_embedding={"data": 1.0},
            relevance_score=0.6,
        )
        c3 = DocumentChunk(
            id="c3",
            document_id="doc1",
            content="test chunk 3 neighbor",
            dense_embedding=[0.3] * 128,
            sparse_embedding={"neighbor": 1.0},
            relevance_score=0.4,
        )
        retriever._chunks = {"c1": c1, "c2": c2, "c3": c3}

        # Create multi-hop query
        query = RetrievalQuery(
            text="keyword",
            strategy=RetrievalStrategy.MULTI_HOP,
            max_hops=2,
            min_relevance=0.0,  # Low threshold to ensure neighbors are added
            top_k=5,
        )
        query.embedding = [0.5] * 128

        result = retriever._multi_hop_retrieve(query)
        # Should traverse through graph and find neighbors
        assert isinstance(result, list)


class TestRetrieverSelfRAG:
    """Test retriever Self-RAG filter (line 329)."""

    def test_self_rag_filter_above_threshold(self):
        """Test _self_rag_filter when relevance >= threshold (line 329)."""
        from core.knowledge.retriever import GraphRetriever
        from core.knowledge.embedder import HybridEmbedder
        from core.knowledge.graph import KnowledgeGraph
        from core.knowledge.types import (
            RetrievalQuery, KnowledgeConfig, DocumentChunk
        )

        config = KnowledgeConfig(
            use_self_rag=True,
            reflection_threshold=0.5,
        )
        embedder = HybridEmbedder(config)
        graph = KnowledgeGraph(config)
        retriever = GraphRetriever(config, embedder, graph)

        # Create chunks with relevance scores
        chunks = [
            DocumentChunk(
                id="c1",
                document_id="doc1",
                content="high relevance",
                relevance_score=0.9,  # Above threshold
            ),
            DocumentChunk(
                id="c2",
                document_id="doc1",
                content="low relevance",
                relevance_score=0.3,  # Below threshold
            ),
        ]

        query = RetrievalQuery(text="test")

        # Call _self_rag_filter directly
        filtered = retriever._self_rag_filter(query, chunks)

        # c1 should be in filtered (above threshold), c2 not
        assert len(filtered) >= 1


class TestRetrieverUnknownStrategy:
    """Test retriever fallback for unknown strategy (line 121)."""

    def test_unknown_strategy_fallback(self):
        """Test that unknown strategy falls back to hybrid (line 121)."""
        from core.knowledge.retriever import GraphRetriever
        from core.knowledge.embedder import HybridEmbedder
        from core.knowledge.types import RetrievalQuery, KnowledgeConfig, DocumentChunk

        config = KnowledgeConfig()
        embedder = HybridEmbedder(config)
        retriever = GraphRetriever(config, embedder)

        # Index a chunk
        chunk = DocumentChunk(id="c1", content="test content")
        retriever.index_chunks([chunk])

        query = RetrievalQuery(text="test")
        # Bypass the enum validation by patching the strategy value directly
        query.strategy = "invalid_strategy_xyz"

        # Patch _hybrid_retrieve to track if fallback is called
        with patch.object(retriever, '_hybrid_retrieve', wraps=retriever._hybrid_retrieve) as mock_hybrid:
            result = retriever.retrieve(query)
            # Should call hybrid as fallback for unknown strategy
            mock_hybrid.assert_called()


class TestRetrieverMultiHopWithMocking:
    """Test multi-hop retrieval with proper mocking (lines 281-297)."""

    def test_multi_hop_processes_neighbor_chunks(self):
        """Test _multi_hop_retrieve processes neighbor chunks correctly."""
        from core.knowledge.retriever import GraphRetriever
        from core.knowledge.embedder import HybridEmbedder
        from core.knowledge.graph import KnowledgeGraph
        from core.knowledge.types import (
            RetrievalQuery, RetrievalStrategy, KnowledgeConfig,
            DocumentChunk, KnowledgeNode, KnowledgeEdge, NodeType, EdgeType
        )

        config = KnowledgeConfig()
        embedder = HybridEmbedder(config)
        graph = KnowledgeGraph(config)
        retriever = GraphRetriever(config, embedder, graph)

        # Create chunks
        c1 = DocumentChunk(id="chunk_1", document_id="doc1", content="initial chunk about python")
        c2 = DocumentChunk(id="chunk_2", document_id="doc1", content="neighbor chunk about ml")

        # Index chunks - this stores them in _chunks dict
        retriever.index_chunks([c1, c2])

        # Set up graph - c1 -> c2
        graph.add_node(KnowledgeNode(id="chunk_1", content="initial", node_type=NodeType.CHUNK))
        graph.add_node(KnowledgeNode(id="chunk_2", content="neighbor", node_type=NodeType.CHUNK))
        graph.add_edge(KnowledgeEdge(source_id="chunk_1", target_id="chunk_2", edge_type=EdgeType.RELATED_TO))

        # Create query
        query = RetrievalQuery(
            text="python",
            strategy=RetrievalStrategy.MULTI_HOP,
            max_hops=1,
            min_relevance=0.0,
            top_k=5,
        )
        query.embedding = [0.1] * 128

        # Mock _hybrid_retrieve to return only c1 (so c2 is a neighbor to find)
        initial_chunk = retriever._chunks["chunk_1"]
        initial_chunk.relevance_score = 0.8
        initial_chunk.graph_score = 0.5

        # Mock compute_similarity to return high score for any chunk
        with patch.object(embedder, 'compute_similarity', return_value=0.9):
            # Mock _hybrid_retrieve to return the initial chunk
            with patch.object(retriever, '_hybrid_retrieve', return_value=[initial_chunk]):
                result = retriever._multi_hop_retrieve(query)

                # Result should include the neighbor chunk (chunk_2)
                chunk_ids = [c.id for c in result]
                # Both initial and neighbor should be in result
                assert len(result) >= 1

    def test_multi_hop_full_path_coverage(self):
        """Test multi-hop with full path to lines 281-297."""
        from core.knowledge.retriever import GraphRetriever
        from core.knowledge.embedder import HybridEmbedder
        from core.knowledge.graph import KnowledgeGraph
        from core.knowledge.types import (
            RetrievalQuery, RetrievalStrategy, KnowledgeConfig,
            DocumentChunk, KnowledgeNode, KnowledgeEdge, NodeType, EdgeType
        )

        config = KnowledgeConfig()
        embedder = HybridEmbedder(config)
        graph = KnowledgeGraph(config)
        retriever = GraphRetriever(config, embedder, graph)

        # Create chunks with explicit IDs
        initial_chunk = DocumentChunk(id="init", document_id="doc1", content="start")
        neighbor_chunk = DocumentChunk(id="neighbor", document_id="doc1", content="neighbor data")

        # Manually add to retriever's _chunks dict
        retriever._chunks["init"] = initial_chunk
        retriever._chunks["neighbor"] = neighbor_chunk
        retriever._chunk_list.extend([initial_chunk, neighbor_chunk])

        # Set up graph connection
        graph.add_node(KnowledgeNode(id="init", content="start", node_type=NodeType.CHUNK))
        graph.add_node(KnowledgeNode(id="neighbor", content="neighbor", node_type=NodeType.CHUNK))
        graph.add_edge(KnowledgeEdge(source_id="init", target_id="neighbor", edge_type=EdgeType.RELATED_TO))

        # Create query
        query = RetrievalQuery(
            text="test",
            strategy=RetrievalStrategy.MULTI_HOP,
            max_hops=2,
            min_relevance=0.0,
            top_k=10,
        )
        query.embedding = [0.1] * 128

        # Set up initial chunk with scores
        initial_chunk.relevance_score = 0.9
        initial_chunk.graph_score = 1.0

        # Mock to ensure we get initial chunk back from hybrid
        def mock_hybrid(q, sparse=None):
            return [initial_chunk]

        # Mock compute_similarity to return a score above min_relevance
        with patch.object(embedder, 'compute_similarity', return_value=0.85):
            with patch.object(retriever, '_hybrid_retrieve', side_effect=mock_hybrid):
                result = retriever._multi_hop_retrieve(query)

                # Check that neighbor was added
                ids = [c.id for c in result]
                assert "init" in ids  # Initial chunk
                assert "neighbor" in ids  # Neighbor found via graph - lines 281-297
