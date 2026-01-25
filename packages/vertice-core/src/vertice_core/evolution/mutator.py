"""
Composite Mutation Operator

GVU Generate phase: Combines multiple mutators for adaptive operator selection.

References:
- arXiv:2505.22954 (Darwin Gödel Machine)
- arXiv:2512.02731 (GVU Operator Framework)
"""

from __future__ import annotations

import logging
import random
from typing import Any, Dict, List, Optional

from .types import AgentVariant, MutationType, MutationProposal
from .operators import (
    BaseMutator,
    PromptMutator,
    ToolMutator,
    WorkflowMutator,
    ParameterMutator,
)

logger = logging.getLogger(__name__)

# Re-export for backwards compatibility
__all__ = [
    "BaseMutator",
    "PromptMutator",
    "ToolMutator",
    "WorkflowMutator",
    "ParameterMutator",
    "CompositeMutator",
]


class CompositeMutator(BaseMutator):
    """
    Combines multiple mutators for the GVU Generate phase.

    Implements multi-operator selection from evolutionary computation.
    """

    mutation_type = MutationType.STRATEGY

    def __init__(self, mutators: Optional[List[BaseMutator]] = None):
        """
        Initialize with list of mutators.

        Args:
            mutators: List of mutators to use (default: all types)
        """
        self._mutators = mutators or [
            PromptMutator(),
            ToolMutator(),
            WorkflowMutator(),
            ParameterMutator(),
        ]

        # Adaptive operator selection weights
        self._operator_weights = {m.mutation_type: 1.0 for m in self._mutators}
        self._operator_success = {m.mutation_type: [] for m in self._mutators}

    def propose(self, variant: AgentVariant) -> Optional[MutationProposal]:
        """Propose a mutation using adaptive operator selection."""
        mutators = list(self._mutators)
        weights = [self._operator_weights.get(m.mutation_type, 1.0) for m in mutators]
        total = sum(weights)
        weights = [w / total for w in weights]

        selected_order = random.choices(mutators, weights=weights, k=len(mutators))

        for mutator in selected_order:
            proposal = mutator.propose(variant)
            if proposal:
                proposal.generator_model = mutator.__class__.__name__
                return proposal

        return None

    def apply(self, variant: AgentVariant, proposal: MutationProposal) -> AgentVariant:
        """Apply mutation using the appropriate mutator."""
        for mutator in self._mutators:
            if mutator.mutation_type == proposal.mutation_type:
                return mutator.apply(variant, proposal)

        logger.warning(f"[Mutator] No handler for {proposal.mutation_type}, returning clone")
        return variant.clone()

    def update_success(self, mutation_type: MutationType, success: bool) -> None:
        """
        Update operator selection weights based on success.

        Implements adaptive operator selection (AOS).
        """
        reward = 1.0 if success else 0.0
        self._operator_success[mutation_type].append(reward)

        max_history = 20
        if len(self._operator_success[mutation_type]) > max_history:
            self._operator_success[mutation_type] = self._operator_success[mutation_type][
                -max_history:
            ]

        history = self._operator_success[mutation_type]
        if history:
            success_rate = sum(history) / len(history)
            self._operator_weights[mutation_type] = 0.5 + success_rate

    def get_mutator_types(self) -> List[MutationType]:
        """Get list of mutation types this composite can handle."""
        return [m.mutation_type for m in self._mutators]

    def get_operator_stats(self) -> Dict[str, Any]:
        """Get adaptive operator selection statistics."""
        return {
            "weights": dict(self._operator_weights),
            "success_rates": {
                mt.value: (sum(h) / len(h) if h else 0.0)
                for mt, h in self._operator_success.items()
            },
        }
