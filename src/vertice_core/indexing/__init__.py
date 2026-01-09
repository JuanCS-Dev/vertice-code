"""
Semantic Indexing Module - Codebase Intelligence.

Phase 10: Refinement Sprint 1

Components:
- CodeChunker: Split code into semantic chunks (functions, classes)
- SemanticEmbedder: Generate embeddings via OpenAI/Azure
- VectorStore: ChromaDB integration for similarity search
- CodebaseIndexer: Background indexing service

Inspired by Cursor's codebase indexing.

Soli Deo Gloria
"""

from __future__ import annotations

from .chunker import (
    CodeChunk,
    CodeChunker,
    ChunkType,
)
from .embedder import (
    EmbeddingConfig,
    EmbeddingResult,
    EmbeddingCache,
    SemanticEmbedder,
    get_embedder,
)
from .vector_store import (
    VectorStoreConfig,
    SearchResult,
    VectorStore,
    get_vector_store,
    CHROMADB_AVAILABLE,
)
from .indexer import (
    IndexerStatus,
    IndexerConfig,
    IndexingProgress,
    CodebaseIndexer,
    get_indexer,
)

__all__ = [
    # Chunker
    "CodeChunk",
    "CodeChunker",
    "ChunkType",
    # Embedder
    "EmbeddingConfig",
    "EmbeddingResult",
    "EmbeddingCache",
    "SemanticEmbedder",
    "get_embedder",
    # Vector Store
    "VectorStoreConfig",
    "SearchResult",
    "VectorStore",
    "get_vector_store",
    "CHROMADB_AVAILABLE",
    # Indexer
    "IndexerStatus",
    "IndexerConfig",
    "IndexingProgress",
    "CodebaseIndexer",
    "get_indexer",
]
