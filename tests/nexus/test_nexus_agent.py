"""
Tests for NEXUS Meta-Agent.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import sys
from pathlib import Path

_gateway_path = Path(__file__).resolve().parents[2] / "apps" / "agent-gateway"
sys.path.insert(0, str(_gateway_path))
sys.path.insert(0, str(_gateway_path / "app"))

from nexus.config import NexusConfig
from nexus.types import MemoryLevel, MetacognitiveInsight, InsightCategory
from nexus.agent import NexusMetaAgent, get_nexus


@pytest.fixture
def config():
    """Create test configuration."""
    return NexusConfig(
        project_id="test-project",
        reflection_interval_seconds=10,
        health_check_interval_seconds=5,
    )


@pytest.fixture
def nexus(config):
    """Create NEXUS agent for testing."""
    with patch("nexus.memory.FIRESTORE_AVAILABLE", False):
        with patch("nexus.metacognitive.GENAI_AVAILABLE", False):
            with patch("nexus.healing.GENAI_AVAILABLE", False):
                with patch("nexus.evolution.GENAI_AVAILABLE", False):
                    return NexusMetaAgent(config)


class TestNexusMetaAgent:
    """Tests for NexusMetaAgent class."""

    def test_initialization(self, nexus):
        """Test agent initialization."""
        assert nexus.config.model == "gemini-3-pro-preview"
        assert nexus.config.default_thinking_level == "HIGH"
        assert nexus._active is False

    def test_components_initialized(self, nexus):
        """Test all components are initialized."""
        assert nexus.memory is not None
        assert nexus.metacognitive is not None
        assert nexus.healing is not None
        assert nexus.evolution is not None
        assert nexus.state is not None

    @pytest.mark.asyncio
    async def test_get_status(self, nexus):
        """Test getting status."""
        status = await nexus.get_status()

        assert status.active is False
        assert status.model == "gemini-3-pro-preview"
        assert status.thinking_level == "HIGH"

    @pytest.mark.asyncio
    async def test_reflect(self, nexus):
        """Test metacognitive reflection."""
        task = {"id": "task_1", "type": "code_generation"}
        outcome = {"success": True, "output": "Generated code"}

        insight = await nexus.reflect(task, outcome)

        assert isinstance(insight, MetacognitiveInsight)
        assert insight.insight_id.startswith("insight_")

    @pytest.mark.asyncio
    async def test_store_memory(self, nexus):
        """Test storing memory through agent."""
        result = await nexus.store_memory(
            content="Test memory content",
            level="L2_EPISODIC",
            importance=0.7,
        )

        assert "block_id" in result
        assert result["level"] == "L2_EPISODIC"

    @pytest.mark.asyncio
    async def test_retrieve_memories(self, nexus):
        """Test retrieving memories through agent."""
        await nexus.store_memory("Memory 1", "L2_EPISODIC", 0.5)
        await nexus.store_memory("Memory 2", "L2_EPISODIC", 0.8)

        memories = await nexus.retrieve_memories("L2_EPISODIC", limit=10)

        assert len(memories) == 2

    @pytest.mark.asyncio
    async def test_build_context(self, nexus):
        """Test building context from memories."""
        await nexus.store_memory("Working context", "L1_WORKING", 0.9)

        context = await nexus.build_context(max_tokens=10000)

        assert isinstance(context, str)

    @pytest.mark.asyncio
    async def test_get_comprehensive_stats(self, nexus):
        """Test getting comprehensive statistics."""
        stats = await nexus.get_comprehensive_stats()

        assert "nexus" in stats
        assert "system_state" in stats
        assert "memory" in stats
        assert "metacognitive" in stats
        assert "healing" in stats
        assert "evolution" in stats


class TestNexusSingleton:
    """Tests for NEXUS singleton pattern."""

    def test_get_nexus_returns_same_instance(self):
        """Test singleton returns same instance."""
        with patch("nexus.agent._nexus_instance", None):
            with patch("nexus.memory.FIRESTORE_AVAILABLE", False):
                with patch("nexus.metacognitive.GENAI_AVAILABLE", False):
                    with patch("nexus.healing.GENAI_AVAILABLE", False):
                        with patch("nexus.evolution.GENAI_AVAILABLE", False):
                            nexus1 = get_nexus()
                            nexus2 = get_nexus()

                            assert nexus1 is nexus2
