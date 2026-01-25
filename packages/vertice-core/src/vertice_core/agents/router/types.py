"""
Router Types - Data structures for semantic routing.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Tuple


class AgentType(str, Enum):
    """Available agent types for routing."""

    PLANNER = "planner"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
    ARCHITECT = "architect"
    EXPLORER = "explorer"
    REFACTOR = "refactor"
    SECURITY = "security"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEVOPS = "devops"
    PERFORMANCE = "performance"
    DATA = "data"
    CHAT = "chat"  # Default conversational


class TaskComplexity(str, Enum):
    """Task complexity levels."""

    SIMPLE = "simple"  # Single step, clear intent
    MODERATE = "moderate"  # Multi-step, some planning needed
    COMPLEX = "complex"  # Complex, requires analysis and decomposition
    EXPERT = "expert"  # Highly specialized domain knowledge required


@dataclass
class RouteDefinition:
    """Definition of a routing target."""

    name: str
    agent_type: AgentType
    description: str
    keywords: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    complexity: TaskComplexity = TaskComplexity.MODERATE
    confidence_threshold: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "agent_type": self.agent_type.value,
            "description": self.description,
            "keywords": self.keywords,
            "examples": self.examples,
            "complexity": self.complexity.value,
            "confidence_threshold": self.confidence_threshold,
            "metadata": self.metadata,
        }


@dataclass
class RoutingDecision:
    """Decision made by the router."""

    route_name: str
    agent_type: AgentType
    confidence: float
    reasoning: str
    alternatives: List[Tuple[str, float]] = field(default_factory=list)
    complexity: TaskComplexity = TaskComplexity.MODERATE
    fallback_used: bool = False
    processing_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_confident(self) -> bool:
        """Check if decision has high confidence."""
        return self.confidence >= 0.8

    @property
    def needs_fallback(self) -> bool:
        """Check if fallback routing is needed."""
        return self.confidence < 0.6
