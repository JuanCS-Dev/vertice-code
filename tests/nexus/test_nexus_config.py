"""
Tests for NEXUS configuration.
"""

import os
import pytest

import sys
from pathlib import Path

_gateway_path = Path(__file__).resolve().parents[2] / "apps" / "agent-gateway"
sys.path.insert(0, str(_gateway_path))
sys.path.insert(0, str(_gateway_path / "app"))

from nexus.config import NexusConfig


class TestNexusConfig:
    """Tests for NexusConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = NexusConfig()

        assert config.model == "gemini-3-pro-preview"
        assert config.flash_model == "gemini-3-flash-preview"
        assert config.default_thinking_level == "HIGH"
        assert config.context_window == 1_048_576
        assert config.max_output_tokens == 65_536
        assert config.temperature == 1.0

    def test_evolutionary_defaults(self):
        """Test evolutionary algorithm defaults."""
        config = NexusConfig()

        assert config.evolutionary_population == 50
        assert config.island_count == 5
        assert config.mutation_rate == 0.15
        assert config.crossover_rate == 0.8
        assert config.elite_ratio == 0.1

    def test_memory_limits(self):
        """Test memory hierarchy limits."""
        config = NexusConfig()

        assert config.l1_working_memory_tokens == 131_072  # 128K
        assert config.l2_episodic_memory_tokens == 524_288  # 512K
        assert config.l3_semantic_memory_tokens == 262_144  # 256K
        assert config.l4_procedural_memory_tokens == 131_072  # 128K

        # Total should be within 1M context window
        total = (
            config.l1_working_memory_tokens
            + config.l2_episodic_memory_tokens
            + config.l3_semantic_memory_tokens
            + config.l4_procedural_memory_tokens
        )
        assert total <= config.context_window

    def test_from_env(self, monkeypatch):
        """Test configuration from environment variables."""
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
        monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-east1")
        monkeypatch.setenv("NEXUS_GEMINI_MODEL", "gemini-3-pro-preview")
        monkeypatch.setenv("NEXUS_THINKING_LEVEL", "LOW")

        config = NexusConfig.from_env()

        assert config.project_id == "test-project"
        assert config.location == "us-east1"
        assert config.model == "gemini-3-pro-preview"
        assert config.default_thinking_level == "LOW"

    def test_firestore_collections(self):
        """Test Firestore collection names."""
        config = NexusConfig()

        assert config.firestore_insights_collection == "nexus_metacognitive_insights"
        assert config.firestore_memory_collection == "nexus_hierarchical_memory"
        assert config.firestore_evolution_collection == "nexus_evolutionary_populations"
        assert config.firestore_healing_collection == "nexus_healing_actions"
