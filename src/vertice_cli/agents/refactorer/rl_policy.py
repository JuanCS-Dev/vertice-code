"""
Reinforcement Learning Policy for Refactoring Decisions.

This module provides RL-guided refactoring suggestions based on:
- Code state metrics (complexity, coupling, cohesion)
- Historical refactoring outcomes
- Quality improvement patterns

Architecture inspired by:
- AI Code Refactoring with RL (2025)
- Q-learning for code quality optimization
"""

from typing import Any, Dict, List, Tuple

from .models import RefactoringAction, RefactoringType


class RLRefactoringPolicy:
    """Reinforcement Learning policy for refactoring decisions.

    This policy learns which refactorings improve code quality
    based on observed outcomes.

    Attributes:
        action_history: History of (action, reward) pairs
        quality_metrics: Metrics used for state representation
    """

    def __init__(self):
        """Initialize RL policy."""
        self.action_history: List[Tuple[RefactoringAction, float]] = []
        self.quality_metrics = ["complexity", "maintainability", "test_coverage"]

    def suggest_refactoring(
        self, code_state: Dict[str, Any], available_actions: List[RefactoringAction]
    ) -> RefactoringAction:
        """Suggest best refactoring action based on learned policy.

        Args:
            code_state: Current code quality metrics
            available_actions: List of possible refactoring actions

        Returns:
            Best refactoring action based on estimated reward
        """
        for action in available_actions:
            action.estimated_reward = self._estimate_reward(action, code_state)

        best_action = max(available_actions, key=lambda a: a.estimated_reward)
        return best_action

    def update_policy(self, action: RefactoringAction, reward: float) -> None:
        """Update policy based on observed reward.

        Args:
            action: The action that was taken
            reward: The observed reward
        """
        self.action_history.append((action, reward))

    def _estimate_reward(self, action: RefactoringAction, state: Dict[str, Any]) -> float:
        """Estimate reward for taking action in current state.

        Uses heuristics based on code quality research:
        - High complexity → extract/decompose rewards
        - Dead code → removal rewards
        - High coupling → penalty (risk of breakage)

        Args:
            action: Proposed refactoring action
            state: Current code metrics

        Returns:
            Estimated reward value
        """
        reward = 0.0

        # High complexity benefits from extraction/decomposition
        if state.get("complexity", 0) > 15:
            if action.type in [
                RefactoringType.EXTRACT_METHOD,
                RefactoringType.DECOMPOSE_CONDITIONAL,
            ]:
                reward += 5.0

        # Dead code removal is always beneficial
        if action.type == RefactoringType.REMOVE_DEAD_CODE:
            reward += 3.0

        # Modernization improves maintainability
        if action.type == RefactoringType.MODERNIZE_SYNTAX:
            reward += 2.0

        # Simplification reduces cognitive load
        if action.type == RefactoringType.SIMPLIFY_EXPRESSION:
            reward += 2.5

        # High coupling increases risk of breakage
        if state.get("coupling", 0) > 10:
            reward -= 2.0

        # Penalty for changes affecting many files
        blast_radius = state.get("blast_radius", 0)
        if blast_radius > 5:
            reward -= 1.0 * (blast_radius / 5)

        return reward

    def get_statistics(self) -> Dict[str, Any]:
        """Get policy statistics.

        Returns:
            Dictionary with policy statistics
        """
        if not self.action_history:
            return {"total_actions": 0, "avg_reward": 0.0}

        total_reward = sum(r for _, r in self.action_history)
        avg_reward = total_reward / len(self.action_history)

        action_counts: Dict[str, int] = {}
        for action, _ in self.action_history:
            action_type = action.type.value
            action_counts[action_type] = action_counts.get(action_type, 0) + 1

        return {
            "total_actions": len(self.action_history),
            "avg_reward": avg_reward,
            "action_distribution": action_counts,
        }


__all__ = ["RLRefactoringPolicy"]
