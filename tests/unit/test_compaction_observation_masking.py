"""
Tests for ObservationMaskingStrategy - Basic functionality tests.

Tests cover basic initialization and core functionality.
"""

import pytest
from vertice_core.agents.compaction.strategies.observation_masking import ObservationMaskingStrategy
from vertice_core.agents.compaction.types import CompactionConfig, CompactionResult
from vertice_core.agents.context.unified import UnifiedContext


class TestObservationMaskingStrategyBasic:
    """Test basic ObservationMaskingStrategy functionality."""

    def test_strategy_creation(self) -> None:
        """Test strategy instantiation."""
        strategy = ObservationMaskingStrategy()
        assert hasattr(strategy, "compact")
        assert hasattr(strategy, "EXTRACT_PATTERNS")
        assert callable(strategy.compact)

    def test_basic_compaction(self) -> None:
        """Test basic compaction functionality."""
        strategy = ObservationMaskingStrategy()
        ctx = UnifiedContext()
        config = CompactionConfig()

        # Add a message
        ctx.add_message("user", "Test message")

        result = strategy.compact(ctx, config)

        assert result.success is True
        assert isinstance(result, CompactionResult)

    def test_empty_context_compaction(self) -> None:
        """Test compaction of empty context."""
        strategy = ObservationMaskingStrategy()
        ctx = UnifiedContext()
        config = CompactionConfig()

        result = strategy.compact(ctx, config)

        assert result.success is True
        assert isinstance(result, CompactionResult)
