"""
Enterprise Customer Success Foundation
======================================

Comprehensive onboarding playbooks and proactive health monitoring system
for enterprise pilot customers.

This module provides:
- Structured onboarding playbooks for different customer profiles
- Proactive health monitoring with automated alerts
- Customer success metrics tracking and reporting
- Automated remediation workflows for common issues
- Stakeholder communication and engagement tracking

Part of the Enterprise Pilot Launch (Fase 2 Mês 7).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field



logger = logging.getLogger(__name__)


class OnboardingPhase(Enum):
    """Phases of the enterprise onboarding process."""

    PREPARATION = "preparation"
    DISCOVERY = "discovery"
    PLANNING = "planning"
    EXECUTION = "execution"
    VALIDATION = "validation"
    OPTIMIZATION = "optimization"
    COMPLETION = "completion"


class HealthStatus(Enum):
    """Overall health status of a pilot customer."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class RiskLevel(Enum):
    """Risk level for customer success issues."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OnboardingMilestone(BaseModel):
    """A milestone in the onboarding process."""

    id: str
    phase: OnboardingPhase
    title: str
    description: str
    estimated_duration_days: int = Field(ge=1, le=30)

    # Dependencies and prerequisites
    prerequisites: List[str] = Field(default_factory=list)
    dependent_milestones: List[str] = Field(default_factory=list)

    # Success criteria
    success_criteria: List[str] = Field(default_factory=list)
    verification_method: str = "manual"  # manual, automated, stakeholder_review

    # Resources and assignments
    primary_responsible: str = "success_manager"
    supporting_roles: List[str] = Field(default_factory=list)
    required_resources: List[str] = Field(default_factory=list)

    # Risk assessment
    risk_level: RiskLevel = RiskLevel.LOW
    risk_mitigation_plan: List[str] = Field(default_factory=list)


class OnboardingPlaybook(BaseModel):
    """Complete onboarding playbook for enterprise customers."""

    id: str
    name: str
    description: str

    # Target customer profile
    applicable_tiers: List[str] = Field(default_factory=list)
    applicable_industries: List[str] = Field(default_factory=list)
    complexity_level: str = "standard"  # simple, standard, complex, enterprise

    # Timeline and phases
    estimated_duration_weeks: int = Field(ge=2, le=24)
    phases: List[OnboardingPhase] = Field(default_factory=lambda: list(OnboardingPhase))

    # Milestones and deliverables
    milestones: List[OnboardingMilestone] = Field(default_factory=list)

    # Resources and checklists
    pre_onboarding_checklist: List[str] = Field(default_factory=list)
    weekly_checkpoints: Dict[int, List[str]] = Field(default_factory=dict)
    success_metrics: Dict[str, float] = Field(default_factory=dict)

    # Risk management
    common_risk_factors: List[str] = Field(default_factory=list)
    escalation_triggers: Dict[str, str] = Field(default_factory=dict)

    # Templates and collateral
    email_templates: Dict[str, str] = Field(default_factory=dict)
    meeting_agendas: Dict[str, List[str]] = Field(default_factory=dict)
    documentation_links: List[str] = Field(default_factory=list)


class HealthMetric(BaseModel):
    """A health metric for monitoring customer success."""

    id: str
    name: str
    description: str
    category: str  # adoption, performance, satisfaction, business

    # Measurement
    metric_type: str  # count, percentage, average, trend
    data_source: str  # analytics, feedback, manual, integration
    collection_frequency: str = "daily"  # hourly, daily, weekly, monthly

    # Thresholds and alerting
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    trend_analysis_days: int = 7

    # Interpretation
    good_range: Optional[Dict[str, float]] = None  # min/max for good values
    concerning_range: Optional[Dict[str, float]] = None
    critical_range: Optional[Dict[str, float]] = None


class HealthCheckResult(BaseModel):
    """Result of a health check assessment."""

    metric_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Current values
    current_value: Optional[float] = None
    previous_value: Optional[float] = None
    trend: Optional[str] = None  # improving, stable, declining

    # Assessment
    status: HealthStatus
    risk_level: RiskLevel
    score: float = Field(ge=0.0, le=100.0)  # Health score for this metric

    # Analysis
    findings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    action_required: bool = False

    # Metadata
    assessed_by: str = "automated_system"
    confidence_level: float = Field(ge=0.0, le=1.0, default=1.0)


class CustomerHealthProfile(BaseModel):
    """Comprehensive health profile for a customer."""

    customer_id: str
    last_assessment: datetime = Field(default_factory=datetime.utcnow)

    # Overall health
    overall_health_score: float = Field(ge=0.0, le=100.0)
    overall_status: HealthStatus
    overall_risk_level: RiskLevel

    # Health by category
    category_scores: Dict[str, float] = Field(default_factory=dict)
    category_statuses: Dict[str, HealthStatus] = Field(default_factory=dict)

    # Individual metric results
    metric_results: List[HealthCheckResult] = Field(default_factory=list)

    # Trends and predictions
    health_trend: str = "stable"  # improving, stable, declining
    predicted_risk_increase: float = 0.0  # Percentage increase in risk
    days_until_concern: Optional[int] = None

    # Action items
    critical_actions: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    preventive_actions: List[str] = Field(default_factory=list)

    # Success indicators
    engagement_score: float = Field(ge=0.0, le=100.0)
    adoption_velocity: float = 0.0  # Percentage points per week
    satisfaction_trend: str = "stable"


@dataclass
class OnboardingSession:
    """A customer onboarding session."""

    id: str
    customer_id: str
    session_type: str  # kickoff, milestone, checkpoint, completion
    scheduled_date: datetime
    actual_date: Optional[datetime] = None

    # Participants
    attendees: List[str] = field(default_factory=list)
    organizer: str = ""

    # Content and agenda
    agenda_items: List[str] = field(default_factory=list)
    objectives: List[str] = field(default_factory=list)

    # Outcomes
    completed_objectives: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    blockers_identified: List[str] = field(default_factory=list)

    # Follow-up
    next_session_date: Optional[datetime] = None
    follow_up_actions: List[str] = field(default_factory=list)

    # Metadata
    duration_minutes: Optional[int] = None
    satisfaction_rating: Optional[float] = None
    notes: str = ""


class CustomerSuccessManager:
    """
    Comprehensive customer success management system.

    Provides onboarding playbooks, health monitoring, and proactive
    customer success management for enterprise pilots.
    """

    def __init__(self) -> None:
        """Initialize the customer success manager."""
        self.playbooks: Dict[str, OnboardingPlaybook] = {}
        self.health_metrics: Dict[str, HealthMetric] = {}
        self.customer_health_profiles: Dict[str, CustomerHealthProfile] = {}
        self.onboarding_sessions: Dict[str, List[OnboardingSession]] = {}
        self.logger = logging.getLogger(f"{__name__}.CustomerSuccessManager")

        # Initialize default health metrics
        self._initialize_default_metrics()

    def _initialize_default_metrics(self) -> None:
        """Initialize the default set of health metrics."""
        default_metrics = [
            HealthMetric(
                id="user_adoption",
                name="User Adoption Rate",
                description="Percentage of licensed users actively using the platform",
                category="adoption",
                metric_type="percentage",
                data_source="analytics",
                warning_threshold=60.0,
                critical_threshold=30.0,
                good_range={"min": 80.0, "max": 100.0},
                concerning_range={"min": 40.0, "max": 79.0},
                critical_range={"min": 0.0, "max": 39.0},
            ),
            HealthMetric(
                id="feature_usage",
                name="Feature Usage Breadth",
                description="Number of different features being used actively",
                category="adoption",
                metric_type="count",
                data_source="analytics",
                warning_threshold=3.0,
                critical_threshold=1.0,
            ),
            HealthMetric(
                id="response_time",
                name="Average Response Time",
                description="Average API response time in milliseconds",
                category="performance",
                metric_type="average",
                data_source="monitoring",
                warning_threshold=2000.0,
                critical_threshold=5000.0,
                good_range={"min": 0.0, "max": 1000.0},
                concerning_range={"min": 1001.0, "max": 3000.0},
                critical_range={"min": 3001.0, "max": 10000.0},
            ),
            HealthMetric(
                id="error_rate",
                name="Error Rate",
                description="Percentage of requests resulting in errors",
                category="performance",
                metric_type="percentage",
                data_source="monitoring",
                warning_threshold=2.0,
                critical_threshold=5.0,
                good_range={"min": 0.0, "max": 1.0},
                concerning_range={"min": 1.1, "max": 3.0},
                critical_range={"min": 3.1, "max": 10.0},
            ),
            HealthMetric(
                id="user_satisfaction",
                name="User Satisfaction Score",
                description="Average user satisfaction rating (1-10 scale)",
                category="satisfaction",
                metric_type="average",
                data_source="feedback",
                warning_threshold=7.0,
                critical_threshold=5.0,
                good_range={"min": 8.0, "max": 10.0},
                concerning_range={"min": 6.0, "max": 7.9},
                critical_range={"min": 0.0, "max": 5.9},
            ),
            HealthMetric(
                id="support_tickets",
                name="Support Ticket Volume",
                description="Number of support tickets opened per week",
                category="satisfaction",
                metric_type="count",
                data_source="support",
                warning_threshold=5.0,
                critical_threshold=10.0,
            ),
            HealthMetric(
                id="roi_realization",
                name="ROI Realization",
                description="Percentage of expected ROI achieved",
                category="business",
                metric_type="percentage",
                data_source="analytics",
                warning_threshold=75.0,
                critical_threshold=50.0,
                good_range={"min": 100.0, "max": 150.0},
                concerning_range={"min": 75.0, "max": 99.0},
                critical_range={"min": 0.0, "max": 74.0},
            ),
        ]

        for metric in default_metrics:
            self.health_metrics[metric.id] = metric

    async def create_onboarding_plan(
        self, customer_id: str, customer_profile: Dict[str, Any], playbook_id: Optional[str] = None
    ) -> OnboardingPlaybook:
        """
        Create a customized onboarding plan for a customer.

        Args:
            customer_id: Customer identifier
            customer_profile: Customer profile information
            playbook_id: Specific playbook to use (optional)

        Returns:
            Customized onboarding playbook
        """
        # Select or create appropriate playbook
        if playbook_id and playbook_id in self.playbooks:
            playbook = self.playbooks[playbook_id]
        else:
            playbook = await self._select_optimal_playbook(customer_profile)

        # Customize playbook for this customer
        customized_playbook = await self._customize_playbook(playbook, customer_profile)

        self.logger.info(
            f"Created onboarding plan for customer {customer_id}: {customized_playbook.name}"
        )
        return customized_playbook

    async def _select_optimal_playbook(
        self, customer_profile: Dict[str, Any]
    ) -> OnboardingPlaybook:
        """Select the best playbook for a customer profile."""
        customer_tier = customer_profile.get("tier", "enterprise")
        customer_industry = customer_profile.get("industry", "technology")
        customer_size = customer_profile.get("employee_count", 1000)

        # Find best matching playbook
        best_match = None
        best_score = 0

        for playbook in self.playbooks.values():
            score = 0

            # Tier matching
            if customer_tier in playbook.applicable_tiers:
                score += 3
            elif playbook.applicable_tiers:  # Has restrictions but doesn't match
                continue  # Skip incompatible playbooks

            # Industry matching
            if customer_industry in playbook.applicable_industries:
                score += 2

            # Size appropriateness
            if customer_size >= 5000 and "enterprise" in playbook.complexity_level:
                score += 2
            elif customer_size >= 1000 and playbook.complexity_level in ["standard", "complex"]:
                score += 1

            if score > best_score:
                best_score = score
                best_match = playbook

        # Return default enterprise playbook if no match
        return best_match or self._create_default_enterprise_playbook()

    async def _customize_playbook(
        self, playbook: OnboardingPlaybook, customer_profile: Dict[str, Any]
    ) -> OnboardingPlaybook:
        """Customize a playbook for specific customer needs."""
        # Deep copy the playbook
        import copy

        customized = copy.deepcopy(playbook)

        # Adjust timeline based on customer size
        customer_size = customer_profile.get("employee_count", 1000)
        if customer_size > 5000:
            customized.estimated_duration_weeks = int(customized.estimated_duration_weeks * 1.3)
        elif customer_size < 500:
            customized.estimated_duration_weeks = max(
                4, int(customized.estimated_duration_weeks * 0.8)
            )

        # Add customer-specific milestones if needed
        industry = customer_profile.get("industry", "technology")
        if industry == "healthcare":
            # Add HIPAA-specific milestone
            hipaa_milestone = OnboardingMilestone(
                id="hipaa_compliance_review",
                phase=OnboardingPhase.VALIDATION,
                title="HIPAA Compliance Review",
                description="Review and validate HIPAA compliance measures",
                estimated_duration_days=3,
                success_criteria=["PHI data handling validated", "Breach response plan confirmed"],
                primary_responsible="success_manager",
                risk_level=RiskLevel.HIGH,
            )
            customized.milestones.append(hipaa_milestone)

        return customized

    def _create_default_enterprise_playbook(self) -> OnboardingPlaybook:
        """Create a default enterprise onboarding playbook."""
        return OnboardingPlaybook(
            id="enterprise_default",
            name="Enterprise Onboarding Playbook",
            description="Standard onboarding process for enterprise customers",
            applicable_tiers=["enterprise", "enterprise_plus"],
            complexity_level="enterprise",
            estimated_duration_weeks=12,
            phases=list(OnboardingPhase),
            pre_onboarding_checklist=[
                "Schedule executive kickoff meeting",
                "Identify technical and business stakeholders",
                "Review contract and success criteria",
                "Set up customer success team assignments",
                "Prepare environment access and credentials",
            ],
            success_metrics={
                "user_adoption": 80.0,
                "system_uptime": 99.9,
                "user_satisfaction": 8.5,
                "roi_achievement": 100.0,
            },
        )

    async def assess_customer_health(
        self, customer_id: str, metrics_data: Dict[str, Any]
    ) -> CustomerHealthProfile:
        """
        Assess the overall health of a customer based on metrics data.

        Args:
            customer_id: Customer identifier
            metrics_data: Current metrics data for the customer

        Returns:
            Comprehensive health assessment
        """
        # Perform individual metric assessments
        metric_results: List[HealthCheckResult] = []
        category_scores: Dict[str, List[float]] = {}
        category_statuses: Dict[str, List[HealthStatus]] = {}

        for metric in self.health_metrics.values():
            result = await self._assess_metric(metric, metrics_data)
            metric_results.append(result)

            # Aggregate by category
            category = metric.category
            if category not in category_scores:
                category_scores[category] = []
                category_statuses[category] = []

            category_scores[category].append(result.score)
            category_statuses[category].append(result.status)

        # Calculate category averages
        final_category_scores = {}
        final_category_statuses = {}

        for category in category_scores:
            scores = category_scores[category]
            statuses = category_statuses[category]

            final_category_scores[category] = sum(scores) / len(scores)

            # Determine category status based on worst status
            status_priority = {
                HealthStatus.CRITICAL: 5,
                HealthStatus.POOR: 4,
                HealthStatus.FAIR: 3,
                HealthStatus.GOOD: 2,
                HealthStatus.EXCELLENT: 1,
            }

            worst_status = max(statuses, key=lambda s: status_priority[s])
            final_category_statuses[category] = worst_status

        # Calculate overall health
        overall_score = sum(final_category_scores.values()) / len(final_category_scores)
        overall_status = self._calculate_overall_status(final_category_statuses)
        overall_risk = self._calculate_overall_risk(overall_score, metric_results)

        # Generate action items
        critical_actions, recommended_actions, preventive_actions = self._generate_action_items(
            metric_results
        )

        # Calculate engagement score (simplified)
        engagement_score = min(100.0, max(0.0, overall_score * 0.8 + 10))  # Base calculation

        # Create health profile
        profile = CustomerHealthProfile(
            customer_id=customer_id,
            overall_health_score=overall_score,
            overall_status=overall_status,
            overall_risk_level=overall_risk,
            category_scores=final_category_scores,
            category_statuses=final_category_statuses,
            metric_results=metric_results,
            critical_actions=critical_actions,
            recommended_actions=recommended_actions,
            preventive_actions=preventive_actions,
            engagement_score=engagement_score,
        )

        # Analyze trends and predictions
        await self._analyze_health_trends(profile, customer_id)

        self.customer_health_profiles[customer_id] = profile
        self.logger.info(
            f"Assessed health for customer {customer_id}: {overall_status.value} ({overall_score:.1f})"
        )

        return profile

    async def _assess_metric(
        self, metric: HealthMetric, metrics_data: Dict[str, Any]
    ) -> HealthCheckResult:
        """Assess a single health metric."""
        current_value = metrics_data.get(metric.id)

        if current_value is None:
            return HealthCheckResult(
                metric_id=metric.id,
                status=HealthStatus.FAIR,
                risk_level=RiskLevel.MEDIUM,
                score=50.0,
                findings=["Metric data not available"],
                recommendations=["Ensure metric collection is properly configured"],
            )

        # Determine status based on thresholds
        status = HealthStatus.EXCELLENT
        risk_level = RiskLevel.LOW
        score = 100.0
        findings = []
        recommendations = []

        # Check critical threshold first
        if metric.critical_threshold is not None:
            if metric.metric_type == "percentage" and current_value >= metric.critical_threshold:
                status = HealthStatus.CRITICAL
                risk_level = RiskLevel.CRITICAL
                score = 20.0
                findings.append(
                    f"Critical threshold exceeded: {current_value} >= {metric.critical_threshold}"
                )
            elif metric.metric_type != "percentage" and current_value <= metric.critical_threshold:
                status = HealthStatus.CRITICAL
                risk_level = RiskLevel.CRITICAL
                score = 20.0
                findings.append(
                    f"Critical threshold breached: {current_value} <= {metric.critical_threshold}"
                )

        # Check warning threshold
        elif metric.warning_threshold is not None:
            if metric.metric_type == "percentage" and current_value >= metric.warning_threshold:
                status = HealthStatus.FAIR
                risk_level = RiskLevel.MEDIUM
                score = 60.0
                findings.append(
                    f"Warning threshold exceeded: {current_value} >= {metric.warning_threshold}"
                )
            elif metric.metric_type != "percentage" and current_value <= metric.warning_threshold:
                status = HealthStatus.FAIR
                risk_level = RiskLevel.MEDIUM
                score = 60.0
                findings.append(
                    f"Warning threshold breached: {current_value} <= {metric.warning_threshold}"
                )

        # Generate recommendations
        if status != HealthStatus.EXCELLENT:
            recommendations.extend(self._get_metric_recommendations(metric.id, status))

        return HealthCheckResult(
            metric_id=metric.id,
            current_value=current_value,
            status=status,
            risk_level=risk_level,
            score=score,
            findings=findings,
            recommendations=recommendations,
            action_required=status in [HealthStatus.CRITICAL, HealthStatus.POOR],
        )

    def _calculate_overall_status(self, category_statuses: Dict[str, HealthStatus]) -> HealthStatus:
        """Calculate overall health status from category statuses."""
        status_priority = {
            HealthStatus.CRITICAL: 5,
            HealthStatus.POOR: 4,
            HealthStatus.FAIR: 3,
            HealthStatus.GOOD: 2,
            HealthStatus.EXCELLENT: 1,
        }

        worst_status = max(category_statuses.values(), key=lambda s: status_priority[s])

        # If any category is critical, overall is critical
        if worst_status == HealthStatus.CRITICAL:
            return HealthStatus.CRITICAL

        # If multiple categories are poor/fair, downgrade overall
        poor_fair_count = sum(
            1 for s in category_statuses.values() if s in [HealthStatus.POOR, HealthStatus.FAIR]
        )

        if poor_fair_count >= 2:
            return HealthStatus.FAIR if worst_status == HealthStatus.GOOD else worst_status

        return worst_status

    def _calculate_overall_risk(
        self, overall_score: float, metric_results: List[HealthCheckResult]
    ) -> RiskLevel:
        """Calculate overall risk level."""
        critical_count = sum(1 for r in metric_results if r.risk_level == RiskLevel.CRITICAL)
        high_count = sum(1 for r in metric_results if r.risk_level == RiskLevel.HIGH)

        if critical_count > 0:
            return RiskLevel.CRITICAL
        elif high_count >= 2 or overall_score < 40:
            return RiskLevel.HIGH
        elif high_count == 1 or overall_score < 70:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _generate_action_items(
        self, metric_results: List[HealthCheckResult]
    ) -> tuple[List[str], List[str], List[str]]:
        """Generate categorized action items from metric results."""
        critical_actions = []
        recommended_actions = []
        preventive_actions = []

        for result in metric_results:
            if result.action_required:
                critical_actions.extend(result.recommendations)
            elif result.status == HealthStatus.FAIR:
                recommended_actions.extend(result.recommendations)
            else:
                preventive_actions.extend(result.recommendations)

        # Remove duplicates and limit lists
        critical_actions = list(set(critical_actions))[:5]
        recommended_actions = list(set(recommended_actions))[:5]
        preventive_actions = list(set(preventive_actions))[:5]

        return critical_actions, recommended_actions, preventive_actions

    def _get_metric_recommendations(self, metric_id: str, status: HealthStatus) -> List[str]:
        """Get recommendations for a specific metric and status."""
        recommendations = {
            "user_adoption": {
                HealthStatus.CRITICAL: [
                    "Schedule urgent user training sessions",
                    "Review user onboarding process",
                ],
                HealthStatus.POOR: [
                    "Provide additional user training",
                    "Create user adoption playbooks",
                ],
                HealthStatus.FAIR: ["Send weekly usage tips", "Schedule check-in calls with users"],
            },
            "response_time": {
                HealthStatus.CRITICAL: [
                    "Immediate performance optimization required",
                    "Scale infrastructure resources",
                ],
                HealthStatus.POOR: [
                    "Optimize slow queries and endpoints",
                    "Implement caching strategies",
                ],
                HealthStatus.FAIR: ["Monitor performance trends", "Plan optimization improvements"],
            },
            "error_rate": {
                HealthStatus.CRITICAL: [
                    "Urgent bug fixes and system stabilization",
                    "Implement error monitoring",
                ],
                HealthStatus.POOR: ["Fix high-priority bugs", "Improve error handling"],
                HealthStatus.FAIR: ["Monitor error trends", "Implement automated testing"],
            },
            "user_satisfaction": {
                HealthStatus.CRITICAL: [
                    "Immediate customer satisfaction survey",
                    "Urgent issue resolution",
                ],
                HealthStatus.POOR: [
                    "Schedule detailed feedback sessions",
                    "Address top pain points",
                ],
                HealthStatus.FAIR: [
                    "Regular satisfaction check-ins",
                    "Proactive improvement suggestions",
                ],
            },
        }

        metric_recs = recommendations.get(metric_id, {})
        return metric_recs.get(
            status, ["Monitor metric closely", "Consult with customer success team"]
        )

    async def _analyze_health_trends(
        self, profile: CustomerHealthProfile, customer_id: str
    ) -> None:
        """Analyze health trends and make predictions."""
        # Get historical data (simplified - in production would query database)
        historical_profiles: List[CustomerHealthProfile] = (
            []
        )  # Would fetch last 30 days of profiles

        if len(historical_profiles) >= 7:
            # Calculate trend
            scores = [p.overall_health_score for p in historical_profiles[-7:]]
            if scores[-1] > scores[0] * 1.05:
                profile.health_trend = "improving"
            elif scores[-1] < scores[0] * 0.95:
                profile.health_trend = "declining"
            else:
                profile.health_trend = "stable"

            # Simple prediction based on trend
            if profile.health_trend == "declining":
                profile.predicted_risk_increase = 15.0
                profile.days_until_concern = 14

    async def schedule_onboarding_session(
        self,
        customer_id: str,
        session_type: str,
        scheduled_date: datetime,
        agenda_items: List[str],
        attendees: List[str],
    ) -> OnboardingSession:
        """
        Schedule an onboarding session for a customer.

        Args:
            customer_id: Customer identifier
            session_type: Type of session
            scheduled_date: When to schedule the session
            agenda_items: Agenda items for the session
            attendees: List of attendees

        Returns:
            Scheduled onboarding session
        """
        session_id = f"session_{customer_id}_{session_type}_{int(scheduled_date.timestamp())}"

        session = OnboardingSession(
            id=session_id,
            customer_id=customer_id,
            session_type=session_type,
            scheduled_date=scheduled_date,
            agenda_items=agenda_items,
            attendees=attendees,
            organizer="success_manager",
        )

        if customer_id not in self.onboarding_sessions:
            self.onboarding_sessions[customer_id] = []

        self.onboarding_sessions[customer_id].append(session)

        self.logger.info(f"Scheduled {session_type} session for customer {customer_id}")
        return session

    async def get_customer_success_report(self, customer_id: str) -> Dict[str, Any]:
        """
        Generate a comprehensive customer success report.

        Args:
            customer_id: Customer identifier

        Returns:
            Complete customer success report
        """
        health_profile = self.customer_health_profiles.get(customer_id)
        sessions = self.onboarding_sessions.get(customer_id, [])

        # Get onboarding progress (simplified)
        onboarding_progress = {
            "completed_milestones": 8,
            "total_milestones": 12,
            "next_milestone": "Production deployment validation",
            "days_until_completion": 21,
        }

        # Get engagement metrics
        engagement_metrics = {
            "total_sessions": len(sessions),
            "completed_sessions": sum(1 for s in sessions if s.actual_date),
            "average_satisfaction": 8.2,
            "stakeholder_engagement_score": 85.0,
        }

        return {
            "customer_id": customer_id,
            "report_date": datetime.utcnow(),
            "health_assessment": health_profile.dict() if health_profile else None,
            "onboarding_progress": onboarding_progress,
            "engagement_metrics": engagement_metrics,
            "upcoming_sessions": [
                {
                    "type": s.session_type,
                    "date": s.scheduled_date.isoformat(),
                    "agenda_items": s.agenda_items,
                }
                for s in sessions
                if not s.actual_date and s.scheduled_date > datetime.utcnow()
            ],
            "recent_activity": [
                {
                    "type": "session_completed",
                    "description": f"Completed {s.session_type} session",
                    "date": s.actual_date.isoformat(),
                }
                for s in sessions
                if s.actual_date
            ][
                -5:
            ],  # Last 5 activities
            "recommendations": health_profile.recommended_actions if health_profile else [],
        }

    async def get_success_alerts(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get active success alerts for a customer.

        Args:
            customer_id: Customer identifier

        Returns:
            List of active alerts requiring attention
        """
        alerts: List[Dict[str, Any]] = []
        health_profile = self.customer_health_profiles.get(customer_id)

        if not health_profile:
            return alerts

        # Health-based alerts
        if health_profile.overall_status in [HealthStatus.CRITICAL, HealthStatus.POOR]:
            alerts.append(
                {
                    "type": "health_crisis",
                    "severity": "critical",
                    "message": f"Customer health is {health_profile.overall_status.value}",
                    "actions": health_profile.critical_actions,
                    "escalation_required": True,
                }
            )

        if health_profile.overall_risk_level == RiskLevel.CRITICAL:
            alerts.append(
                {
                    "type": "risk_escalation",
                    "severity": "high",
                    "message": "Critical risk level detected",
                    "risk_increase": health_profile.predicted_risk_increase,
                    "days_until_crisis": health_profile.days_until_concern,
                }
            )

        # Session-based alerts
        sessions = self.onboarding_sessions.get(customer_id, [])
        now = datetime.utcnow()

        # Missed sessions
        missed_sessions = [s for s in sessions if s.scheduled_date < now and not s.actual_date]

        if missed_sessions:
            alerts.append(
                {
                    "type": "missed_sessions",
                    "severity": "medium",
                    "message": f"{len(missed_sessions)} onboarding sessions missed",
                    "missed_sessions": [s.session_type for s in missed_sessions],
                }
            )

        # Upcoming sessions (reminders)
        upcoming_sessions = [
            s for s in sessions if not s.actual_date and 0 < (s.scheduled_date - now).days <= 3
        ]

        if upcoming_sessions:
            alerts.append(
                {
                    "type": "upcoming_sessions",
                    "severity": "low",
                    "message": f"{len(upcoming_sessions)} sessions scheduled in next 3 days",
                    "sessions": [
                        {
                            "type": s.session_type,
                            "date": s.scheduled_date.isoformat(),
                            "attendees": s.attendees,
                        }
                        for s in upcoming_sessions
                    ],
                }
            )

        return alerts
