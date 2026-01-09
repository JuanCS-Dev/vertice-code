"""
Knowledge Module

Agentic RAG 2.0 with GraphRAG and knowledge graph integration.

References:
- arXiv:2501.00309 (GraphRAG Survey)
- arXiv:2410.05983 (GNN-RAG for Multi-Hop Reasoning)
- arXiv:2404.16130 (KG²RAG: Chunk Expansion)
- arXiv:2312.10997 (Self-RAG: Self-Reflective RAG)
- arXiv:2404.03242 (RAG for LLMs Survey)
"""

from .types import (
    DocumentChunk,
    KnowledgeNode,
    KnowledgeEdge,
    RetrievalQuery,
    RetrievalResult,
    GraphContext,
    KnowledgeConfig,
)
from .chunker import SemanticChunker
from .embedder import HybridEmbedder
from .retriever import GraphRetriever
from .graph import KnowledgeGraph
from .mixin import KnowledgeMixin

__all__ = [
    # Types
    "DocumentChunk",
    "KnowledgeNode",
    "KnowledgeEdge",
    "RetrievalQuery",
    "RetrievalResult",
    "GraphContext",
    "KnowledgeConfig",
    # Core
    "SemanticChunker",
    "HybridEmbedder",
    "GraphRetriever",
    "KnowledgeGraph",
    "KnowledgeMixin",
]
