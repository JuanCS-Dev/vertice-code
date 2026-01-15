"""
Enterprise Health Monitoring System
===================================

Proactive monitoring and alerting for enterprise pilot health.

This module provides:
- Automated health metric collection
- Risk assessment and alerting
- Trend analysis and prediction
- Automated remediation recommendations

Part of the Customer Success Foundation.
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


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
    engagement_score: float = Field(ge=0.0, le=100.0, default=0.0)
    adoption_velocity: float = 0.0  # Percentage points per week
    satisfaction_trend: str = "stable"


class HealthMonitoringEngine:
    """
    Automated health monitoring engine for enterprise pilots.

    Continuously monitors customer health and provides proactive
    alerts and recommendations.
    """

    def __init__(self) -> None:
        """Initialize the health monitoring engine."""
        self.metrics: Dict[str, HealthMetric] = {}
        self.customer_profiles: Dict[str, CustomerHealthProfile] = {}
        self.logger = logging.getLogger(f"{__name__}.HealthMonitoringEngine")

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
            self.metrics[metric.id] = metric

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
        metric_results = []
        category_scores = {}
        category_statuses = {}

        for metric in self.metrics.values():
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

        # Calculate engagement score
        engagement_score = min(100.0, max(0.0, overall_score * 0.8 + 10))

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

        self.customer_profiles[customer_id] = profile
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

    async def get_health_alerts(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get active health alerts for a customer.

        Args:
            customer_id: Customer identifier

        Returns:
            List of active alerts requiring attention
        """
        alerts: List[Dict[str, Any]] = []
        profile = self.customer_profiles.get(customer_id)

        if not profile:
            return alerts

        # Health-based alerts
        if profile.overall_status in [HealthStatus.CRITICAL, HealthStatus.POOR]:
            alerts.append(
                {
                    "type": "health_crisis",
                    "severity": "critical",
                    "message": f"Customer health is {profile.overall_status.value}",
                    "actions": profile.critical_actions,
                    "escalation_required": True,
                }
            )

        if profile.overall_risk_level == RiskLevel.CRITICAL:
            alerts.append(
                {
                    "type": "risk_escalation",
                    "severity": "high",
                    "message": "Critical risk level detected",
                    "risk_increase": profile.predicted_risk_increase,
                    "days_until_crisis": profile.days_until_concern,
                }
            )

        return alerts
