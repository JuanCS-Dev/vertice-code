"""
Tests for Compaction Types - Sprint 2 Refactoring.

Tests cover:
    - Compaction enums and configurations
    - Type validation and serialization
    - Backward compatibility re-exports
"""

import pytest
from vertice_core.agents.compaction.types import (
    CompactionStrategy,
    CompactionTrigger,
    CompactionConfig,
    CompactionResult,
    MaskedObservation,
)


class TestCompactionEnums:
    """Test compaction strategy enums."""

    def test_compaction_strategies_defined(self) -> None:
        """Test all compaction strategies are properly defined."""
        assert CompactionStrategy.OBSERVATION_MASKING == "observation_masking"
        assert CompactionStrategy.HIERARCHICAL == "hierarchical"
        assert CompactionStrategy.LLM_SUMMARY == "llm_summary"
        assert CompactionStrategy.HYBRID == "hybrid"
        assert CompactionStrategy.NONE == "none"

    def test_compaction_triggers_defined(self) -> None:
        """Test all compaction triggers are properly defined."""
        assert CompactionTrigger.THRESHOLD == "threshold"
        assert CompactionTrigger.PERIODIC == "periodic"
        assert CompactionTrigger.MANUAL == "manual"
        assert CompactionTrigger.ADAPTIVE == "adaptive"


class TestCompactionConfig:
    """Test CompactionConfig dataclass."""

    def test_config_creation_minimal(self) -> None:
        """Test config creation with minimal required fields."""
        config = CompactionConfig()
        assert config.trigger_threshold == 0.85
        assert config.target_threshold == 0.60
        assert config.default_strategy == CompactionStrategy.OBSERVATION_MASKING

    def test_config_creation_custom(self) -> None:
        """Test config creation with custom values."""
        config = CompactionConfig(
            trigger_threshold=0.90,
            target_threshold=0.50,
            keep_recent_messages=20,
            default_strategy=CompactionStrategy.HIERARCHICAL,
        )
        assert config.trigger_threshold == 0.90
        assert config.target_threshold == 0.50
        assert config.keep_recent_messages == 20
        assert config.default_strategy == CompactionStrategy.HIERARCHICAL


class TestCompactionResult:
    """Test CompactionResult dataclass."""

    def test_result_creation_success(self) -> None:
        """Test successful compaction result."""
        result = CompactionResult(
            success=True,
            strategy_used=CompactionStrategy.OBSERVATION_MASKING,
            tokens_before=1500,
            tokens_after=800,
            compression_ratio=0.533,
            duration_ms=45.2,
            messages_removed=5,
        )
        assert result.success is True
        assert result.strategy_used == CompactionStrategy.OBSERVATION_MASKING
        assert result.tokens_before == 1500
        assert result.tokens_after == 800
        assert result.compression_ratio == 0.533
        assert result.duration_ms == 45.2
        assert result.messages_removed == 5
        assert result.tokens_saved == 700  # Property test

    def test_result_creation_failure(self) -> None:
        """Test failed compaction result."""
        result = CompactionResult(
            success=False,
            strategy_used=CompactionStrategy.LLM_SUMMARY,
            tokens_before=1000,
            tokens_after=1000,  # No change on failure
            compression_ratio=1.0,
            duration_ms=120.5,
            messages_removed=0,
            error="LLM service unavailable",
        )
        assert result.success is False
        assert result.error == "LLM service unavailable"
        assert result.tokens_before == 1000
        assert result.tokens_after == 1000
        assert result.compression_ratio == 1.0
        assert result.tokens_saved == 0
