"""
Tests for NEXUS Hierarchical Memory System.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import sys
from pathlib import Path

_gateway_path = Path(__file__).resolve().parents[2] / "apps" / "agent-gateway"
sys.path.insert(0, str(_gateway_path))
sys.path.insert(0, str(_gateway_path / "app"))

from nexus.config import NexusConfig
from nexus.types import MemoryLevel, MemoryBlock
from nexus.memory import HierarchicalMemory


@pytest.fixture
def config():
    """Create test configuration."""
    return NexusConfig(
        project_id="test-project",
        l1_working_memory_tokens=1000,
        l2_episodic_memory_tokens=2000,
        l3_semantic_memory_tokens=1500,
        l4_procedural_memory_tokens=500,
    )


@pytest.fixture
def memory(config):
    """Create memory system for testing."""
    with patch("nexus.memory.FIRESTORE_AVAILABLE", False):
        return HierarchicalMemory(config)


class TestHierarchicalMemory:
    """Tests for HierarchicalMemory class."""

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, memory):
        """Test basic store and retrieve."""
        block = await memory.store(
            content="Test content for memory",
            level=MemoryLevel.L2_EPISODIC,
            importance=0.7,
        )

        assert block.content == "Test content for memory"
        assert block.level == MemoryLevel.L2_EPISODIC
        assert block.importance == 0.7

        retrieved = await memory.retrieve(MemoryLevel.L2_EPISODIC, limit=10)
        assert len(retrieved) == 1
        assert retrieved[0].block_id == block.block_id

    @pytest.mark.asyncio
    async def test_token_estimation(self, memory):
        """Test token count estimation."""
        content = "a" * 400  # ~100 tokens
        block = await memory.store(
            content=content,
            level=MemoryLevel.L1_WORKING,
        )

        assert block.token_count == 100

    @pytest.mark.asyncio
    async def test_eviction_on_capacity(self, memory):
        """Test that old blocks are evicted when capacity exceeded."""
        # Fill L1 with blocks
        for i in range(10):
            await memory.store(
                content="x" * 400,  # 100 tokens each
                level=MemoryLevel.L1_WORKING,
                importance=0.3,
            )

        # L1 limit is 1000 tokens, so should have ~10 blocks max
        # Adding more should trigger eviction
        await memory.store(
            content="y" * 800,  # 200 tokens - should trigger eviction
            level=MemoryLevel.L1_WORKING,
            importance=0.9,
        )

        current_tokens = memory._current_level_tokens(MemoryLevel.L1_WORKING)
        assert current_tokens <= memory._token_limits[MemoryLevel.L1_WORKING]

    @pytest.mark.asyncio
    async def test_retrieve_with_min_importance(self, memory):
        """Test filtering by minimum importance."""
        await memory.store(
            content="Low importance",
            level=MemoryLevel.L2_EPISODIC,
            importance=0.2,
        )
        await memory.store(
            content="High importance",
            level=MemoryLevel.L2_EPISODIC,
            importance=0.9,
        )

        high_only = await memory.retrieve(
            MemoryLevel.L2_EPISODIC,
            limit=10,
            min_importance=0.5,
        )

        assert len(high_only) == 1
        assert high_only[0].importance == 0.9

    @pytest.mark.asyncio
    async def test_retrieve_all_levels(self, memory):
        """Test retrieving from all memory levels."""
        await memory.store("Working", MemoryLevel.L1_WORKING)
        await memory.store("Episodic", MemoryLevel.L2_EPISODIC)
        await memory.store("Semantic", MemoryLevel.L3_SEMANTIC)
        await memory.store("Procedural", MemoryLevel.L4_PROCEDURAL)

        all_memories = await memory.retrieve_all_levels()

        assert len(all_memories[MemoryLevel.L1_WORKING]) == 1
        assert len(all_memories[MemoryLevel.L2_EPISODIC]) == 1
        assert len(all_memories[MemoryLevel.L3_SEMANTIC]) == 1
        assert len(all_memories[MemoryLevel.L4_PROCEDURAL]) == 1

    @pytest.mark.asyncio
    async def test_promote_to_semantic(self, memory):
        """Test promoting episodic memories to semantic."""
        episodic_blocks = [
            await memory.store("Experience 1", MemoryLevel.L2_EPISODIC),
            await memory.store("Experience 2", MemoryLevel.L2_EPISODIC),
        ]

        semantic_block = await memory.promote_to_semantic(
            episodic_blocks=episodic_blocks,
            abstraction="Pattern: Experiences lead to learning",
            importance=0.8,
        )

        assert semantic_block.level == MemoryLevel.L3_SEMANTIC
        assert "source_blocks" in semantic_block.metadata

    @pytest.mark.asyncio
    async def test_store_procedure(self, memory):
        """Test storing learned procedures."""
        block = await memory.store_procedure(
            procedure_name="debug_error",
            steps=["Read error", "Check logs", "Fix code", "Test"],
            success_rate=0.95,
        )

        assert block.level == MemoryLevel.L4_PROCEDURAL
        assert "PROCEDURE: debug_error" in block.content
        assert block.importance == 0.95

    @pytest.mark.asyncio
    async def test_build_context_prompt(self, memory):
        """Test building context prompt from memories."""
        await memory.store("Current task", MemoryLevel.L1_WORKING, importance=0.9)
        await memory.store("Recent experience", MemoryLevel.L2_EPISODIC, importance=0.7)
        await memory.store("Learned pattern", MemoryLevel.L3_SEMANTIC, importance=0.8)

        all_memories = await memory.retrieve_all_levels()
        context = memory.build_context_prompt(all_memories, max_tokens=10000)

        assert "WORKING CONTEXT" in context
        assert "RECENT EXPERIENCES" in context
        assert "LEARNED PATTERNS" in context

    @pytest.mark.asyncio
    async def test_get_stats(self, memory):
        """Test getting memory statistics."""
        await memory.store("Test 1", MemoryLevel.L1_WORKING)
        await memory.store("Test 2", MemoryLevel.L2_EPISODIC)

        stats = await memory.get_stats()

        assert stats["total_blocks"] == 2
        assert "by_level" in stats
        assert "L1_WORKING" in stats["by_level"]

    @pytest.mark.asyncio
    async def test_clear_level(self, memory):
        """Test clearing a memory level."""
        await memory.store("Block 1", MemoryLevel.L1_WORKING)
        await memory.store("Block 2", MemoryLevel.L1_WORKING)

        count = await memory.clear_level(MemoryLevel.L1_WORKING)

        assert count == 2
        retrieved = await memory.retrieve(MemoryLevel.L1_WORKING)
        assert len(retrieved) == 0
