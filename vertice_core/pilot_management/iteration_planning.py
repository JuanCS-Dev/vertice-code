"""
Iteration Planning Management
=============================

Sprint/iteration planning and capacity management.

This module provides:
- Iteration plan creation and management
- Capacity planning and resource allocation
- Progress tracking and completion monitoring

Part of the Product Iteration Engine.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


logger = logging.getLogger(__name__)


@dataclass
class IterationPlan:
    """A product iteration plan (sprint/release)."""

    id: str
    name: str
    start_date: datetime
    end_date: datetime

    # Capacity and goals
    team_capacity_days: int  # Total team capacity in person-days
    planned_features: List[str] = field(default_factory=list)  # Feature IDs
    stretch_goals: List[str] = field(default_factory=list)  # Nice-to-have features

    # Status
    status: str = "planned"  # planned, active, completed
    completed_features: List[str] = field(default_factory=list)

    # Metrics
    planned_velocity: float = 0.0  # Story points or feature points
    actual_velocity: float = 0.0
    quality_score: float = 0.0  # 0-100 quality assessment

    @property
    def duration_days(self) -> int:
        """Calculate iteration duration."""
        return (self.end_date - self.start_date).days

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        total_features = len(self.planned_features)
        if total_features == 0:
            return 100.0
        return (len(self.completed_features) / total_features) * 100.0

    @property
    def capacity_utilization(self) -> float:
        """Calculate capacity utilization."""
        # Simplified calculation
        planned_effort = sum(self._estimate_feature_effort(fid) for fid in self.planned_features)
        if planned_effort == 0:
            return 0.0
        return min(100.0, (planned_effort / self.team_capacity_days) * 100.0)

    def _estimate_feature_effort(self, feature_id: str) -> float:
        """Estimate effort for a feature (simplified)."""
        effort_map = {"small": 3, "medium": 10, "large": 25, "extra_large": 60}
        return effort_map.get("medium", 10)


class IterationPlanningManager:
    """
    Manager for iteration planning and execution.
    """

    def __init__(self) -> None:
        """Initialize the iteration planning manager."""
        self.iteration_plans: Dict[str, IterationPlan] = {}
        self.logger = logging.getLogger(f"{__name__}.IterationPlanningManager")

    async def create_iteration_plan(
        self,
        name: str,
        start_date: datetime,
        end_date: datetime,
        team_capacity_days: int,
        planned_features: List[str],
    ) -> str:
        """
        Create a new iteration plan.

        Args:
            name: Iteration name
            start_date: Iteration start date
            end_date: Iteration end date
            team_capacity_days: Team capacity in person-days
            planned_features: List of feature IDs to include

        Returns:
            Iteration plan ID
        """
        iteration_id = f"iteration_{int(datetime.utcnow().timestamp())}"

        iteration = IterationPlan(
            id=iteration_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            team_capacity_days=team_capacity_days,
            planned_features=planned_features,
        )

        self.iteration_plans[iteration_id] = iteration

        self.logger.info(f"Created iteration plan: {iteration_id} - {name}")
        return iteration_id

    async def get_iteration_backlog(self) -> List[str]:
        """
        Get the current iteration backlog (prioritized features not yet planned).

        Returns:
            List of feature IDs ready for iteration planning
        """
        # Simplified - would integrate with feature prioritization
        return ["feature_1", "feature_2", "feature_3"]  # Placeholder

    async def update_iteration_progress(
        self, iteration_id: str, completed_features: List[str], status: Optional[str] = None
    ) -> bool:
        """
        Update progress for an active iteration.

        Args:
            iteration_id: Iteration identifier
            completed_features: List of completed feature IDs
            status: New status (optional)

        Returns:
            True if update was successful
        """
        iteration = self.iteration_plans.get(iteration_id)
        if not iteration:
            return False

        iteration.completed_features.extend(completed_features)
        if status:
            iteration.status = status

        self.logger.info(
            f"Updated progress for iteration {iteration_id}: {len(completed_features)} features completed"
        )
        return True
