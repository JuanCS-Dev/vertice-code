"""
Tests for ContextCompactor - Sprint 2 Refactoring.
"""

import pytest
from vertice_core.agents.compaction.compactor import ContextCompactor
from vertice_core.agents.compaction.types import CompactionConfig


class TestContextCompactor:
    """Test ContextCompactor class."""

    def test_compactor_creation(self) -> None:
        """Test ContextCompactor instantiation."""
        config = CompactionConfig()
        compactor = ContextCompactor(config)
        assert compactor.config == config
        assert hasattr(compactor, "compact")
        assert hasattr(compactor, "auto_compact")
