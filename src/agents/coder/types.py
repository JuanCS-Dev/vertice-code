"""
Coder Agent Types

Dataclasses and types for the Coder Agent.
Includes Darwin Gödel Machine types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class CodeGenerationRequest:
    """Request for code generation."""

    description: str
    language: str = "python"
    style: str = "clean"  # clean, verbose, minimal
    include_tests: bool = False
    include_docs: bool = True


@dataclass
class EvaluationResult:
    """Result of code self-evaluation (Darwin Gödel seed)."""

    valid_syntax: bool
    lint_score: float  # 0.0 to 1.0
    quality_score: float  # 0.0 to 1.0
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Check if evaluation passed minimum threshold."""
        return self.valid_syntax and self.quality_score >= 0.6


@dataclass
class GeneratedCode:
    """Generated code result with self-evaluation."""

    code: str
    language: str
    explanation: str
    tests: Optional[str] = None
    tokens_used: int = 0
    evaluation: Optional[EvaluationResult] = None
    correction_attempts: int = 0


# =============================================================================
# DARWIN GÖDEL MACHINE TYPES
# =============================================================================


@dataclass
class AgentVariant:
    """
    A variant in the Darwin Gödel lineage.

    Each variant represents a version of the agent with specific
    prompts, tools, and strategies that can be evolved.
    """

    id: str
    parent_id: Optional[str]
    generation: int
    system_prompt: str
    tools: List[str]
    strategies: Dict[str, Any]
    benchmark_scores: Dict[str, float] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modification_description: str = ""

    @property
    def fitness(self) -> float:
        """Calculate overall fitness from benchmark scores."""
        if not self.benchmark_scores:
            return 0.0
        return sum(self.benchmark_scores.values()) / len(self.benchmark_scores)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "generation": self.generation,
            "system_prompt": self.system_prompt,
            "tools": self.tools,
            "strategies": self.strategies,
            "benchmark_scores": self.benchmark_scores,
            "created_at": self.created_at,
            "modification_description": self.modification_description,
            "fitness": self.fitness,
        }


@dataclass
class EvolutionResult:
    """Result of an evolution cycle."""

    new_variant: AgentVariant
    improvement: float  # Percentage improvement over parent
    modifications_made: List[str]
    benchmark_results: Dict[str, float]
    success: bool


@dataclass
class BenchmarkTask:
    """A task for benchmarking agent performance."""

    id: str
    description: str
    expected_output: Optional[str] = None
    test_code: Optional[str] = None
    language: str = "python"
    difficulty: str = "medium"  # easy, medium, hard
