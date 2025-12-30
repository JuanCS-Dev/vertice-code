"""
Semantic Chunker

Intelligent document chunking for RAG.

References:
- arXiv:2404.03242 (RAG for LLMs Survey)
- arXiv:2404.16130 (KG²RAG)
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from .types import DocumentChunk, KnowledgeConfig

logger = logging.getLogger(__name__)


class SemanticChunker:
    """
    Semantic document chunker for RAG.

    Implements intelligent chunking strategies:
    - Sentence-aware boundaries
    - Semantic coherence (based on headings/sections)
    - Overlap for context continuity
    - Metadata preservation
    """

    # Sentence boundaries
    SENTENCE_ENDINGS = re.compile(r'[.!?]\s+')

    # Section markers
    SECTION_MARKERS = re.compile(r'^#{1,6}\s|^(?:def|class|function)\s|^\d+\.\s')

    def __init__(self, config: Optional[KnowledgeConfig] = None):
        """
        Initialize chunker.

        Args:
            config: Knowledge configuration
        """
        self._config = config or KnowledgeConfig()

    def chunk_document(
        self,
        content: str,
        document_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """
        Chunk a document into semantically coherent pieces.

        Args:
            content: Document content
            document_id: Document identifier
            metadata: Document metadata

        Returns:
            List of DocumentChunk objects
        """
        if self._config.use_semantic_chunking:
            return self._semantic_chunk(content, document_id, metadata or {})
        else:
            return self._fixed_chunk(content, document_id, metadata or {})

    def _semantic_chunk(
        self,
        content: str,
        document_id: str,
        metadata: Dict[str, Any],
    ) -> List[DocumentChunk]:
        """
        Chunk using semantic boundaries (sentences, paragraphs, sections).

        Respects natural document structure.
        """
        chunks = []
        chunk_size = self._config.chunk_size
        overlap = self._config.chunk_overlap

        # Split into paragraphs first
        paragraphs = self._split_paragraphs(content)

        current_chunk = ""
        current_start = 0
        chunk_index = 0

        for para in paragraphs:
            # Check if adding paragraph exceeds chunk size
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                # Create chunk from current content
                chunk = self._create_chunk(
                    content=current_chunk.strip(),
                    document_id=document_id,
                    metadata=metadata,
                    start_char=current_start,
                    end_char=current_start + len(current_chunk),
                    chunk_index=chunk_index,
                )
                chunks.append(chunk)
                chunk_index += 1

                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, overlap)
                current_start = current_start + len(current_chunk) - len(overlap_text)
                current_chunk = overlap_text

            current_chunk += para + "\n\n"

            # Check if paragraph itself is too large
            if len(para) > chunk_size:
                # Split large paragraph into sentences
                sentence_chunks = self._split_large_paragraph(
                    para,
                    document_id,
                    metadata,
                    current_start,
                    chunk_index,
                )
                chunks.extend(sentence_chunks)
                chunk_index += len(sentence_chunks)
                current_chunk = ""
                current_start += len(para)

        # Handle remaining content
        if current_chunk.strip():
            chunk = self._create_chunk(
                content=current_chunk.strip(),
                document_id=document_id,
                metadata=metadata,
                start_char=current_start,
                end_char=current_start + len(current_chunk),
                chunk_index=chunk_index,
            )
            chunks.append(chunk)

        logger.debug(
            f"[Chunker] Document {document_id}: {len(content)} chars -> {len(chunks)} chunks"
        )

        return chunks

    def _fixed_chunk(
        self,
        content: str,
        document_id: str,
        metadata: Dict[str, Any],
    ) -> List[DocumentChunk]:
        """
        Simple fixed-size chunking with overlap.

        Falls back when semantic chunking is disabled.
        """
        chunks = []
        chunk_size = self._config.chunk_size
        overlap = self._config.chunk_overlap

        start = 0
        chunk_index = 0

        while start < len(content):
            end = min(start + chunk_size, len(content))

            # Try to end at sentence boundary
            if end < len(content):
                # Look for sentence ending near the boundary
                search_start = max(end - 100, start)
                match = None
                for m in self.SENTENCE_ENDINGS.finditer(content[search_start:end]):
                    match = m

                if match:
                    end = search_start + match.end()

            chunk_content = content[start:end].strip()

            if chunk_content:
                chunk = self._create_chunk(
                    content=chunk_content,
                    document_id=document_id,
                    metadata=metadata,
                    start_char=start,
                    end_char=end,
                    chunk_index=chunk_index,
                )
                chunks.append(chunk)
                chunk_index += 1

            # Ensure we always advance to prevent infinite loop
            new_start = end - overlap
            if new_start <= start:
                new_start = end  # Skip overlap at document end
            start = new_start

        return chunks

    def _split_paragraphs(self, content: str) -> List[str]:
        """Split content into paragraphs."""
        # Split on double newlines
        paragraphs = re.split(r'\n\s*\n', content)
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_large_paragraph(
        self,
        paragraph: str,
        document_id: str,
        metadata: Dict[str, Any],
        start_offset: int,
        chunk_index: int,
    ) -> List[DocumentChunk]:
        """Split a large paragraph into sentence-based chunks."""
        chunks = []
        sentences = self.SENTENCE_ENDINGS.split(paragraph)
        chunk_size = self._config.chunk_size

        current_chunk = ""
        current_start = start_offset

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunk = self._create_chunk(
                    content=current_chunk.strip(),
                    document_id=document_id,
                    metadata=metadata,
                    start_char=current_start,
                    end_char=current_start + len(current_chunk),
                    chunk_index=chunk_index + len(chunks),
                )
                chunks.append(chunk)
                current_start += len(current_chunk)
                current_chunk = ""

            current_chunk += sentence + ". "

        if current_chunk.strip():
            chunk = self._create_chunk(
                content=current_chunk.strip(),
                document_id=document_id,
                metadata=metadata,
                start_char=current_start,
                end_char=current_start + len(current_chunk),
                chunk_index=chunk_index + len(chunks),
            )
            chunks.append(chunk)

        return chunks

    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """Get overlap text from end of chunk, respecting sentence boundaries."""
        if len(text) <= overlap_size:
            return text

        overlap_text = text[-overlap_size:]

        # Try to start at a sentence boundary
        match = self.SENTENCE_ENDINGS.search(overlap_text)
        if match:
            return overlap_text[match.end():]

        return overlap_text

    def _create_chunk(
        self,
        content: str,
        document_id: str,
        metadata: Dict[str, Any],
        start_char: int,
        end_char: int,
        chunk_index: int,
    ) -> DocumentChunk:
        """Create a DocumentChunk with metadata."""
        return DocumentChunk(
            document_id=document_id,
            content=content,
            metadata={
                **metadata,
                "chunk_index": chunk_index,
                "char_range": f"{start_char}-{end_char}",
            },
            start_char=start_char,
            end_char=end_char,
            chunk_index=chunk_index,
        )

    def rechunk_for_context(
        self,
        chunks: List[DocumentChunk],
        context_window: int = 3,
    ) -> List[DocumentChunk]:
        """
        Create expanded chunks with surrounding context.

        Useful for providing more context in retrieval.

        Args:
            chunks: Original chunks
            context_window: Number of chunks to include before/after

        Returns:
            Expanded chunks
        """
        expanded_chunks = []

        for i, chunk in enumerate(chunks):
            # Gather surrounding chunks
            start_idx = max(0, i - context_window)
            end_idx = min(len(chunks), i + context_window + 1)

            context_chunks = chunks[start_idx:end_idx]
            expanded_content = "\n\n".join(c.content for c in context_chunks)

            expanded_chunk = DocumentChunk(
                id=chunk.id,
                document_id=chunk.document_id,
                content=chunk.content,  # Original content
                expanded_context=expanded_content,  # With surrounding context
                metadata={
                    **chunk.metadata,
                    "context_range": f"{start_idx}-{end_idx}",
                },
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                chunk_index=chunk.chunk_index,
            )
            expanded_chunks.append(expanded_chunk)

        return expanded_chunks
