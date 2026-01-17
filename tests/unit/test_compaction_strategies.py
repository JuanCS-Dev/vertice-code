"""
Tests for Compaction Strategies - Sprint 2 Refactoring.

Tests cover:
    - Strategy instantiation and basic functionality
"""


from vertice_core.agents.compaction.strategies import (
    ObservationMaskingStrategy,
    HierarchicalStrategy,
    LLMSummaryStrategy,
)


class TestObservationMaskingStrategy:
    """Test ObservationMaskingStrategy."""

    def test_strategy_creation(self) -> None:
        """Test strategy instantiation."""
        strategy = ObservationMaskingStrategy()
        assert hasattr(strategy, "compact")
        assert callable(strategy.compact)


class TestHierarchicalStrategy:
    """Test HierarchicalStrategy."""

    def test_strategy_creation(self) -> None:
        """Test strategy instantiation."""
        strategy = HierarchicalStrategy()
        assert hasattr(strategy, "compact")
        assert callable(strategy.compact)


class TestLLMSummaryStrategy:
    """Test LLMSummaryStrategy."""

    def test_strategy_creation(self) -> None:
        """Test strategy instantiation."""
        strategy = LLMSummaryStrategy()
        assert hasattr(strategy, "compact")
        assert callable(strategy.compact)
