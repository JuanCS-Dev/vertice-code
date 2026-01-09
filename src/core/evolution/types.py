"""
Evolution Types

Type definitions for self-improving agent systems.

References:
- arXiv:2505.22954 (Darwin Gödel Machine - Sakana AI)
- arXiv:2512.02731 (GVU Operator Framework - unified self-improvement)
- arXiv:2310.11958 (STaR: Self-Taught Reasoner)
- arXiv:2401.01335 (SPIN: Self-Play Fine-Tuning)
- Quality-Diversity optimization (Mouret & Clune, 2015)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime
import uuid


class MutationType(str, Enum):
    """Types of mutations that can be applied to an agent."""
    PROMPT = "prompt"           # Modify system prompts (STaR-style)
    TOOL = "tool"               # Add/modify tools
    WORKFLOW = "workflow"       # Change execution workflow
    STRATEGY = "strategy"       # Adjust decision strategies
    PARAMETER = "parameter"     # Tune hyperparameters
    ARCHITECTURE = "architecture"  # Structural changes (DGM)


class EvolutionStatus(str, Enum):
    """Status of an evolution cycle."""
    PENDING = "pending"
    GENERATING = "generating"    # GVU: Generator phase
    VERIFYING = "verifying"      # GVU: Verifier phase
    UPDATING = "updating"        # GVU: Updater phase
    IMPROVED = "improved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class GVUPhase(str, Enum):
    """
    GVU Operator phases (arXiv:2512.02731).

    The GVU framework unifies:
    - STaR (Self-Taught Reasoner)
    - SPIN (Self-Play)
    - Reflexion
    - AlphaZero self-play
    - GANs
    """
    GENERATE = "generate"   # G: Generate candidate solutions
    VERIFY = "verify"       # V: Verify/evaluate candidates
    UPDATE = "update"       # U: Update model based on verification


@dataclass
class KappaMetrics:
    """
    κ coefficient metrics (arXiv:2512.02731).

    The κ coefficient is conceptualized as a Lie derivative measuring
    the rate of self-improvement in the agent's capability space.

    κ = lim(t→0) [f(θ + t·∇θ) - f(θ)] / t

    Where f is the fitness function and θ are agent parameters.
    """
    kappa: float = 0.0              # Self-improvement rate
    kappa_variance: float = 0.0     # Variance in improvement
    improvement_velocity: float = 0.0  # d(fitness)/dt
    improvement_acceleration: float = 0.0  # d²(fitness)/dt²

    # Per-dimension κ for interpretability
    kappa_per_dimension: Dict[str, float] = field(default_factory=dict)

    def compute_kappa(
        self,
        fitness_history: List[float],
        time_steps: Optional[List[float]] = None,
    ) -> float:
        """
        Compute κ coefficient from fitness history.

        Uses finite difference approximation of the Lie derivative.
        """
        if len(fitness_history) < 2:
            return 0.0

        if time_steps is None:
            time_steps = list(range(len(fitness_history)))

        # Compute velocity (first derivative)
        velocities = []
        for i in range(1, len(fitness_history)):
            dt = time_steps[i] - time_steps[i - 1]
            if dt > 0:
                v = (fitness_history[i] - fitness_history[i - 1]) / dt
                velocities.append(v)

        if not velocities:
            return 0.0

        self.improvement_velocity = sum(velocities) / len(velocities)

        # Compute acceleration (second derivative)
        if len(velocities) >= 2:
            accelerations = []
            for i in range(1, len(velocities)):
                dt = time_steps[i + 1] - time_steps[i]
                if dt > 0:
                    a = (velocities[i] - velocities[i - 1]) / dt
                    accelerations.append(a)
            if accelerations:
                self.improvement_acceleration = sum(accelerations) / len(accelerations)

        # κ is the normalized improvement rate
        max_fitness = max(fitness_history) if fitness_history else 1.0
        self.kappa = self.improvement_velocity / max_fitness if max_fitness > 0 else 0.0
        self.kappa_variance = (
            sum((v - self.improvement_velocity) ** 2 for v in velocities) / len(velocities)
            if velocities else 0.0
        )

        return self.kappa


@dataclass
class AgentVariant:
    """
    A variant of an agent in the evolution archive.

    Tracks lineage and performance across generations.
    Supports Quality-Diversity (QD) optimization.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_id: Optional[str] = None
    generation: int = 0

    # Configuration
    prompts: Dict[str, str] = field(default_factory=dict)
    tools: List[str] = field(default_factory=list)
    workflow: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Performance metrics
    fitness_score: float = 0.0
    benchmark_results: Dict[str, float] = field(default_factory=dict)

    # Quality-Diversity metrics (Mouret & Clune, 2015)
    behavior_descriptor: List[float] = field(default_factory=list)
    novelty_score: float = 0.0
    niche_id: Optional[str] = None

    # GVU metrics (arXiv:2512.02731)
    kappa_metrics: KappaMetrics = field(default_factory=KappaMetrics)
    verification_score: float = 0.0  # V phase score
    generation_quality: float = 0.0  # G phase score

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def clone(self) -> AgentVariant:
        """Create a clone of this variant for mutation."""
        return AgentVariant(
            parent_id=self.id,
            generation=self.generation + 1,
            prompts=dict(self.prompts),
            tools=list(self.tools),
            workflow=dict(self.workflow),
            parameters=dict(self.parameters),
            behavior_descriptor=list(self.behavior_descriptor),
            metadata={"cloned_from": self.id},
        )

    def compute_behavior_descriptor(self) -> List[float]:
        """
        Compute behavior descriptor for QD optimization.

        Returns a vector characterizing the agent's behavioral niche.
        """
        descriptor = []

        # Prompt complexity
        total_prompt_length = sum(len(p) for p in self.prompts.values())
        descriptor.append(min(1.0, total_prompt_length / 10000))

        # Tool diversity
        descriptor.append(min(1.0, len(self.tools) / 10))

        # Workflow complexity
        workflow_depth = len(str(self.workflow))
        descriptor.append(min(1.0, workflow_depth / 1000))

        # Parameter count
        param_count = len(self.parameters)
        descriptor.append(min(1.0, param_count / 20))

        self.behavior_descriptor = descriptor
        return descriptor

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "generation": self.generation,
            "prompts": self.prompts,
            "tools": self.tools,
            "workflow": self.workflow,
            "parameters": self.parameters,
            "fitness_score": self.fitness_score,
            "benchmark_results": self.benchmark_results,
            "behavior_descriptor": self.behavior_descriptor,
            "novelty_score": self.novelty_score,
            "niche_id": self.niche_id,
            "verification_score": self.verification_score,
            "generation_quality": self.generation_quality,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AgentVariant:
        """Create from dictionary."""
        # Handle nested KappaMetrics
        kappa_data = data.pop("kappa_metrics", None)
        variant = cls(**data)
        if kappa_data:
            variant.kappa_metrics = KappaMetrics(**kappa_data)
        return variant


@dataclass
class MutationProposal:
    """
    A proposed mutation following GVU Generate phase.

    Includes confidence calibration for uncertainty quantification.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    mutation_type: MutationType = MutationType.PROMPT
    target_key: str = ""
    original_value: Any = None
    proposed_value: Any = None
    reasoning: str = ""

    # Confidence with calibration (arXiv:2503.15850)
    confidence: float = 0.5
    confidence_calibrated: float = 0.5  # Post-calibration confidence
    uncertainty_type: str = "epistemic"  # epistemic vs aleatoric

    # GVU metadata
    gvu_phase: GVUPhase = GVUPhase.GENERATE
    generator_model: str = ""

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationResult:
    """
    Result of GVU Verify phase.

    Captures empirical validation of a mutation.
    """
    proposal_id: str = ""
    verified: bool = False
    verification_score: float = 0.0

    # Benchmark results
    benchmark_passed: int = 0
    benchmark_failed: int = 0
    benchmark_total: int = 0

    # Confidence in verification
    verification_confidence: float = 0.0
    false_positive_risk: float = 0.0

    reasoning: str = ""


@dataclass
class EvolutionResult:
    """
    Result of an evolution cycle (full GVU iteration).

    Tracks all three phases: Generate → Verify → Update.
    """
    cycle_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_variant: AgentVariant = field(default_factory=AgentVariant)
    child_variant: AgentVariant = field(default_factory=AgentVariant)
    mutations_applied: List[MutationProposal] = field(default_factory=list)
    status: EvolutionStatus = EvolutionStatus.PENDING

    # GVU phase results
    generation_time_ms: float = 0.0
    verification_time_ms: float = 0.0
    update_time_ms: float = 0.0
    verification_result: Optional[VerificationResult] = None

    # Metrics
    fitness_delta: float = 0.0
    evaluation_time_ms: float = 0.0
    kappa_contribution: float = 0.0  # Contribution to κ

    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cycle_id": self.cycle_id,
            "parent_id": self.parent_variant.id,
            "child_id": self.child_variant.id,
            "mutations_count": len(self.mutations_applied),
            "status": self.status.value,
            "fitness_delta": self.fitness_delta,
            "kappa_contribution": self.kappa_contribution,
            "evaluation_time_ms": self.evaluation_time_ms,
            "gvu_times": {
                "generate": self.generation_time_ms,
                "verify": self.verification_time_ms,
                "update": self.update_time_ms,
            },
            "reasoning": self.reasoning,
        }


@dataclass
class EvolutionConfig:
    """
    Configuration for evolution system.

    Combines Darwin-Gödel, GVU, and QD parameters.
    """
    # Core thresholds
    improvement_threshold: float = 0.05  # 5% improvement required
    verification_threshold: float = 0.8  # 80% benchmark pass rate

    # Archive settings (QD optimization)
    max_archive_size: int = 100
    diversity_weight: float = 0.3
    exploitation_weight: float = 0.7
    novelty_threshold: float = 0.1  # Minimum novelty for archival

    # Mutation settings
    mutation_rate: float = 0.2
    crossover_rate: float = 0.1

    # GVU settings
    max_generation_attempts: int = 5
    verification_sample_size: int = 10
    update_learning_rate: float = 0.01

    # Timeouts
    benchmark_timeout_seconds: int = 300
    generation_timeout_seconds: int = 60

    # Limits
    max_generations: int = 1000
    target_kappa: float = 0.1  # Target self-improvement rate
