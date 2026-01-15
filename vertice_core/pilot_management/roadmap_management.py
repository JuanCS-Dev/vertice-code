"""
Product Roadmap Management
==========================

Strategic roadmap planning and milestone management.

This module provides:
- Roadmap milestone creation and tracking
- Business value assessment for roadmap items
- Timeline management and dependency tracking

Part of the Product Iteration Engine.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Any
from datetime import datetime
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class RoadmapMilestone(BaseModel):
    """A milestone in the product roadmap."""

    id: str
    name: str
    description: str
    target_date: datetime
    theme: str  # Strategic theme (e.g., "Enterprise Expansion", "AI Enhancement")

    # Content
    planned_features: List[str] = Field(default_factory=list)  # Feature IDs
    key_objectives: List[str] = Field(default_factory=list)

    # Status
    status: str = "planned"  # planned, in_progress, completed, delayed
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)

    # Business impact
    expected_business_value: float = 0.0  # Expected revenue impact
    risk_level: str = "medium"  # low, medium, high, critical


class RoadmapManager:
    """
    Manager for product roadmap milestones and planning.
    """

    def __init__(self) -> None:
        """Initialize the roadmap manager."""
        self.milestones: Dict[str, RoadmapMilestone] = {}
        self.logger = logging.getLogger(f"{__name__}.RoadmapManager")

    async def create_milestone(
        self,
        name: str,
        description: str,
        target_date: datetime,
        theme: str,
        planned_features: List[str],
        key_objectives: List[str],
    ) -> str:
        """
        Create a new roadmap milestone.

        Args:
            name: Milestone name
            description: Milestone description
            target_date: Target completion date
            theme: Strategic theme
            planned_features: List of feature IDs
            key_objectives: Key objectives

        Returns:
            Milestone ID
        """
        milestone_id = f"milestone_{int(datetime.utcnow().timestamp())}"

        milestone = RoadmapMilestone(
            id=milestone_id,
            name=name,
            description=description,
            target_date=target_date,
            theme=theme,
            planned_features=planned_features,
            key_objectives=key_objectives,
        )

        self.milestones[milestone_id] = milestone

        self.logger.info(f"Created roadmap milestone: {milestone_id} - {name}")
        return milestone_id

    async def get_roadmap_view(self) -> Dict[str, Any]:
        """
        Get a comprehensive roadmap view.

        Returns:
            Roadmap data including milestones and themes
        """
        # Get all milestones sorted by date
        milestones = list(self.milestones.values())
        milestones.sort(key=lambda m: m.target_date)

        # Calculate roadmap metrics
        total_features = sum(len(m.planned_features) for m in milestones)
        completed_features = sum(
            len(
                [f for f in m.planned_features if self._is_feature_completed(f)]
            )  # Would check actual feature status
            for m in milestones
        )

        roadmap_completion = (
            (completed_features / total_features * 100) if total_features > 0 else 0
        )

        return {
            "milestones": [
                {
                    "id": m.id,
                    "name": m.name,
                    "theme": m.theme,
                    "target_date": m.target_date.isoformat(),
                    "status": m.status,
                    "progress_percentage": m.progress_percentage,
                    "planned_features_count": len(m.planned_features),
                    "completed_features_count": self._count_completed_features(m.planned_features),
                }
                for m in milestones
            ],
            "summary": {
                "total_milestones": len(milestones),
                "total_features": total_features,
                "completed_features": completed_features,
                "roadmap_completion_percentage": roadmap_completion,
                "next_milestone": milestones[0].name if milestones else None,
                "next_milestone_date": (
                    milestones[0].target_date.isoformat() if milestones else None
                ),
            },
            "themes": self._get_theme_breakdown(milestones),
        }

    def _is_feature_completed(self, feature_id: str) -> bool:
        """Check if a feature is completed (simplified)."""
        # In production, this would check actual feature status
        return False  # Placeholder

    def _count_completed_features(self, feature_ids: List[str]) -> int:
        """Count completed features in a list."""
        return sum(1 for fid in feature_ids if self._is_feature_completed(fid))

    def _get_theme_breakdown(self, milestones: List[RoadmapMilestone]) -> Dict[str, Any]:
        """Get breakdown of features by theme."""
        themes: Dict[str, Dict[str, int]] = {}

        for milestone in milestones:
            theme = milestone.theme
            if theme not in themes:
                themes[theme] = {"milestones": 0, "features": 0, "completed_features": 0}

            themes[theme]["milestones"] += 1
            themes[theme]["features"] += len(milestone.planned_features)
            themes[theme]["completed_features"] += self._count_completed_features(
                milestone.planned_features
            )

        return themes
