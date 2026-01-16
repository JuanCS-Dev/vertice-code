"""
Hybrid Embedder

Combines dense and sparse embeddings for hybrid retrieval.

References:
- arXiv:2404.03242 (RAG for LLMs Survey)
- arXiv:2501.00309 (GraphRAG)
- BM25 (Robertson & Zaragoza, 2009)
"""

from __future__ import annotations

import logging
import math
import re
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple

from .types import DocumentChunk, KnowledgeConfig

logger = logging.getLogger(__name__)


class HybridEmbedder:
    """
    Hybrid embedding system combining dense and sparse representations.

    Implements:
    - Dense embeddings (semantic similarity)
    - Sparse embeddings (BM25-style keyword matching)
    - Hybrid scoring with configurable weights

    References:
    - Dense: Neural embeddings for semantic similarity
    - Sparse: BM25 for keyword matching (handles OOV, exact match)
    """

    # Common stopwords for sparse embedding
    STOPWORDS = {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "as",
        "is",
        "was",
        "are",
        "were",
        "been",
        "be",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "shall",
        "can",
        "this",
        "that",
        "these",
        "those",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
    }

    def __init__(
        self,
        config: Optional[KnowledgeConfig] = None,
        dense_encoder: Optional[Callable[[str], List[float]]] = None,
    ):
        """
        Initialize embedder.

        Args:
            config: Knowledge configuration
            dense_encoder: Optional custom dense encoder function
        """
        self._config = config or KnowledgeConfig()
        self._dense_encoder = dense_encoder or self._default_dense_encoder

        # BM25 parameters
        self._k1 = 1.5
        self._b = 0.75

        # Document statistics for BM25
        self._doc_count = 0
        self._doc_lengths: Dict[str, int] = {}
        self._avg_doc_length = 0.0
        self._term_doc_freqs: Dict[str, int] = defaultdict(int)

        # Embedding cache
        self._embedding_cache: Dict[str, List[float]] = {}

    def embed_chunks(
        self,
        chunks: List[DocumentChunk],
    ) -> List[DocumentChunk]:
        """
        Compute embeddings for chunks.

        Args:
            chunks: Chunks to embed

        Returns:
            Chunks with embeddings populated
        """
        # Update document statistics
        self._update_doc_stats(chunks)

        for chunk in chunks:
            # Dense embedding
            if self._config.use_hybrid_embedding or not chunk.sparse_embedding:
                chunk.dense_embedding = self._get_dense_embedding(chunk.content)

            # Sparse embedding (BM25)
            if self._config.use_hybrid_embedding or not chunk.dense_embedding:
                chunk.sparse_embedding = self._compute_sparse_embedding(chunk.content)

        logger.debug(f"[Embedder] Embedded {len(chunks)} chunks")
        return chunks

    def embed_query(
        self,
        query: str,
    ) -> Tuple[List[float], Dict[str, float]]:
        """
        Compute embeddings for a query.

        Args:
            query: Query text

        Returns:
            Tuple of (dense_embedding, sparse_embedding)
        """
        dense = self._get_dense_embedding(query)
        sparse = self._compute_query_sparse_embedding(query)
        return dense, sparse

    def compute_similarity(
        self,
        query_dense: List[float],
        query_sparse: Dict[str, float],
        chunk: DocumentChunk,
    ) -> float:
        """
        Compute hybrid similarity between query and chunk.

        Args:
            query_dense: Query dense embedding
            query_sparse: Query sparse embedding
            chunk: Target chunk

        Returns:
            Hybrid similarity score
        """
        dense_score = 0.0
        sparse_score = 0.0

        # Dense similarity (cosine)
        if query_dense and chunk.dense_embedding:
            dense_score = self._cosine_similarity(query_dense, chunk.dense_embedding)

        # Sparse similarity (BM25-style)
        if query_sparse and chunk.sparse_embedding:
            sparse_score = self._sparse_similarity(query_sparse, chunk.sparse_embedding)

        # Hybrid combination
        if self._config.use_hybrid_embedding:
            return (
                self._config.dense_weight * dense_score + self._config.sparse_weight * sparse_score
            )
        elif chunk.dense_embedding:
            return dense_score
        else:
            return sparse_score

    def _get_dense_embedding(self, text: str) -> List[float]:
        """Get dense embedding with caching."""
        if self._config.cache_embeddings and text in self._embedding_cache:
            return self._embedding_cache[text]

        embedding = self._dense_encoder(text)

        if self._config.cache_embeddings:
            self._embedding_cache[text] = embedding

        return embedding

    def _default_dense_encoder(self, text: str) -> List[float]:
        """
        Default dense encoder (placeholder).

        In production, use sentence-transformers or similar.
        """
        # Simple hash-based pseudo-embedding for demonstration
        # Replace with actual model in production
        dim = self._config.embedding_dim
        embedding = [0.0] * dim

        words = text.lower().split()
        for i, word in enumerate(words[:dim]):
            # Simple hash-based value
            h = hash(word) % 1000000 / 1000000.0
            embedding[i % dim] += h

        # Normalize
        norm = math.sqrt(sum(x * x for x in embedding)) or 1.0
        embedding = [x / norm for x in embedding]

        return embedding

    def _compute_sparse_embedding(self, text: str) -> Dict[str, float]:
        """
        Compute sparse BM25-style embedding.

        Uses TF-IDF inspired weighting.
        """
        tokens = self._tokenize(text)
        doc_length = len(tokens)

        # Term frequencies
        tf: Dict[str, int] = defaultdict(int)
        for token in tokens:
            tf[token] += 1

        # BM25 scoring
        sparse = {}
        for term, freq in tf.items():
            if term in self.STOPWORDS:
                continue

            # IDF component
            df = self._term_doc_freqs.get(term, 1)
            idf = math.log((self._doc_count - df + 0.5) / (df + 0.5) + 1)

            # TF component with saturation
            tf_score = (freq * (self._k1 + 1)) / (
                freq
                + self._k1 * (1 - self._b + self._b * doc_length / max(self._avg_doc_length, 1))
            )

            sparse[term] = tf_score * idf

        return sparse

    def _compute_query_sparse_embedding(self, query: str) -> Dict[str, float]:
        """Compute sparse embedding for query."""
        tokens = self._tokenize(query)

        # Simple TF for query
        tf: Dict[str, float] = defaultdict(float)
        for token in tokens:
            if token not in self.STOPWORDS:
                tf[token] += 1.0

        # Normalize
        total = sum(tf.values()) or 1.0
        return {term: count / total for term, count in tf.items()}

    def _update_doc_stats(self, chunks: List[DocumentChunk]) -> None:
        """Update document statistics for BM25."""
        for chunk in chunks:
            tokens = self._tokenize(chunk.content)
            doc_id = chunk.id

            self._doc_lengths[doc_id] = len(tokens)

            # Update term document frequencies
            unique_terms = set(tokens)
            for term in unique_terms:
                self._term_doc_freqs[term] += 1

        self._doc_count = len(self._doc_lengths)
        self._avg_doc_length = (
            sum(self._doc_lengths.values()) / self._doc_count if self._doc_count > 0 else 1.0
        )

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for sparse embedding."""
        # Simple whitespace + punctuation tokenization
        text = text.lower()
        tokens = re.findall(r"\b\w+\b", text)
        return tokens

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def _sparse_similarity(
        self,
        query: Dict[str, float],
        doc: Dict[str, float],
    ) -> float:
        """Compute sparse similarity (dot product of common terms)."""
        score = 0.0
        for term, query_weight in query.items():
            if term in doc:
                score += query_weight * doc[term]
        return score

    def clear_cache(self) -> None:
        """Clear embedding cache."""
        self._embedding_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get embedder statistics."""
        return {
            "doc_count": self._doc_count,
            "avg_doc_length": self._avg_doc_length,
            "vocab_size": len(self._term_doc_freqs),
            "cache_size": len(self._embedding_cache),
        }
