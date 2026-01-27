"""
NEXUS Hierarchical Memory System (L1-L4)

Implements the 1M token memory hierarchy for Gemini 3 Pro:
- L1: Working Memory (128K) - Immediate context
- L2: Episodic Memory (512K) - Recent experiences
- L3: Semantic Memory (256K) - Extracted patterns
- L4: Procedural Memory (128K) - Learned procedures

Persistence: Google Cloud Firestore
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from nexus.config import NexusConfig
from nexus.types import MemoryBlock, MemoryLevel

logger = logging.getLogger(__name__)

try:
    from google.cloud import firestore

    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False
    logger.warning("google-cloud-firestore not available, using in-memory storage")


class HierarchicalMemory:
    """
    Hierarchical Memory System for NEXUS Meta-Agent.

    Leverages Gemini 3 Pro's 1M token context window with intelligent
    memory management across 4 levels.
    """

    def __init__(self, config: NexusConfig):
        self.config = config
        self._local_memory: Dict[MemoryLevel, List[MemoryBlock]] = defaultdict(list)
        self._token_limits = {
            MemoryLevel.L1_WORKING: config.l1_working_memory_tokens,
            MemoryLevel.L2_EPISODIC: config.l2_episodic_memory_tokens,
            MemoryLevel.L3_SEMANTIC: config.l3_semantic_memory_tokens,
            MemoryLevel.L4_PROCEDURAL: config.l4_procedural_memory_tokens,
        }

        if FIRESTORE_AVAILABLE:
            try:
                self._db = firestore.AsyncClient(project=config.project_id)
                self._collection = self._db.collection(config.firestore_memory_collection)
            except Exception as e:
                logger.warning(f"Firestore init failed: {e}, using in-memory storage")
                self._db = None
                self._collection = None
        else:
            self._db = None
            self._collection = None

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough: ~4 chars per token)."""
        return len(text) // 4

    def _current_level_tokens(self, level: MemoryLevel) -> int:
        """Calculate current token usage for a memory level."""
        return sum(block.token_count for block in self._local_memory[level])

    async def store(
        self,
        content: str,
        level: MemoryLevel,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryBlock:
        """Store content in the specified memory level."""
        token_count = self._estimate_tokens(content)

        block = MemoryBlock(
            level=level,
            content=content,
            token_count=token_count,
            importance=importance,
            metadata=metadata or {},
        )

        # Evict if necessary
        await self._evict_if_needed(level, token_count)

        # Store locally
        self._local_memory[level].append(block)

        # Persist to Firestore
        if self._collection:
            try:
                await self._collection.document(block.block_id).set(block.to_dict())
            except Exception as e:
                logger.warning(f"Failed to persist memory block: {e}")

        logger.debug(
            f"Stored memory block {block.block_id} in {level.value} " f"({token_count} tokens)"
        )
        return block

    async def _evict_if_needed(self, level: MemoryLevel, new_tokens: int) -> None:
        """Evict old/low-importance blocks if capacity exceeded."""
        limit = self._token_limits[level]
        current = self._current_level_tokens(level)

        while current + new_tokens > limit and self._local_memory[level]:
            # Sort by importance (ascending) and age (oldest first)
            blocks = sorted(
                self._local_memory[level],
                key=lambda b: (b.importance, -b.access_count, b.created_at.timestamp()),
            )

            if not blocks:
                break

            # Evict lowest priority block
            evicted = blocks[0]
            self._local_memory[level].remove(evicted)
            current -= evicted.token_count

            # Remove from Firestore
            if self._collection:
                try:
                    await self._collection.document(evicted.block_id).delete()
                except Exception as e:
                    logger.warning(f"Failed to delete evicted block: {e}")

            logger.debug(f"Evicted memory block {evicted.block_id} from {level.value}")

    async def retrieve(
        self,
        level: MemoryLevel,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> List[MemoryBlock]:
        """Retrieve memory blocks from a specific level."""
        blocks = [b for b in self._local_memory[level] if b.importance >= min_importance]

        # Sort by importance and recency
        blocks.sort(
            key=lambda b: (b.importance, b.last_accessed.timestamp()),
            reverse=True,
        )

        # Update access metadata
        now = datetime.now(timezone.utc)
        for block in blocks[:limit]:
            block.last_accessed = now
            block.access_count += 1

        return blocks[:limit]

    async def retrieve_all_levels(
        self,
        query: Optional[str] = None,
        limit_per_level: int = 5,
    ) -> Dict[MemoryLevel, List[MemoryBlock]]:
        """Retrieve memory from all levels for context building."""
        result = {}

        for level in MemoryLevel:
            blocks = await self.retrieve(level, limit=limit_per_level)
            if query:
                # Simple relevance filtering
                query_lower = query.lower()
                blocks = [b for b in blocks if query_lower in b.content.lower()]
            result[level] = blocks

        return result

    async def promote_to_semantic(
        self,
        episodic_blocks: List[MemoryBlock],
        abstraction: str,
        importance: float = 0.7,
    ) -> MemoryBlock:
        """Promote episodic memories to semantic memory via abstraction."""
        metadata = {
            "source_blocks": [b.block_id for b in episodic_blocks],
            "abstraction_type": "pattern_extraction",
        }

        return await self.store(
            content=abstraction,
            level=MemoryLevel.L3_SEMANTIC,
            importance=importance,
            metadata=metadata,
        )

    async def store_procedure(
        self,
        procedure_name: str,
        steps: List[str],
        success_rate: float = 1.0,
    ) -> MemoryBlock:
        """Store a learned procedure in L4 procedural memory."""
        content = f"PROCEDURE: {procedure_name}\n" + "\n".join(
            f"  {i+1}. {step}" for i, step in enumerate(steps)
        )

        return await self.store(
            content=content,
            level=MemoryLevel.L4_PROCEDURAL,
            importance=success_rate,
            metadata={
                "procedure_name": procedure_name,
                "step_count": len(steps),
                "success_rate": success_rate,
            },
        )

    def build_context_prompt(
        self,
        memories: Dict[MemoryLevel, List[MemoryBlock]],
        max_tokens: int = 100_000,
    ) -> str:
        """Build a context prompt from hierarchical memories."""
        sections = []
        total_tokens = 0

        level_labels = {
            MemoryLevel.L1_WORKING: "WORKING CONTEXT",
            MemoryLevel.L2_EPISODIC: "RECENT EXPERIENCES",
            MemoryLevel.L3_SEMANTIC: "LEARNED PATTERNS",
            MemoryLevel.L4_PROCEDURAL: "KNOWN PROCEDURES",
        }

        for level in MemoryLevel:
            blocks = memories.get(level, [])
            if not blocks:
                continue

            section_content = []
            for block in blocks:
                if total_tokens + block.token_count > max_tokens:
                    break
                section_content.append(block.content)
                total_tokens += block.token_count

            if section_content:
                sections.append(
                    f"=== {level_labels[level]} ===\n" + "\n---\n".join(section_content)
                )

        return "\n\n".join(sections)

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        stats = {
            "total_blocks": 0,
            "total_tokens": 0,
            "by_level": {},
        }

        for level in MemoryLevel:
            blocks = self._local_memory[level]
            tokens = self._current_level_tokens(level)
            limit = self._token_limits[level]

            stats["by_level"][level.value] = {
                "blocks": len(blocks),
                "tokens": tokens,
                "limit": limit,
                "usage_pct": round(tokens / limit * 100, 1) if limit > 0 else 0,
            }
            stats["total_blocks"] += len(blocks)
            stats["total_tokens"] += tokens

        return stats

    async def load_from_firestore(self) -> int:
        """Load memory blocks from Firestore on startup."""
        if not self._collection:
            return 0

        loaded = 0
        try:
            docs = self._collection.stream()
            async for doc in docs:
                data = doc.to_dict()
                block = MemoryBlock.from_dict(data)
                self._local_memory[block.level].append(block)
                loaded += 1
        except Exception as e:
            logger.warning(f"Failed to load from Firestore: {e}")

        logger.info(f"Loaded {loaded} memory blocks from Firestore")
        return loaded

    async def clear_level(self, level: MemoryLevel) -> int:
        """Clear all memory blocks from a specific level."""
        count = len(self._local_memory[level])
        block_ids = [b.block_id for b in self._local_memory[level]]

        self._local_memory[level].clear()

        if self._collection:
            for block_id in block_ids:
                try:
                    await self._collection.document(block_id).delete()
                except Exception as e:
                    logger.warning(f"Failed to delete block {block_id}: {e}")

        logger.info(f"Cleared {count} blocks from {level.value}")
        return count
