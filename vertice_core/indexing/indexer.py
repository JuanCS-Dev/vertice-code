"""
Codebase Indexer - Background Semantic Indexing.

Orchestrates chunking, embedding, and vector storage for codebase search.

Features:
- Full initial indexing
- Incremental updates (only modified files)
- File watching for automatic re-indexing
- Status reporting for TUI integration
- Concurrent processing for speed

Phase 10: Refinement Sprint 1

Soli Deo Gloria
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .chunker import CodeChunk, CodeChunker
from .embedder import EmbeddingConfig, SemanticEmbedder, get_embedder
from .vector_store import SearchResult, VectorStore, VectorStoreConfig, get_vector_store

logger = logging.getLogger(__name__)


class IndexerStatus(str, Enum):
    """Indexer status states."""

    IDLE = "idle"
    SCANNING = "scanning"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    WATCHING = "watching"
    ERROR = "error"


@dataclass
class IndexerConfig:
    """Configuration for the codebase indexer."""

    # Paths
    root_dir: str = "."
    index_dir: str = ".vertice/index"

    # File patterns
    extensions: List[str] = field(
        default_factory=lambda: [
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".go",
            ".rs",
            ".java",
            ".c",
            ".cpp",
            ".h",
        ]
    )
    exclude_patterns: List[str] = field(
        default_factory=lambda: [
            "__pycache__",
            "node_modules",
            ".git",
            ".venv",
            "venv",
            "dist",
            "build",
            ".egg-info",
            ".pytest_cache",
            ".mypy_cache",
            ".vertice",
            ".cache",
            "*.pyc",
            "*.pyo",
        ]
    )

    # Processing
    batch_size: int = 50  # Files per batch
    max_concurrent: int = 5  # Concurrent embedding requests
    max_file_size_kb: int = 500  # Skip files larger than this

    # Incremental indexing
    check_modified: bool = True  # Only re-index modified files

    # Embedding config (passed to SemanticEmbedder)
    embedding_config: Optional[EmbeddingConfig] = None

    # Vector store config
    vector_config: Optional[VectorStoreConfig] = None


@dataclass
class IndexingProgress:
    """Progress information during indexing."""

    status: IndexerStatus = IndexerStatus.IDLE
    total_files: int = 0
    processed_files: int = 0
    total_chunks: int = 0
    indexed_chunks: int = 0
    skipped_files: int = 0
    error_count: int = 0
    current_file: str = ""
    start_time: float = 0.0
    errors: List[str] = field(default_factory=list)

    @property
    def progress_percent(self) -> float:
        """Get progress as percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time == 0:
            return 0.0
        return time.time() - self.start_time

    @property
    def files_per_second(self) -> float:
        """Get processing rate."""
        elapsed = self.elapsed_seconds
        if elapsed == 0:
            return 0.0
        return self.processed_files / elapsed

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "status": self.status.value,
            "progress": f"{self.progress_percent:.1f}%",
            "files": f"{self.processed_files}/{self.total_files}",
            "chunks": self.indexed_chunks,
            "skipped": self.skipped_files,
            "errors": self.error_count,
            "elapsed": f"{self.elapsed_seconds:.1f}s",
            "rate": f"{self.files_per_second:.1f} files/s",
            "current": self.current_file,
        }


class FileHashCache:
    """
    Tracks file modification state for incremental indexing.

    Uses content hash + mtime for change detection.
    """

    def __init__(self, cache_path: str):
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._hashes: Dict[str, Tuple[str, float]] = {}  # filepath -> (hash, mtime)
        self._load()

    def _load(self) -> None:
        """Load cache from disk."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r") as f:
                    data = json.load(f)
                    self._hashes = {k: tuple(v) for k, v in data.items()}
            except (OSError, json.JSONDecodeError) as e:
                logger.debug(f"Could not load hash cache: {e}")
                self._hashes = {}

    def _save(self) -> None:
        """Save cache to disk."""
        try:
            with open(self.cache_path, "w") as f:
                json.dump({k: list(v) for k, v in self._hashes.items()}, f)
        except Exception as e:
            logger.warning(f"Failed to save hash cache: {e}")

    def _compute_hash(self, filepath: Path) -> str:
        """Compute content hash of file."""
        try:
            content = filepath.read_bytes()
            return hashlib.md5(content).hexdigest()
        except (OSError, IOError) as e:
            logger.debug(f"Could not compute hash for {filepath}: {e}")
            return ""

    def is_modified(self, filepath: str) -> bool:
        """Check if file has been modified since last index."""
        path = Path(filepath)
        if not path.exists():
            return False

        try:
            mtime = path.stat().st_mtime
        except OSError as e:
            logger.debug(f"Could not stat file {filepath}: {e}")
            return True

        # Check if we have cached info
        if filepath not in self._hashes:
            return True

        cached_hash, cached_mtime = self._hashes[filepath]

        # Quick check: mtime unchanged
        if mtime == cached_mtime:
            return False

        # Slow check: content hash
        current_hash = self._compute_hash(path)
        return current_hash != cached_hash

    def update(self, filepath: str) -> None:
        """Update cache for a file."""
        path = Path(filepath)
        if not path.exists():
            self._hashes.pop(filepath, None)
            return

        try:
            mtime = path.stat().st_mtime
            content_hash = self._compute_hash(path)
            self._hashes[filepath] = (content_hash, mtime)
        except OSError as e:
            logger.debug(f"Could not update cache for {filepath}: {e}")

    def update_batch(self, filepaths: List[str]) -> None:
        """Update cache for multiple files."""
        for fp in filepaths:
            self.update(fp)
        self._save()

    def remove(self, filepath: str) -> None:
        """Remove file from cache."""
        self._hashes.pop(filepath, None)

    def clear(self) -> None:
        """Clear all cached hashes."""
        self._hashes.clear()
        self._save()


class CodebaseIndexer:
    """
    High-level interface for codebase indexing and search.

    Orchestrates:
    - CodeChunker: Splits code into semantic chunks
    - SemanticEmbedder: Generates embeddings via Azure OpenAI
    - VectorStore: Stores and searches embeddings

    Usage:
        indexer = CodebaseIndexer()
        await indexer.index_codebase()  # Full index
        results = await indexer.search("error handling")  # Search
    """

    def __init__(
        self,
        config: Optional[IndexerConfig] = None,
        embedder: Optional[SemanticEmbedder] = None,
        store: Optional[VectorStore] = None,
        on_progress: Optional[Callable[[IndexingProgress], None]] = None,
    ):
        """
        Initialize the indexer.

        Args:
            config: Indexer configuration
            embedder: Pre-configured embedder (optional)
            store: Pre-configured vector store (optional)
            on_progress: Callback for progress updates
        """
        self.config = config or IndexerConfig()

        # Initialize components
        self._chunker = CodeChunker()
        self._embedder = embedder or get_embedder(self.config.embedding_config)
        self._store = store or get_vector_store(self.config.vector_config)

        # Progress tracking
        self._progress = IndexingProgress()
        self._on_progress = on_progress

        # File hash cache for incremental indexing
        cache_path = Path(self.config.index_dir) / "file_hashes.json"
        self._hash_cache = FileHashCache(str(cache_path))

        # Indexing state
        self._is_indexing = False
        self._cancel_requested = False

    @property
    def progress(self) -> IndexingProgress:
        """Get current indexing progress."""
        return self._progress

    @property
    def is_indexing(self) -> bool:
        """Check if indexing is in progress."""
        return self._is_indexing

    def _update_progress(self, **kwargs) -> None:
        """Update progress and notify callback."""
        for key, value in kwargs.items():
            if hasattr(self._progress, key):
                setattr(self._progress, key, value)

        if self._on_progress:
            try:
                self._on_progress(self._progress)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    async def index_codebase(
        self, full_reindex: bool = False, paths: Optional[List[str]] = None
    ) -> IndexingProgress:
        """
        Index the codebase.

        Args:
            full_reindex: If True, re-index all files regardless of modification
            paths: Specific paths to index (default: entire root_dir)

        Returns:
            Final IndexingProgress with statistics
        """
        if self._is_indexing:
            raise RuntimeError("Indexing already in progress")

        self._is_indexing = True
        self._cancel_requested = False
        self._progress = IndexingProgress(start_time=time.time())

        try:
            # Phase 1: Scan files
            self._update_progress(status=IndexerStatus.SCANNING)
            files = self._scan_files(paths)
            self._update_progress(total_files=len(files))

            if not files:
                logger.info("No files to index")
                return self._progress

            # Phase 2: Filter modified files (unless full reindex)
            if not full_reindex and self.config.check_modified:
                files = [f for f in files if self._hash_cache.is_modified(f)]
                self._update_progress(
                    total_files=len(files), skipped_files=self._progress.total_files - len(files)
                )

            if not files:
                logger.info("All files up to date")
                self._update_progress(status=IndexerStatus.IDLE)
                return self._progress

            logger.info(f"Indexing {len(files)} files...")

            # Phase 3: Process in batches
            batch_size = self.config.batch_size
            for i in range(0, len(files), batch_size):
                if self._cancel_requested:
                    break

                batch = files[i : i + batch_size]
                await self._process_batch(batch)

            # Update hash cache
            self._hash_cache.update_batch(files)

            self._update_progress(status=IndexerStatus.IDLE)
            logger.info(
                f"Indexing complete: {self._progress.indexed_chunks} chunks "
                f"from {self._progress.processed_files} files"
            )

        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            self._update_progress(
                status=IndexerStatus.ERROR, errors=self._progress.errors + [str(e)]
            )
            raise

        finally:
            self._is_indexing = False

        return self._progress

    def cancel(self) -> None:
        """Request cancellation of ongoing indexing."""
        self._cancel_requested = True

    def _scan_files(self, paths: Optional[List[str]] = None) -> List[str]:
        """Scan for indexable files."""
        root = Path(self.config.root_dir)
        files = []

        # Use provided paths or scan root
        if paths:
            for p in paths:
                path = Path(p)
                if path.is_file():
                    files.append(str(path))
                elif path.is_dir():
                    files.extend(self._scan_directory(path))
        else:
            files = self._scan_directory(root)

        return files

    def _scan_directory(self, directory: Path) -> List[str]:
        """Recursively scan directory for indexable files."""
        files = []

        for path in directory.rglob("*"):
            if not path.is_file():
                continue

            # Check extension
            if path.suffix not in self.config.extensions:
                continue

            # Check excludes
            str_path = str(path)
            if any(excl in str_path for excl in self.config.exclude_patterns):
                continue

            # Check file size
            try:
                size_kb = path.stat().st_size / 1024
                if size_kb > self.config.max_file_size_kb:
                    continue
            except OSError as e:
                logger.debug(f"Could not stat file {path}: {e}")
                continue

            files.append(str_path)

        return files

    async def _process_batch(self, files: List[str]) -> None:
        """Process a batch of files."""
        all_chunks: List[CodeChunk] = []

        # Phase: Chunking
        self._update_progress(status=IndexerStatus.CHUNKING)

        for filepath in files:
            if self._cancel_requested:
                return

            self._update_progress(current_file=filepath)

            try:
                # Delete existing chunks for this file
                self._store.delete_file(filepath)

                # Chunk the file
                chunks = self._chunker.chunk_file(filepath)
                all_chunks.extend(chunks)

                self._update_progress(
                    processed_files=self._progress.processed_files + 1,
                    total_chunks=self._progress.total_chunks + len(chunks),
                )

            except Exception as e:
                logger.warning(f"Failed to chunk {filepath}: {e}")
                self._update_progress(
                    error_count=self._progress.error_count + 1,
                    errors=self._progress.errors + [f"{filepath}: {e}"],
                )

        if not all_chunks:
            return

        # Phase: Embedding
        self._update_progress(status=IndexerStatus.EMBEDDING)

        try:
            results = await self._embedder.embed_chunks(all_chunks, show_progress=False)
            embeddings = [r.embedding for r in results]

        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            self._update_progress(
                error_count=self._progress.error_count + 1,
                errors=self._progress.errors + [f"Embedding: {e}"],
            )
            return

        # Phase: Storing
        self._update_progress(status=IndexerStatus.STORING)

        try:
            stored = self._store.add_chunks(all_chunks, embeddings)
            self._update_progress(indexed_chunks=self._progress.indexed_chunks + stored)

        except Exception as e:
            logger.error(f"Storage failed: {e}")
            self._update_progress(
                error_count=self._progress.error_count + 1,
                errors=self._progress.errors + [f"Storage: {e}"],
            )

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filepath_filter: Optional[str] = None,
        language_filter: Optional[str] = None,
        min_score: float = 0.5,
    ) -> List[SearchResult]:
        """
        Search the indexed codebase.

        Args:
            query: Natural language search query
            top_k: Number of results to return
            filepath_filter: Filter by filepath pattern
            language_filter: Filter by programming language
            min_score: Minimum similarity score

        Returns:
            List of SearchResult objects
        """
        # Embed query
        query_embedding = await self._embedder.embed_query(query)

        # Search vector store
        results = self._store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filepath_filter=filepath_filter,
            language_filter=language_filter,
            min_score=min_score,
        )

        return results

    async def index_file(self, filepath: str) -> int:
        """
        Index or re-index a single file.

        Args:
            filepath: Path to file

        Returns:
            Number of chunks indexed
        """
        if not Path(filepath).exists():
            return 0

        # Delete existing chunks
        self._store.delete_file(filepath)

        # Chunk file
        chunks = self._chunker.chunk_file(filepath)
        if not chunks:
            return 0

        # Embed chunks
        results = await self._embedder.embed_chunks(chunks)
        embeddings = [r.embedding for r in results]

        # Store
        stored = self._store.add_chunks(chunks, embeddings)

        # Update hash cache
        self._hash_cache.update(filepath)

        return stored

    def delete_file(self, filepath: str) -> int:
        """Remove a file from the index."""
        deleted = self._store.delete_file(filepath)
        self._hash_cache.remove(filepath)
        return deleted

    def get_stats(self) -> Dict[str, Any]:
        """Get indexer statistics."""
        return {
            "indexed_chunks": self._store.count(),
            "embedder": self._embedder.get_stats(),
            "store": self._store.get_stats(),
            "config": {
                "root_dir": self.config.root_dir,
                "extensions": self.config.extensions,
            },
        }

    def clear(self) -> None:
        """Clear all indexed data."""
        self._store.clear()
        self._hash_cache.clear()
        self._embedder.clear_cache()


# Singleton instance
_indexer: Optional[CodebaseIndexer] = None


def get_indexer(config: Optional[IndexerConfig] = None) -> CodebaseIndexer:
    """Get or create singleton indexer instance."""
    global _indexer
    if _indexer is None or config is not None:
        _indexer = CodebaseIndexer(config)
    return _indexer


__all__ = [
    "IndexerStatus",
    "IndexerConfig",
    "IndexingProgress",
    "CodebaseIndexer",
    "get_indexer",
]
