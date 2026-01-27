"""
Tests for NEXUS type definitions.
"""

import pytest
from datetime import datetime, timezone

import sys
from pathlib import Path

_gateway_path = Path(__file__).resolve().parents[2] / "apps" / "agent-gateway"
sys.path.insert(0, str(_gateway_path))
sys.path.insert(0, str(_gateway_path / "app"))

from nexus.types import (
    MemoryLevel,
    HealingAction,
    InsightCategory,
    SystemState,
    MetacognitiveInsight,
    EvolutionaryCandidate,
    MemoryBlock,
    HealingRecord,
    NexusStatus,
)


class TestMemoryLevel:
    """Tests for MemoryLevel enum."""

    def test_all_levels(self):
        """Test all memory levels exist."""
        assert MemoryLevel.L1_WORKING.value == "L1_WORKING"
        assert MemoryLevel.L2_EPISODIC.value == "L2_EPISODIC"
        assert MemoryLevel.L3_SEMANTIC.value == "L3_SEMANTIC"
        assert MemoryLevel.L4_PROCEDURAL.value == "L4_PROCEDURAL"

    def test_level_from_string(self):
        """Test creating level from string."""
        level = MemoryLevel("L2_EPISODIC")
        assert level == MemoryLevel.L2_EPISODIC


class TestHealingAction:
    """Tests for HealingAction enum."""

    def test_all_actions(self):
        """Test all healing actions exist."""
        actions = [
            HealingAction.RESTART_AGENT,
            HealingAction.ROLLBACK_CODE,
            HealingAction.SCALE_RESOURCES,
            HealingAction.CLEAR_CACHE,
            HealingAction.RESET_STATE,
            HealingAction.PATCH_CODE,
            HealingAction.NOTIFY_OPERATOR,
        ]
        assert len(actions) == 7


class TestSystemState:
    """Tests for SystemState dataclass."""

    def test_default_state(self):
        """Test default system state."""
        state = SystemState()

        assert state.agent_health == {}
        assert state.active_tasks == []
        assert state.recent_failures == []
        assert state.evolutionary_generation == 0
        assert state.total_healings == 0
        assert state.total_optimizations == 0

    def test_to_dict(self):
        """Test serialization to dict."""
        state = SystemState(evolutionary_generation=5)
        d = state.to_dict()

        assert d["evolutionary_generation"] == 5
        assert "last_reflection" in d

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "agent_health": {"coder": 0.95},
            "active_tasks": ["task1"],
            "recent_failures": [],
            "optimization_history": [],
            "skill_performance": {},
            "last_reflection": "2026-01-27T10:00:00+00:00",
            "evolutionary_generation": 10,
            "total_healings": 5,
            "total_optimizations": 3,
            "total_insights": 20,
        }
        state = SystemState.from_dict(data)

        assert state.evolutionary_generation == 10
        assert state.agent_health["coder"] == 0.95


class TestMetacognitiveInsight:
    """Tests for MetacognitiveInsight dataclass."""

    def test_default_insight(self):
        """Test default insight creation."""
        insight = MetacognitiveInsight()

        assert insight.insight_id.startswith("insight_")
        assert insight.confidence == 0.0
        assert insight.category == InsightCategory.PERFORMANCE
        assert insight.applied is False

    def test_insight_with_values(self):
        """Test insight with custom values."""
        insight = MetacognitiveInsight(
            observation="High error rate detected",
            causal_analysis="Memory leak in processing loop",
            learning="Need better resource management",
            action="Implement automatic cleanup",
            confidence=0.85,
            category=InsightCategory.ERROR_PATTERN,
        )

        assert insight.confidence == 0.85
        assert insight.category == InsightCategory.ERROR_PATTERN

    def test_insight_serialization(self):
        """Test insight serialization round-trip."""
        insight = MetacognitiveInsight(
            observation="Test observation",
            confidence=0.9,
        )

        d = insight.to_dict()
        restored = MetacognitiveInsight.from_dict(d)

        assert restored.observation == insight.observation
        assert restored.confidence == insight.confidence


class TestEvolutionaryCandidate:
    """Tests for EvolutionaryCandidate dataclass."""

    def test_default_candidate(self):
        """Test default candidate creation."""
        candidate = EvolutionaryCandidate()

        assert candidate.candidate_id.startswith("cand_")
        assert candidate.code == ""
        assert candidate.generation == 0
        assert candidate.aggregate_fitness == 0.0

    def test_candidate_with_fitness(self):
        """Test candidate with fitness scores."""
        candidate = EvolutionaryCandidate(
            code="def optimize(): pass",
            fitness_scores={"correctness": 0.9, "performance": 0.8, "aggregate": 0.85},
        )

        assert candidate.aggregate_fitness == 0.85

    def test_candidate_serialization(self):
        """Test candidate serialization round-trip."""
        candidate = EvolutionaryCandidate(
            code="print('hello')",
            generation=5,
        )

        d = candidate.to_dict()
        restored = EvolutionaryCandidate.from_dict(d)

        assert restored.code == candidate.code
        assert restored.generation == candidate.generation


class TestMemoryBlock:
    """Tests for MemoryBlock dataclass."""

    def test_default_block(self):
        """Test default memory block."""
        block = MemoryBlock()

        assert block.block_id.startswith("mem_")
        assert block.level == MemoryLevel.L1_WORKING
        assert block.importance == 0.5

    def test_block_serialization(self):
        """Test memory block serialization."""
        block = MemoryBlock(
            content="Test memory content",
            level=MemoryLevel.L3_SEMANTIC,
            importance=0.8,
        )

        d = block.to_dict()

        assert d["level"] == "L3_SEMANTIC"
        assert d["importance"] == 0.8


class TestHealingRecord:
    """Tests for HealingRecord dataclass."""

    def test_default_record(self):
        """Test default healing record."""
        record = HealingRecord()

        assert record.record_id.startswith("heal_")
        assert record.action == HealingAction.NOTIFY_OPERATOR
        assert record.success is False

    def test_record_serialization(self):
        """Test healing record serialization."""
        record = HealingRecord(
            anomaly_type="high_error_rate",
            anomaly_severity=0.8,
            action=HealingAction.RESTART_AGENT,
            success=True,
        )

        d = record.to_dict()

        assert d["action"] == "restart_agent"
        assert d["success"] is True
