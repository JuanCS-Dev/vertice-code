"""
NEXUS Type Definitions

Core data structures for the NEXUS Meta-Agent system.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class MemoryLevel(str, Enum):
    """Hierarchical memory levels (L1-L4)."""

    L1_WORKING = "L1_WORKING"  # 128K - Immediate context
    L2_EPISODIC = "L2_EPISODIC"  # 512K - Recent experiences
    L3_SEMANTIC = "L3_SEMANTIC"  # 256K - Extracted patterns
    L4_PROCEDURAL = "L4_PROCEDURAL"  # 128K - Learned procedures


class HealingAction(str, Enum):
    """Types of autonomous healing actions."""

    RESTART_AGENT = "restart_agent"
    ROLLBACK_CODE = "rollback_code"
    SCALE_RESOURCES = "scale_resources"
    CLEAR_CACHE = "clear_cache"
    RESET_STATE = "reset_state"
    PATCH_CODE = "patch_code"
    NOTIFY_OPERATOR = "notify_operator"


class InsightCategory(str, Enum):
    """Categories of metacognitive insights."""

    PERFORMANCE = "performance"
    ERROR_PATTERN = "error_pattern"
    OPTIMIZATION = "optimization"
    CAPABILITY_GAP = "capability_gap"
    ARCHITECTURAL = "architectural"
    BEHAVIORAL = "behavioral"


@dataclass
class SystemState:
    """Current state of the agent ecosystem."""

    agent_health: Dict[str, float] = field(default_factory=dict)
    active_tasks: List[str] = field(default_factory=list)
    recent_failures: List[Dict[str, Any]] = field(default_factory=list)
    optimization_history: List[Dict[str, Any]] = field(default_factory=list)
    skill_performance: Dict[str, float] = field(default_factory=dict)
    last_reflection: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evolutionary_generation: int = 0
    total_healings: int = 0
    total_optimizations: int = 0
    total_insights: int = 0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["last_reflection"] = self.last_reflection.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemState":
        if "last_reflection" in data and isinstance(data["last_reflection"], str):
            data["last_reflection"] = datetime.fromisoformat(data["last_reflection"])
        return cls(**data)


@dataclass
class MetacognitiveInsight:
    """Self-reflection insight from metacognitive analysis."""

    insight_id: str = field(default_factory=lambda: f"insight_{uuid.uuid4().hex[:12]}")
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    context: str = ""
    observation: str = ""
    causal_analysis: str = ""
    learning: str = ""
    action: str = ""
    confidence: float = 0.0
    category: InsightCategory = InsightCategory.PERFORMANCE
    applied: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        d["category"] = self.category.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetacognitiveInsight":
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if "category" in data and isinstance(data["category"], str):
            data["category"] = InsightCategory(data["category"])
        return cls(**data)


@dataclass
class EvolutionaryCandidate:
    """A candidate solution in evolutionary optimization."""

    candidate_id: str = field(default_factory=lambda: f"cand_{uuid.uuid4().hex[:12]}")
    code: str = ""
    prompt: str = ""
    ancestry: List[str] = field(default_factory=list)
    generation: int = 0
    island_id: int = 0
    fitness_scores: Dict[str, float] = field(default_factory=dict)
    evaluation_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def aggregate_fitness(self) -> float:
        return self.fitness_scores.get("aggregate", 0.0)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["created_at"] = self.created_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvolutionaryCandidate":
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class MemoryBlock:
    """A block of hierarchical memory."""

    block_id: str = field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:12]}")
    level: MemoryLevel = MemoryLevel.L1_WORKING
    content: str = ""
    token_count: int = 0
    importance: float = 0.5
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["level"] = self.level.value
        d["created_at"] = self.created_at.isoformat()
        d["last_accessed"] = self.last_accessed.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryBlock":
        if "level" in data and isinstance(data["level"], str):
            data["level"] = MemoryLevel(data["level"])
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "last_accessed" in data and isinstance(data["last_accessed"], str):
            data["last_accessed"] = datetime.fromisoformat(data["last_accessed"])
        return cls(**data)


@dataclass
class HealingRecord:
    """Record of a healing action."""

    record_id: str = field(default_factory=lambda: f"heal_{uuid.uuid4().hex[:12]}")
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    anomaly_type: str = ""
    anomaly_severity: float = 0.0
    diagnosis: str = ""
    action: HealingAction = HealingAction.NOTIFY_OPERATOR
    success: bool = False
    rollback_available: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        d["action"] = self.action.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HealingRecord":
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if "action" in data and isinstance(data["action"], str):
            data["action"] = HealingAction(data["action"])
        return cls(**data)


@dataclass
class NexusStatus:
    """Current status of the NEXUS Meta-Agent."""

    active: bool = False
    model: str = "gemini-3-pro-preview"
    thinking_level: str = "HIGH"
    system_state: Optional[SystemState] = None
    total_insights: int = 0
    total_healings: int = 0
    total_evolutions: int = 0
    memory_usage: Dict[str, int] = field(default_factory=dict)
    last_reflection: Optional[str] = None
    uptime_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.system_state:
            d["system_state"] = self.system_state.to_dict()
        return d
