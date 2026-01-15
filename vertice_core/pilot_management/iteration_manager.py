"""
Weekly Iteration Management for Enterprise Pilots
================================================

Comprehensive system for managing weekly iteration cycles, feedback collection,
and success metrics tracking for enterprise pilot programs.

This module provides:
- Weekly iteration planning and execution
- Structured feedback collection from all stakeholders
- Success metrics monitoring and alerting
- Iteration-based program adjustments
- Automated reporting and stakeholder communication

Part of the Enterprise Pilot Launch (Fase 2 Mês 7).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class IterationStatus(Enum):
    """Status of a weekly iteration."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXTENDED = "extended"


class FeedbackType(Enum):
    """Types of feedback collected during iterations."""

    TECHNICAL = "technical"
    BUSINESS = "business"
    USER_EXPERIENCE = "user_experience"
    SUCCESS_MANAGER = "success_manager"
    EXECUTIVE = "executive"


class MetricTrend(Enum):
    """Trend direction for success metrics."""

    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    CRITICAL = "critical"


class IterationGoal(BaseModel):
    """Specific goal for a weekly iteration."""

    id: str
    description: str
    category: str  # technical, adoption, integration, etc.
    priority: int = Field(ge=1, le=5)  # 1=lowest, 5=highest
    assigned_to: Optional[str] = None
    estimated_effort_hours: float = Field(ge=0.5, le=40.0)
    success_criteria: List[str] = Field(default_factory=list)

    @property
    def is_completed(self) -> bool:
        """Check if goal has completion markers."""
        return any(
            "✓" in criteria or "completed" in criteria.lower() for criteria in self.success_criteria
        )


class FeedbackEntry(BaseModel):
    """Structured feedback entry from stakeholders."""

    id: str
    iteration_number: int
    feedback_type: FeedbackType
    stakeholder_name: str
    stakeholder_title: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    # Feedback content
    overall_satisfaction: float = Field(ge=0.0, le=10.0)
    key_achievements: List[str] = Field(default_factory=list)
    challenges_encountered: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    # Detailed ratings
    ease_of_use: Optional[float] = Field(None, ge=0.0, le=10.0)
    feature_completeness: Optional[float] = Field(None, ge=0.0, le=10.0)
    performance_satisfaction: Optional[float] = Field(None, ge=0.0, le=10.0)
    support_quality: Optional[float] = Field(None, ge=0.0, le=10.0)

    # Free-form feedback
    positive_feedback: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    additional_comments: Optional[str] = None

    @property
    def sentiment_score(self) -> float:
        """Calculate overall sentiment score from ratings."""
        ratings = [
            self.overall_satisfaction,
            self.ease_of_use,
            self.feature_completeness,
            self.performance_satisfaction,
            self.support_quality,
        ]

        valid_ratings = [r for r in ratings if r is not None]
        return sum(valid_ratings) / len(valid_ratings) if valid_ratings else 5.0


class SuccessMetricsSnapshot(BaseModel):
    """Snapshot of success metrics at a point in time."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    iteration_number: int

    # Adoption metrics
    active_users: int = 0
    total_sessions: int = 0
    features_used: int = 0
    integrations_configured: int = 0

    # Performance metrics
    average_response_time_ms: float = 0.0
    error_rate_percentage: float = 0.0
    uptime_percentage: float = 100.0

    # Quality metrics
    code_reviews_completed: int = 0
    bugs_reported: int = 0
    user_satisfaction_score: float = 0.0

    # Business metrics
    time_saved_hours: float = 0.0
    productivity_gain_percentage: float = 0.0
    roi_percentage: float = 0.0

    def calculate_trends(
        self, previous: Optional[SuccessMetricsSnapshot]
    ) -> Dict[str, MetricTrend]:
        """Calculate metric trends compared to previous snapshot."""
        if not previous:
            return {}

        trends = {}

        # Adoption trends
        if self.active_users > previous.active_users * 1.1:
            trends["adoption"] = MetricTrend.IMPROVING
        elif self.active_users < previous.active_users * 0.9:
            trends["adoption"] = MetricTrend.DECLINING
        else:
            trends["adoption"] = MetricTrend.STABLE

        # Performance trends
        if self.average_response_time_ms > previous.average_response_time_ms * 1.2:
            trends["performance"] = MetricTrend.DECLINING
        elif self.average_response_time_ms < previous.average_response_time_ms * 0.8:
            trends["performance"] = MetricTrend.IMPROVING
        else:
            trends["performance"] = MetricTrend.STABLE

        # Quality trends
        if self.error_rate_percentage > previous.error_rate_percentage * 1.5:
            trends["quality"] = MetricTrend.DECLINING
        elif self.error_rate_percentage < previous.error_rate_percentage * 0.5:
            trends["quality"] = MetricTrend.IMPROVING
        else:
            trends["quality"] = MetricTrend.STABLE

        # Business impact
        if self.productivity_gain_percentage > previous.productivity_gain_percentage:
            trends["business_impact"] = MetricTrend.IMPROVING
        elif self.productivity_gain_percentage < previous.productivity_gain_percentage * 0.9:
            trends["business_impact"] = MetricTrend.DECLINING
        else:
            trends["business_impact"] = MetricTrend.STABLE

        return trends


@dataclass
class WeeklyIteration:
    """Complete weekly iteration for a pilot program."""

    number: int
    pilot_program_id: str
    planned_start_date: datetime
    planned_end_date: datetime

    # Optional timeline fields
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None

    # Status and progress
    status: IterationStatus = IterationStatus.PLANNED
    progress_percentage: float = 0.0

    # Goals and deliverables
    goals: List[IterationGoal] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)

    # Feedback and metrics
    feedback_entries: List[FeedbackEntry] = field(default_factory=list)
    metrics_snapshot: Optional[SuccessMetricsSnapshot] = None

    # Outcomes and learnings
    key_learnings: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    next_iteration_focus: List[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def duration_days(self) -> int:
        """Calculate actual iteration duration."""
        start = self.actual_start_date or self.planned_start_date
        end = self.actual_end_date or datetime.utcnow()
        return (end - start).days

    @property
    def is_on_track(self) -> bool:
        """Check if iteration is progressing according to plan."""
        if self.status != IterationStatus.IN_PROGRESS:
            return True

        # Should be at least 20% complete per day
        expected_progress = min(100.0, self.duration_days * 20.0)
        return self.progress_percentage >= expected_progress * 0.8  # 80% of expected

    @property
    def completion_score(self) -> float:
        """Calculate iteration completion score."""
        if not self.goals:
            return 0.0

        completed_goals = sum(1 for goal in self.goals if goal.is_completed)
        return (completed_goals / len(self.goals)) * 100.0

    @property
    def feedback_summary(self) -> Dict[str, Any]:
        """Generate summary of all feedback for this iteration."""
        if not self.feedback_entries:
            return {}

        total_entries = len(self.feedback_entries)
        avg_satisfaction = (
            sum(entry.sentiment_score for entry in self.feedback_entries) / total_entries
        )

        feedback_by_type: Dict[str, List[float]] = {}
        for entry in self.feedback_entries:
            if entry.feedback_type.value not in feedback_by_type:
                feedback_by_type[entry.feedback_type.value] = []
            feedback_by_type[entry.feedback_type.value].append(entry.sentiment_score)

        return {
            "total_feedback_entries": total_entries,
            "average_satisfaction": avg_satisfaction,
            "feedback_by_type": {
                ftype: sum(scores) / len(scores) for ftype, scores in feedback_by_type.items()
            },
            "key_themes": self._extract_key_themes(),
        }

    def _extract_key_themes(self) -> Dict[str, int]:
        """Extract common themes from feedback."""
        themes: Dict[str, int] = {}

        for entry in self.feedback_entries:
            # Analyze positive feedback
            if entry.positive_feedback:
                if "performance" in entry.positive_feedback.lower():
                    themes["performance"] = themes.get("performance", 0) + 1
                if "usability" in entry.positive_feedback.lower():
                    themes["usability"] = themes.get("usability", 0) + 1
                if "features" in entry.positive_feedback.lower():
                    themes["features"] = themes.get("features", 0) + 1

            # Analyze improvement areas
            if entry.areas_for_improvement:
                if "integration" in entry.areas_for_improvement.lower():
                    themes["integration"] = themes.get("integration", 0) + 1
                if "training" in entry.areas_for_improvement.lower():
                    themes["training"] = themes.get("training", 0) + 1
                if "support" in entry.areas_for_improvement.lower():
                    themes["support"] = themes.get("support", 0) + 1

        return themes


class IterationPlanningTemplate(BaseModel):
    """Template for planning weekly iterations."""

    name: str
    description: str
    applicable_industries: List[str] = Field(default_factory=list)
    applicable_tiers: List[str] = Field(default_factory=list)

    # Standard goals by iteration phase
    early_iteration_goals: List[Dict[str, Any]] = Field(default_factory=list)
    mid_iteration_goals: List[Dict[str, Any]] = Field(default_factory=list)
    late_iteration_goals: List[Dict[str, Any]] = Field(default_factory=list)

    # Success criteria templates
    success_criteria_templates: List[str] = Field(default_factory=list)

    # Expected metrics by iteration
    expected_metrics: Dict[str, Dict[str, float]] = Field(default_factory=dict)


class WeeklyIterationManager:
    """
    Manager for weekly iteration cycles in pilot programs.

    Handles iteration planning, execution tracking, feedback collection,
    and automated success metrics monitoring.
    """

    def __init__(self) -> None:
        """Initialize the iteration manager."""
        self.iterations: Dict[str, Dict[int, WeeklyIteration]] = (
            {}
        )  # program_id -> iteration_number -> iteration
        self.templates: Dict[str, IterationPlanningTemplate] = {}
        self.logger = logging.getLogger(f"{__name__}.WeeklyIterationManager")

    async def create_iteration(
        self,
        pilot_program_id: str,
        iteration_number: int,
        start_date: datetime,
        template_name: Optional[str] = None,
    ) -> WeeklyIteration:
        """
        Create a new weekly iteration for a pilot program.

        Args:
            pilot_program_id: Pilot program identifier
            iteration_number: Sequential iteration number
            start_date: When the iteration should start
            template_name: Optional template to use for planning

        Returns:
            Created weekly iteration
        """
        end_date = start_date + timedelta(days=7)

        iteration = WeeklyIteration(
            number=iteration_number,
            pilot_program_id=pilot_program_id,
            planned_start_date=start_date,
            planned_end_date=end_date,
        )

        # Apply template if specified
        if template_name and template_name in self.templates:
            await self._apply_template(iteration, template_name)

        # Initialize iterations dictionary
        if pilot_program_id not in self.iterations:
            self.iterations[pilot_program_id] = {}

        self.iterations[pilot_program_id][iteration_number] = iteration

        self.logger.info(f"Created iteration {iteration_number} for pilot {pilot_program_id}")
        return iteration

    async def _apply_template(self, iteration: WeeklyIteration, template_name: str) -> None:
        """Apply a planning template to an iteration."""
        template = self.templates[template_name]

        # Determine iteration phase
        if iteration.number <= 2:
            goal_templates = template.early_iteration_goals
        elif iteration.number <= 4:
            goal_templates = template.mid_iteration_goals
        else:
            goal_templates = template.late_iteration_goals

        # Create goals from templates
        for goal_data in goal_templates:
            goal = IterationGoal(
                id=f"goal_{iteration.number}_{len(iteration.goals) + 1}",
                description=goal_data.get("description", ""),
                category=goal_data.get("category", "general"),
                priority=goal_data.get("priority", 3),
                estimated_effort_hours=goal_data.get("effort_hours", 8.0),
                success_criteria=goal_data.get("success_criteria", []),
            )
            iteration.goals.append(goal)

    async def start_iteration(self, pilot_program_id: str, iteration_number: int) -> bool:
        """
        Mark an iteration as started.

        Args:
            pilot_program_id: Pilot program identifier
            iteration_number: Iteration number

        Returns:
            True if iteration was started successfully
        """
        iteration = self._get_iteration(pilot_program_id, iteration_number)
        if not iteration:
            return False

        iteration.status = IterationStatus.IN_PROGRESS
        iteration.actual_start_date = datetime.utcnow()
        iteration.updated_at = datetime.utcnow()

        self.logger.info(f"Started iteration {iteration_number} for pilot {pilot_program_id}")
        return True

    async def update_iteration_progress(
        self,
        pilot_program_id: str,
        iteration_number: int,
        progress_percentage: float,
        completed_goals: Optional[List[str]] = None,
        new_blockers: Optional[List[str]] = None,
    ) -> bool:
        """
        Update progress for an active iteration.

        Args:
            pilot_program_id: Pilot program identifier
            iteration_number: Iteration number
            progress_percentage: Current progress (0-100)
            completed_goals: List of completed goal IDs
            new_blockers: List of new blockers identified

        Returns:
            True if update was successful
        """
        iteration = self._get_iteration(pilot_program_id, iteration_number)
        if not iteration:
            return False

        iteration.progress_percentage = progress_percentage
        iteration.updated_at = datetime.utcnow()

        # Mark goals as completed
        if completed_goals:
            for goal in iteration.goals:
                if goal.id in completed_goals:
                    goal.success_criteria.append("✓ Completed")

        # Add new blockers
        if new_blockers:
            iteration.blockers.extend(new_blockers)

        self.logger.info(
            f"Updated progress for iteration {iteration_number}: {progress_percentage}%"
        )
        return True

    async def submit_feedback(
        self, pilot_program_id: str, iteration_number: int, feedback: FeedbackEntry
    ) -> bool:
        """
        Submit feedback for an iteration.

        Args:
            pilot_program_id: Pilot program identifier
            iteration_number: Iteration number
            feedback: Feedback entry to submit

        Returns:
            True if feedback was submitted successfully
        """
        iteration = self._get_iteration(pilot_program_id, iteration_number)
        if not iteration:
            return False

        feedback.id = (
            f"feedback_{pilot_program_id}_{iteration_number}_{len(iteration.feedback_entries) + 1}"
        )
        iteration.feedback_entries.append(feedback)
        iteration.updated_at = datetime.utcnow()

        self.logger.info(
            f"Submitted {feedback.feedback_type.value} feedback for iteration {iteration_number}"
        )
        return True

    async def record_metrics_snapshot(
        self, pilot_program_id: str, iteration_number: int, metrics: SuccessMetricsSnapshot
    ) -> bool:
        """
        Record success metrics snapshot for an iteration.

        Args:
            pilot_program_id: Pilot program identifier
            iteration_number: Iteration number
            metrics: Metrics snapshot to record

        Returns:
            True if metrics were recorded successfully
        """
        iteration = self._get_iteration(pilot_program_id, iteration_number)
        if not iteration:
            return False

        metrics.iteration_number = iteration_number
        iteration.metrics_snapshot = metrics
        iteration.updated_at = datetime.utcnow()

        self.logger.info(f"Recorded metrics snapshot for iteration {iteration_number}")
        return True

    async def complete_iteration(
        self,
        pilot_program_id: str,
        iteration_number: int,
        key_learnings: List[str],
        action_items: List[str],
        next_focus: List[str],
    ) -> bool:
        """
        Complete an iteration with outcomes and learnings.

        Args:
            pilot_program_id: Pilot program identifier
            iteration_number: Iteration number
            key_learnings: Key learnings from the iteration
            action_items: Action items for next steps
            next_focus: Focus areas for next iteration

        Returns:
            True if iteration was completed successfully
        """
        iteration = self._get_iteration(pilot_program_id, iteration_number)
        if not iteration:
            return False

        iteration.status = IterationStatus.COMPLETED
        iteration.actual_end_date = datetime.utcnow()
        iteration.key_learnings = key_learnings
        iteration.action_items = action_items
        iteration.next_iteration_focus = next_focus
        iteration.updated_at = datetime.utcnow()

        self.logger.info(f"Completed iteration {iteration_number} for pilot {pilot_program_id}")
        return True

    async def get_iteration_report(
        self, pilot_program_id: str, iteration_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a comprehensive report for an iteration.

        Args:
            pilot_program_id: Pilot program identifier
            iteration_number: Iteration number

        Returns:
            Complete iteration report, or None if not found
        """
        iteration = self._get_iteration(pilot_program_id, iteration_number)
        if not iteration:
            return None

        return {
            "iteration_info": {
                "number": iteration.number,
                "status": iteration.status.value,
                "progress_percentage": iteration.progress_percentage,
                "completion_score": iteration.completion_score,
                "is_on_track": iteration.is_on_track,
                "duration_days": iteration.duration_days,
            },
            "goals": [
                {
                    "id": goal.id,
                    "description": goal.description,
                    "category": goal.category,
                    "priority": goal.priority,
                    "completed": goal.is_completed,
                    "success_criteria": goal.success_criteria,
                }
                for goal in iteration.goals
            ],
            "feedback_summary": iteration.feedback_summary,
            "metrics": iteration.metrics_snapshot.dict() if iteration.metrics_snapshot else None,
            "outcomes": {
                "key_learnings": iteration.key_learnings,
                "action_items": iteration.action_items,
                "next_iteration_focus": iteration.next_iteration_focus,
                "blockers": iteration.blockers,
            },
            "timeline": {
                "planned_start": iteration.planned_start_date.isoformat(),
                "planned_end": iteration.planned_end_date.isoformat(),
                "actual_start": (
                    iteration.actual_start_date.isoformat() if iteration.actual_start_date else None
                ),
                "actual_end": (
                    iteration.actual_end_date.isoformat() if iteration.actual_end_date else None
                ),
            },
        }

    async def get_program_iteration_summary(self, pilot_program_id: str) -> Dict[str, Any]:
        """
        Generate summary of all iterations for a pilot program.

        Args:
            pilot_program_id: Pilot program identifier

        Returns:
            Summary of all iterations
        """
        if pilot_program_id not in self.iterations:
            return {"total_iterations": 0, "iterations": []}

        iterations = list(self.iterations[pilot_program_id].values())
        iterations.sort(key=lambda x: x.number)

        completed_iterations = [i for i in iterations if i.status == IterationStatus.COMPLETED]
        avg_completion_score = (
            sum(i.completion_score for i in completed_iterations) / len(completed_iterations)
            if completed_iterations
            else 0.0
        )

        # Calculate trends
        trends = {}
        if len(completed_iterations) >= 2:
            latest = completed_iterations[-1]
            previous = completed_iterations[-2]
            if latest.metrics_snapshot and previous.metrics_snapshot:
                trends = latest.metrics_snapshot.calculate_trends(previous.metrics_snapshot)

        return {
            "total_iterations": len(iterations),
            "completed_iterations": len(completed_iterations),
            "average_completion_score": avg_completion_score,
            "overall_progress": (
                sum(i.progress_percentage for i in iterations) / len(iterations)
                if iterations
                else 0.0
            ),
            "trends": trends,
            "iterations": [
                {
                    "number": i.number,
                    "status": i.status.value,
                    "progress": i.progress_percentage,
                    "completion_score": i.completion_score,
                    "is_on_track": i.is_on_track,
                }
                for i in iterations
            ],
        }

    def _get_iteration(
        self, pilot_program_id: str, iteration_number: int
    ) -> Optional[WeeklyIteration]:
        """Get a specific iteration."""
        if pilot_program_id not in self.iterations:
            return None
        return self.iterations[pilot_program_id].get(iteration_number)

    async def check_iteration_alerts(self, pilot_program_id: str) -> List[Dict[str, Any]]:
        """
        Check for alerts on iteration progress and health.

        Args:
            pilot_program_id: Pilot program identifier

        Returns:
            List of alerts requiring attention
        """
        alerts: List[Dict[str, Any]] = []

        if pilot_program_id not in self.iterations:
            return alerts

        iterations = self.iterations[pilot_program_id]
        now = datetime.utcnow()

        for iteration in iterations.values():
            if iteration.status == IterationStatus.IN_PROGRESS:
                # Check if iteration is behind schedule
                days_elapsed = (now - iteration.planned_start_date).days
                if days_elapsed > 7 and iteration.progress_percentage < 50:
                    alerts.append(
                        {
                            "type": "progress_alert",
                            "severity": "high",
                            "message": f"Iteration {iteration.number} is significantly behind schedule",
                            "iteration_number": iteration.number,
                            "current_progress": iteration.progress_percentage,
                            "days_elapsed": days_elapsed,
                        }
                    )

                # Check for blockers
                if iteration.blockers:
                    alerts.append(
                        {
                            "type": "blocker_alert",
                            "severity": "medium",
                            "message": f"Iteration {iteration.number} has {len(iteration.blockers)} active blockers",
                            "iteration_number": iteration.number,
                            "blockers": iteration.blockers,
                        }
                    )

                # Check feedback collection
                days_since_start = (
                    now - (iteration.actual_start_date or iteration.planned_start_date)
                ).days
                if days_since_start >= 5 and len(iteration.feedback_entries) == 0:
                    alerts.append(
                        {
                            "type": "feedback_alert",
                            "severity": "low",
                            "message": f"Iteration {iteration.number} has no feedback collected yet",
                            "iteration_number": iteration.number,
                            "days_since_start": days_since_start,
                        }
                    )

        return alerts
