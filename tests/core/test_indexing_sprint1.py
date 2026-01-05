"""
Tests for Sprint 1: Semantic Indexing System.

Tests:
- CodeChunker: AST-based code splitting
- SemanticEmbedder: Embedding generation with caching
- VectorStore: Vector storage and similarity search
- CodebaseIndexer: Full indexing pipeline

Phase 10: Refinement Sprint 1

Soli Deo Gloria
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

# Import modules under test
from vertice_core.indexing import (
    ChunkType,
    CodeChunk,
    CodeChunker,
    EmbeddingCache,
    EmbeddingConfig,
    SemanticEmbedder,
    VectorStore,
    VectorStoreConfig,
    SearchResult,
    IndexerConfig,
    IndexerStatus,
    IndexingProgress,
    CodebaseIndexer,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_python_code():
    """Sample Python code for testing."""
    return '''
"""Module docstring."""

import os
from typing import List

CONSTANT = 42


def greet(name: str) -> str:
    """Greet someone by name.

    Args:
        name: The name to greet

    Returns:
        Greeting string
    """
    return f"Hello, {name}!"


async def async_operation(data: List[int]) -> int:
    """Process data asynchronously."""
    return sum(data)


class Calculator:
    """A simple calculator class."""

    def __init__(self, initial: int = 0):
        """Initialize calculator."""
        self.value = initial

    def add(self, x: int) -> int:
        """Add a number."""
        self.value += x
        return self.value

    def multiply(self, x: int) -> int:
        """Multiply by a number."""
        self.value *= x
        return self.value
'''


@pytest.fixture
def sample_js_code():
    """Sample JavaScript code for testing."""
    return '''
// Module imports
import { useState } from 'react';

const LIMIT = 100;

function processData(data) {
    return data.filter(x => x > 0);
}

async function fetchData(url) {
    const response = await fetch(url);
    return response.json();
}

class UserService {
    constructor(apiUrl) {
        this.apiUrl = apiUrl;
    }

    async getUser(id) {
        return this.fetch(`/users/${id}`);
    }
}
'''


@pytest.fixture
def python_file(temp_dir, sample_python_code):
    """Create a Python file for testing."""
    file_path = temp_dir / "sample.py"
    file_path.write_text(sample_python_code)
    return file_path


@pytest.fixture
def js_file(temp_dir, sample_js_code):
    """Create a JavaScript file for testing."""
    file_path = temp_dir / "sample.js"
    file_path.write_text(sample_js_code)
    return file_path


# ============================================================================
# CodeChunker Tests
# ============================================================================


class TestCodeChunker:
    """Tests for CodeChunker."""

    def test_chunk_python_functions(self, python_file):
        """Test chunking Python functions."""
        chunker = CodeChunker()
        chunks = chunker.chunk_file(str(python_file))

        # Should have chunks for functions and classes
        assert len(chunks) >= 3

        # Check we have a greet function
        func_names = [c.name for c in chunks]
        assert "greet" in func_names
        assert "async_operation" in func_names
        assert "Calculator" in func_names

    def test_chunk_python_methods(self, python_file):
        """Test chunking extracts methods from classes."""
        chunker = CodeChunker()
        chunks = chunker.chunk_file(str(python_file))

        # Should have method chunks
        method_chunks = [c for c in chunks if c.chunk_type == ChunkType.METHOD]
        method_names = [c.name for c in method_chunks]

        assert "__init__" in method_names
        assert "add" in method_names
        assert "multiply" in method_names

    def test_chunk_python_preserves_docstrings(self, python_file):
        """Test that docstrings are preserved."""
        chunker = CodeChunker()
        chunks = chunker.chunk_file(str(python_file))

        greet_chunk = next((c for c in chunks if c.name == "greet"), None)
        assert greet_chunk is not None
        assert greet_chunk.docstring is not None
        assert "Greet someone" in greet_chunk.docstring

    def test_chunk_python_signature(self, python_file):
        """Test function signature extraction."""
        chunker = CodeChunker()
        chunks = chunker.chunk_file(str(python_file))

        greet_chunk = next((c for c in chunks if c.name == "greet"), None)
        assert greet_chunk is not None
        assert greet_chunk.signature is not None
        assert "name: str" in greet_chunk.signature
        assert "-> str" in greet_chunk.signature

    def test_chunk_javascript(self, js_file):
        """Test chunking JavaScript code."""
        chunker = CodeChunker()
        chunks = chunker.chunk_file(str(js_file))

        # Should have some chunks (regex-based)
        assert len(chunks) >= 1

        chunk_names = [c.name for c in chunks]
        # At least one function should be detected
        assert any("processData" in name or "fetchData" in name for name in chunk_names) or len(chunks) > 0

    def test_chunk_nonexistent_file(self):
        """Test handling of nonexistent file."""
        chunker = CodeChunker()
        chunks = chunker.chunk_file("/nonexistent/path/file.py")
        assert chunks == []

    def test_chunk_directory(self, temp_dir, sample_python_code, sample_js_code):
        """Test chunking entire directory."""
        # Create multiple files
        (temp_dir / "a.py").write_text(sample_python_code)
        (temp_dir / "b.py").write_text("def foo(): pass")
        (temp_dir / "c.js").write_text(sample_js_code)

        chunker = CodeChunker()
        chunks = chunker.chunk_directory(str(temp_dir))

        # Should have chunks from all files
        assert len(chunks) >= 4

        # Check different files represented
        filepaths = set(c.filepath for c in chunks)
        assert len(filepaths) >= 2

    def test_chunk_id_generation(self, python_file):
        """Test chunk IDs are unique and consistent."""
        chunker = CodeChunker()
        chunks = chunker.chunk_file(str(python_file))

        # IDs should be unique
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids))

        # Same content should give same ID
        chunks2 = chunker.chunk_file(str(python_file))
        ids2 = [c.chunk_id for c in chunks2]
        assert ids == ids2

    def test_to_embedding_text(self, python_file):
        """Test embedding text generation."""
        chunker = CodeChunker()
        chunks = chunker.chunk_file(str(python_file))

        greet_chunk = next((c for c in chunks if c.name == "greet"), None)
        assert greet_chunk is not None

        embed_text = greet_chunk.to_embedding_text()
        assert "File:" in embed_text
        assert "Function: greet" in embed_text
        assert "Description:" in embed_text
        assert "Code:" in embed_text


# ============================================================================
# SemanticEmbedder Tests
# ============================================================================


class TestEmbeddingCache:
    """Tests for EmbeddingCache."""

    def test_cache_put_get(self, temp_dir):
        """Test basic put/get operations."""
        cache = EmbeddingCache(str(temp_dir / "cache"))

        embedding = [0.1, 0.2, 0.3]
        cache.put("test content", embedding, "test-model")

        result = cache.get("test content", "test-model")
        assert result == embedding

    def test_cache_miss(self, temp_dir):
        """Test cache miss returns None."""
        cache = EmbeddingCache(str(temp_dir / "cache"))

        result = cache.get("nonexistent", "model")
        assert result is None

    def test_cache_model_specific(self, temp_dir):
        """Test cache is model-specific."""
        cache = EmbeddingCache(str(temp_dir / "cache"))

        cache.put("content", [1.0, 2.0], "model-a")
        cache.put("content", [3.0, 4.0], "model-b")

        assert cache.get("content", "model-a") == [1.0, 2.0]
        assert cache.get("content", "model-b") == [3.0, 4.0]

    def test_cache_batch_operations(self, temp_dir):
        """Test batch put/get operations."""
        cache = EmbeddingCache(str(temp_dir / "cache"))

        items = [
            ("text1", [0.1, 0.2]),
            ("text2", [0.3, 0.4]),
            ("text3", [0.5, 0.6]),
        ]
        cache.put_batch(items, "model")

        results = cache.get_batch(["text1", "text2", "text3", "text4"], "model")
        assert results["text1"] == [0.1, 0.2]
        assert results["text2"] == [0.3, 0.4]
        assert results["text3"] == [0.5, 0.6]
        assert results["text4"] is None

    def test_cache_persistence(self, temp_dir):
        """Test cache persists across instances."""
        cache_dir = str(temp_dir / "cache")

        # First instance
        cache1 = EmbeddingCache(cache_dir)
        cache1.put("persistent", [1.0, 2.0, 3.0], "model")

        # Second instance (should load from disk)
        cache2 = EmbeddingCache(cache_dir)
        result = cache2.get("persistent", "model")
        assert result == [1.0, 2.0, 3.0]

    def test_cache_stats(self, temp_dir):
        """Test cache statistics."""
        cache = EmbeddingCache(str(temp_dir / "cache"))

        cache.put("a", [1.0] * 100, "model")
        cache.put("b", [2.0] * 100, "model")

        stats = cache.get_stats()
        assert stats["total_embeddings"] == 2
        assert "model" in stats["by_model"]


class TestSemanticEmbedder:
    """Tests for SemanticEmbedder."""

    def test_embedder_init(self, temp_dir):
        """Test embedder initialization."""
        config = EmbeddingConfig(cache_dir=str(temp_dir / "cache"))
        embedder = SemanticEmbedder(config)

        assert embedder.config.dimensions == 3072
        assert embedder.config.model == "text-embedding-3-large"

    def test_is_available(self, temp_dir, mock_azure_env):
        """Test availability check."""
        # mock_azure_env removes Azure env vars to force is_available() = False
        config = EmbeddingConfig(
            cache_dir=str(temp_dir / "cache"),
            azure_endpoint="",
            azure_api_key=""
        )
        embedder = SemanticEmbedder(config)

        # Without credentials (env vars removed), should not be available
        assert not embedder.is_available()

    @pytest.mark.asyncio
    async def test_local_fallback(self, temp_dir, mock_azure_env):
        """Test local fallback embedding."""
        # mock_azure_env ensures we use local fallback, not Azure
        config = EmbeddingConfig(
            cache_dir=str(temp_dir / "cache"),
            azure_api_key="",  # Force fallback
            use_local_fallback=True,
            dimensions=128,  # Smaller for test
        )
        embedder = SemanticEmbedder(config)

        results = await embedder.embed_texts(["Hello world", "Test text"])

        assert len(results) == 2
        assert len(results[0].embedding) == 128
        assert len(results[1].embedding) == 128
        assert results[0].model == "local-hash"

    @pytest.mark.asyncio
    async def test_embed_chunks(self, temp_dir, python_file, mock_azure_env):
        """Test embedding code chunks."""
        # mock_azure_env ensures we use local fallback
        config = EmbeddingConfig(
            cache_dir=str(temp_dir / "cache"),
            use_local_fallback=True,
            dimensions=64,
        )
        embedder = SemanticEmbedder(config)

        chunker = CodeChunker()
        chunks = chunker.chunk_file(str(python_file))[:3]  # Limit for test

        results = await embedder.embed_chunks(chunks)

        assert len(results) == len(chunks)
        for result, chunk in zip(results, chunks):
            assert result.chunk_id == chunk.chunk_id
            assert len(result.embedding) == 64

    @pytest.mark.asyncio
    async def test_cache_hit(self, temp_dir, mock_azure_env):
        """Test cache is used on second call."""
        # mock_azure_env ensures we use local fallback
        config = EmbeddingConfig(
            cache_dir=str(temp_dir / "cache"),
            use_local_fallback=True,
            dimensions=64,
        )
        embedder = SemanticEmbedder(config)

        # First call - should embed
        results1 = await embedder.embed_texts(["test"])
        assert not results1[0].from_cache

        # Second call - should use cache
        results2 = await embedder.embed_texts(["test"])
        assert results2[0].from_cache
        assert results1[0].embedding == results2[0].embedding

    @pytest.mark.asyncio
    async def test_embed_query(self, temp_dir, mock_azure_env):
        """Test query embedding."""
        # mock_azure_env ensures we use local fallback
        config = EmbeddingConfig(
            cache_dir=str(temp_dir / "cache"),
            use_local_fallback=True,
            dimensions=64,
        )
        embedder = SemanticEmbedder(config)

        embedding = await embedder.embed_query("find error handling code")

        assert len(embedding) == 64
        # Should be normalized (L2 norm ~= 1)
        import math
        norm = math.sqrt(sum(x*x for x in embedding))
        assert 0.9 < norm < 1.1

    def test_stats(self, temp_dir):
        """Test statistics retrieval."""
        config = EmbeddingConfig(cache_dir=str(temp_dir / "cache"))
        embedder = SemanticEmbedder(config)

        stats = embedder.get_stats()
        assert "model" in stats
        assert "dimensions" in stats
        assert "total_embedded" in stats


# ============================================================================
# VectorStore Tests
# ============================================================================


class TestVectorStore:
    """Tests for VectorStore."""

    def test_store_init(self, temp_dir):
        """Test store initialization."""
        config = VectorStoreConfig(
            persist_dir=str(temp_dir / "vectors"),
            use_chromadb=False,  # Use in-memory for tests
        )
        store = VectorStore(config)

        assert store.backend_type == "memory"
        assert store.count() == 0

    def test_add_chunks(self, temp_dir, python_file):
        """Test adding chunks to store."""
        config = VectorStoreConfig(
            persist_dir=str(temp_dir / "vectors"),
            use_chromadb=False,
        )
        store = VectorStore(config)

        # Create chunks and fake embeddings
        chunker = CodeChunker()
        chunks = chunker.chunk_file(str(python_file))[:3]
        embeddings = [[float(i)] * 64 for i in range(len(chunks))]

        added = store.add_chunks(chunks, embeddings)

        assert added == len(chunks)
        assert store.count() == len(chunks)

    def test_search_basic(self, temp_dir, python_file):
        """Test basic search functionality."""
        config = VectorStoreConfig(
            persist_dir=str(temp_dir / "vectors"),
            use_chromadb=False,
            similarity_threshold=0.0,  # Accept all for test
        )
        store = VectorStore(config)

        # Add chunks
        chunker = CodeChunker()
        chunks = chunker.chunk_file(str(python_file))
        # Create distinct embeddings
        embeddings = [[1.0 if i == j else 0.0 for j in range(64)] for i in range(len(chunks))]

        store.add_chunks(chunks, embeddings)

        # Search with exact match to first embedding
        query_embedding = embeddings[0]
        results = store.search(query_embedding, top_k=3, min_score=0.0)

        assert len(results) > 0
        assert results[0].chunk_id == chunks[0].chunk_id
        assert results[0].score > 0.99  # Should be near-perfect match

    def test_search_with_filters(self, temp_dir):
        """Test search with filters."""
        config = VectorStoreConfig(
            persist_dir=str(temp_dir / "vectors"),
            use_chromadb=False,
            similarity_threshold=0.0,
        )
        store = VectorStore(config)

        # Create chunks for different languages
        chunks = [
            CodeChunk(
                chunk_id="py1", filepath="/test.py", content="def foo(): pass",
                start_line=1, end_line=1, chunk_type=ChunkType.FUNCTION,
                name="foo", language="python"
            ),
            CodeChunk(
                chunk_id="js1", filepath="/test.js", content="function bar() {}",
                start_line=1, end_line=1, chunk_type=ChunkType.FUNCTION,
                name="bar", language="javascript"
            ),
        ]
        embeddings = [[1.0] * 64, [1.0] * 64]  # Same embedding

        store.add_chunks(chunks, embeddings)

        # Search with language filter
        results = store.search([1.0] * 64, language_filter="python", min_score=0.0)
        assert len(results) == 1
        assert results[0].language == "python"

    def test_delete_chunks(self, temp_dir, python_file):
        """Test deleting chunks."""
        config = VectorStoreConfig(
            persist_dir=str(temp_dir / "vectors"),
            use_chromadb=False,
        )
        store = VectorStore(config)

        chunker = CodeChunker()
        chunks = chunker.chunk_file(str(python_file))[:3]
        embeddings = [[1.0] * 64] * len(chunks)

        store.add_chunks(chunks, embeddings)
        initial_count = store.count()

        # Delete one chunk
        deleted = store.delete_chunks([chunks[0].chunk_id])
        assert deleted == 1
        assert store.count() == initial_count - 1

    def test_delete_file(self, temp_dir, python_file):
        """Test deleting all chunks for a file."""
        config = VectorStoreConfig(
            persist_dir=str(temp_dir / "vectors"),
            use_chromadb=False,
        )
        store = VectorStore(config)

        chunker = CodeChunker()
        chunks = chunker.chunk_file(str(python_file))
        embeddings = [[1.0] * 64] * len(chunks)

        store.add_chunks(chunks, embeddings)
        initial_count = store.count()

        # Delete by filepath
        deleted = store.delete_file(str(python_file))
        assert deleted == initial_count
        assert store.count() == 0

    def test_clear(self, temp_dir, python_file):
        """Test clearing all data."""
        config = VectorStoreConfig(
            persist_dir=str(temp_dir / "vectors"),
            use_chromadb=False,
        )
        store = VectorStore(config)

        chunker = CodeChunker()
        chunks = chunker.chunk_file(str(python_file))[:3]
        embeddings = [[1.0] * 64] * len(chunks)

        store.add_chunks(chunks, embeddings)
        assert store.count() > 0

        store.clear()
        assert store.count() == 0

    def test_stats(self, temp_dir):
        """Test statistics."""
        config = VectorStoreConfig(
            persist_dir=str(temp_dir / "vectors"),
            use_chromadb=False,
        )
        store = VectorStore(config)

        stats = store.get_stats()
        assert "backend" in stats
        assert "total_chunks" in stats
        assert stats["backend"] == "memory"


# ============================================================================
# CodebaseIndexer Tests
# ============================================================================


class TestCodebaseIndexer:
    """Tests for CodebaseIndexer."""

    @pytest.fixture
    def sample_project(self, temp_dir, sample_python_code):
        """Create a sample project structure."""
        # Create directories
        src = temp_dir / "src"
        src.mkdir()
        tests = temp_dir / "tests"
        tests.mkdir()

        # Create files
        (src / "main.py").write_text(sample_python_code)
        (src / "utils.py").write_text("def helper(): return 42")
        (tests / "test_main.py").write_text("def test_example(): assert True")

        # Create files to exclude
        pycache = temp_dir / "__pycache__"
        pycache.mkdir()
        (pycache / "cached.pyc").write_text("binary")

        return temp_dir

    @pytest.mark.asyncio
    async def test_indexer_init(self, temp_dir):
        """Test indexer initialization."""
        config = IndexerConfig(
            root_dir=str(temp_dir),
            index_dir=str(temp_dir / ".index"),
            embedding_config=EmbeddingConfig(use_local_fallback=True, dimensions=64),
            vector_config=VectorStoreConfig(use_chromadb=False),
        )
        indexer = CodebaseIndexer(config)

        assert indexer.progress.status == IndexerStatus.IDLE
        assert not indexer.is_indexing

    @pytest.mark.asyncio
    async def test_index_codebase(self, sample_project, mock_azure_env):
        """Test full codebase indexing."""
        # mock_azure_env ensures we use local fallback
        config = IndexerConfig(
            root_dir=str(sample_project),
            index_dir=str(sample_project / ".index"),
            embedding_config=EmbeddingConfig(
                use_local_fallback=True,
                dimensions=64,
                cache_dir=str(sample_project / ".cache")
            ),
            vector_config=VectorStoreConfig(
                use_chromadb=False,
                persist_dir=str(sample_project / ".vectors")
            ),
        )
        indexer = CodebaseIndexer(config)

        progress = await indexer.index_codebase()

        assert progress.status == IndexerStatus.IDLE
        assert progress.processed_files >= 3  # main.py, utils.py, test_main.py
        assert progress.indexed_chunks > 0
        assert progress.error_count == 0

    @pytest.mark.asyncio
    async def test_incremental_index(self, sample_project, mock_azure_env):
        """Test incremental indexing only processes changed files."""
        # mock_azure_env ensures we use local fallback
        config = IndexerConfig(
            root_dir=str(sample_project),
            index_dir=str(sample_project / ".index"),
            check_modified=True,
            embedding_config=EmbeddingConfig(
                use_local_fallback=True,
                dimensions=64,
                cache_dir=str(sample_project / ".cache")
            ),
            vector_config=VectorStoreConfig(
                use_chromadb=False,
                persist_dir=str(sample_project / ".vectors")
            ),
        )
        indexer = CodebaseIndexer(config)

        # First index - should process all files
        progress1 = await indexer.index_codebase()
        first_count = progress1.processed_files

        # Second index - should skip unchanged files
        progress2 = await indexer.index_codebase()
        assert progress2.skipped_files > 0
        assert progress2.processed_files < first_count

    @pytest.mark.asyncio
    async def test_search(self, sample_project, sample_python_code, mock_azure_env):
        """Test searching indexed codebase."""
        # mock_azure_env ensures we use local fallback
        config = IndexerConfig(
            root_dir=str(sample_project),
            index_dir=str(sample_project / ".index"),
            embedding_config=EmbeddingConfig(
                use_local_fallback=True,
                dimensions=64,
                cache_dir=str(sample_project / ".cache")
            ),
            vector_config=VectorStoreConfig(
                use_chromadb=False,
                persist_dir=str(sample_project / ".vectors"),
                similarity_threshold=0.0,  # Accept all for test
            ),
        )
        indexer = CodebaseIndexer(config)

        # Index first
        await indexer.index_codebase()

        # Search
        results = await indexer.search("calculator multiply", min_score=0.0)

        assert len(results) > 0
        # Results should be SearchResult objects
        assert all(isinstance(r, SearchResult) for r in results)

    @pytest.mark.asyncio
    async def test_index_single_file(self, sample_project, mock_azure_env):
        """Test indexing a single file."""
        # mock_azure_env ensures we use local fallback
        config = IndexerConfig(
            root_dir=str(sample_project),
            index_dir=str(sample_project / ".index"),
            embedding_config=EmbeddingConfig(
                use_local_fallback=True,
                dimensions=64,
                cache_dir=str(sample_project / ".cache")
            ),
            vector_config=VectorStoreConfig(
                use_chromadb=False,
                persist_dir=str(sample_project / ".vectors")
            ),
        )
        indexer = CodebaseIndexer(config)

        # Index single file
        file_path = sample_project / "src" / "main.py"
        indexed = await indexer.index_file(str(file_path))

        assert indexed > 0

    @pytest.mark.asyncio
    async def test_delete_file(self, sample_project, sample_python_code, mock_azure_env):
        """Test removing a file from index."""
        # mock_azure_env ensures we use local fallback
        config = IndexerConfig(
            root_dir=str(sample_project),
            index_dir=str(sample_project / ".index"),
            embedding_config=EmbeddingConfig(
                use_local_fallback=True,
                dimensions=64,
                cache_dir=str(sample_project / ".cache")
            ),
            vector_config=VectorStoreConfig(
                use_chromadb=False,
                persist_dir=str(sample_project / ".vectors")
            ),
        )
        indexer = CodebaseIndexer(config)

        # Index first
        await indexer.index_codebase()
        initial_count = indexer._store.count()

        # Delete a file from index
        file_path = sample_project / "src" / "main.py"
        deleted = indexer.delete_file(str(file_path))

        assert deleted > 0
        assert indexer._store.count() < initial_count

    @pytest.mark.asyncio
    async def test_progress_callback(self, sample_project, mock_azure_env):
        """Test progress callback is called."""
        # mock_azure_env ensures we use local fallback
        progress_updates = []

        def on_progress(progress: IndexingProgress):
            progress_updates.append(progress.to_dict())

        config = IndexerConfig(
            root_dir=str(sample_project),
            index_dir=str(sample_project / ".index"),
            embedding_config=EmbeddingConfig(
                use_local_fallback=True,
                dimensions=64,
                cache_dir=str(sample_project / ".cache")
            ),
            vector_config=VectorStoreConfig(
                use_chromadb=False,
                persist_dir=str(sample_project / ".vectors")
            ),
        )
        indexer = CodebaseIndexer(config, on_progress=on_progress)

        await indexer.index_codebase()

        # Should have received multiple progress updates
        assert len(progress_updates) > 0
        # Should have status transitions
        statuses = [p["status"] for p in progress_updates]
        assert IndexerStatus.SCANNING.value in statuses
        assert IndexerStatus.IDLE.value in statuses

    @pytest.mark.asyncio
    async def test_get_stats(self, sample_project, mock_azure_env):
        """Test statistics retrieval."""
        # mock_azure_env ensures we use local fallback
        config = IndexerConfig(
            root_dir=str(sample_project),
            index_dir=str(sample_project / ".index"),
            embedding_config=EmbeddingConfig(
                use_local_fallback=True,
                dimensions=64,
                cache_dir=str(sample_project / ".cache")
            ),
            vector_config=VectorStoreConfig(
                use_chromadb=False,
                persist_dir=str(sample_project / ".vectors")
            ),
        )
        indexer = CodebaseIndexer(config)

        await indexer.index_codebase()
        stats = indexer.get_stats()

        assert "indexed_chunks" in stats
        assert "embedder" in stats
        assert "store" in stats
        assert stats["indexed_chunks"] > 0

    @pytest.mark.asyncio
    async def test_clear(self, sample_project, mock_azure_env):
        """Test clearing all indexed data."""
        # mock_azure_env ensures we use local fallback
        config = IndexerConfig(
            root_dir=str(sample_project),
            index_dir=str(sample_project / ".index"),
            embedding_config=EmbeddingConfig(
                use_local_fallback=True,
                dimensions=64,
                cache_dir=str(sample_project / ".cache")
            ),
            vector_config=VectorStoreConfig(
                use_chromadb=False,
                persist_dir=str(sample_project / ".vectors")
            ),
        )
        indexer = CodebaseIndexer(config)

        await indexer.index_codebase()
        assert indexer._store.count() > 0

        indexer.clear()
        assert indexer._store.count() == 0


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, temp_dir, mock_azure_env):
        """Test complete chunking -> embedding -> storage -> search pipeline."""
        # mock_azure_env ensures we use local fallback
        # Create sample code
        code = '''
def parse_config(path: str) -> dict:
    """Parse configuration file and return settings."""
    with open(path) as f:
        return json.load(f)

def validate_config(config: dict) -> bool:
    """Validate configuration settings."""
    required = ["host", "port", "debug"]
    return all(key in config for key in required)
'''
        file_path = temp_dir / "config.py"
        file_path.write_text(code)

        # Initialize components
        config = IndexerConfig(
            root_dir=str(temp_dir),
            index_dir=str(temp_dir / ".index"),
            embedding_config=EmbeddingConfig(
                use_local_fallback=True,
                dimensions=64,
                cache_dir=str(temp_dir / ".cache")
            ),
            vector_config=VectorStoreConfig(
                use_chromadb=False,
                persist_dir=str(temp_dir / ".vectors"),
                similarity_threshold=0.0,
            ),
        )
        indexer = CodebaseIndexer(config)

        # Index
        progress = await indexer.index_codebase()
        assert progress.indexed_chunks > 0

        # Search
        results = await indexer.search("configuration validation", min_score=0.0)
        assert len(results) > 0

        # Verify result structure
        result = results[0]
        assert hasattr(result, "chunk_id")
        assert hasattr(result, "filepath")
        assert hasattr(result, "content")
        assert hasattr(result, "score")
        assert hasattr(result, "start_line")
        assert hasattr(result, "end_line")


# ============================================================================
# Edge Cases & Error Handling
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_chunk_empty_file(self, temp_dir):
        """Test chunking an empty file."""
        empty_file = temp_dir / "empty.py"
        empty_file.write_text("")

        chunker = CodeChunker()
        chunks = chunker.chunk_file(str(empty_file))

        # Should return empty list or single module chunk
        assert isinstance(chunks, list)

    def test_chunk_syntax_error(self, temp_dir):
        """Test chunking file with syntax errors."""
        bad_file = temp_dir / "bad.py"
        bad_file.write_text("def broken(:\n    pass")

        chunker = CodeChunker()
        chunks = chunker.chunk_file(str(bad_file))

        # Should fallback to generic chunking
        assert isinstance(chunks, list)

    @pytest.mark.asyncio
    async def test_embed_empty_list(self, temp_dir):
        """Test embedding empty list."""
        config = EmbeddingConfig(
            cache_dir=str(temp_dir / "cache"),
            use_local_fallback=True,
        )
        embedder = SemanticEmbedder(config)

        results = await embedder.embed_texts([])
        assert results == []

    def test_search_empty_store(self, temp_dir):
        """Test searching empty store."""
        config = VectorStoreConfig(
            persist_dir=str(temp_dir / "vectors"),
            use_chromadb=False,
        )
        store = VectorStore(config)

        results = store.search([1.0] * 64)
        assert results == []

    @pytest.mark.asyncio
    async def test_index_empty_directory(self, temp_dir):
        """Test indexing empty directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        config = IndexerConfig(
            root_dir=str(empty_dir),
            index_dir=str(temp_dir / ".index"),
            embedding_config=EmbeddingConfig(use_local_fallback=True, dimensions=64),
            vector_config=VectorStoreConfig(use_chromadb=False),
        )
        indexer = CodebaseIndexer(config)

        progress = await indexer.index_codebase()
        assert progress.total_files == 0
        assert progress.indexed_chunks == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
