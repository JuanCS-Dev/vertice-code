"""
Evolution Module

Darwin-Gödel Machine implementation for self-improving agents.

References:
- arXiv:2505.22954 (Darwin Gödel Machine - Sakana AI)
- arXiv:2512.02731 (GVU Operator Framework)
- arXiv:2310.11958 (STaR: Self-Taught Reasoner)
- arXiv:2401.01335 (SPIN: Self-Play Fine-Tuning)
- arXiv:2303.11366 (Reflexion)
- Quality-Diversity optimization (Mouret & Clune, 2015)
- Novelty Search (Lehman & Stanley, 2011)
"""

from .types import (
    MutationType,
    EvolutionStatus,
    GVUPhase,
    KappaMetrics,
    AgentVariant,
    MutationProposal,
    VerificationResult,
    EvolutionResult,
    EvolutionConfig,
)
from .archive import SolutionArchive
from .mutator import (
    BaseMutator,
    PromptMutator,
    ToolMutator,
    WorkflowMutator,
    ParameterMutator,
    CompositeMutator,
)
from .evaluator import BenchmarkEvaluator
from .mixin import EvolutionMixin

__all__ = [
    # Types
    "MutationType",
    "EvolutionStatus",
    "GVUPhase",
    "KappaMetrics",
    "AgentVariant",
    "MutationProposal",
    "VerificationResult",
    "EvolutionResult",
    "EvolutionConfig",
    # Archive
    "SolutionArchive",
    # Mutators
    "BaseMutator",
    "PromptMutator",
    "ToolMutator",
    "WorkflowMutator",
    "ParameterMutator",
    "CompositeMutator",
    # Evaluator
    "BenchmarkEvaluator",
    # Mixin
    "EvolutionMixin",
]
