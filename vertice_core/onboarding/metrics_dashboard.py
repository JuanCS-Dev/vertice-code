"""
Success Metrics Dashboard for Enterprise Pilots
===============================================

Real-time monitoring and analytics for pilot program success.

This module provides comprehensive metrics tracking including:
- Pilot satisfaction and adoption rates
- Feature usage analytics
- SLA compliance monitoring
- Expansion opportunity identification
- Churn risk assessment

Part of the Enterprise Foundation (Fase 2: Pilot Preparation).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any
from datetime import datetime, timedelta
from enum import Enum

from pydantic import BaseModel, Field

from ..billing.analytics import AnalyticsEngine


logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics tracked for pilots."""

    SATISFACTION = "satisfaction"
    ADOPTION = "adoption"
    USAGE = "usage"
    PERFORMANCE = "performance"
    EXPANSION = "expansion"
    CHURN_RISK = "churn_risk"


class SLAStatus(Enum):
    """SLA compliance status."""

    COMPLIANT = "compliant"
    WARNING = "warning"
    BREACHED = "breached"


@dataclass
class PilotMetrics:
    """
    Comprehensive metrics for pilot program success tracking.

    All metrics are calculated in real-time from usage data and feedback.
    """

    tenant_id: str
    period_start: datetime
    period_end: datetime

    # Core success metrics (0-100 scale)
    satisfaction_score: float = 0.0
    adoption_rate: float = 0.0
    feature_usage_depth: float = 0.0

    # Usage metrics
    active_users: int = 0
    total_sessions: int = 0
    ai_tokens_used: int = 0
    api_calls_made: int = 0

    # Performance metrics
    average_response_time_ms: float = 0.0
    error_rate_percentage: float = 0.0
    uptime_percentage: float = 100.0

    # Business metrics
    expansion_opportunities: int = 0
    churn_risk_score: float = 0.0
    support_tickets: int = 0

    # Feature-specific usage
    feature_usage: Dict[str, float] = field(default_factory=dict)

    # SLA compliance
    sla_status: SLAStatus = SLAStatus.COMPLIANT
    sla_breaches: List[str] = field(default_factory=list)

    def calculate_overall_score(self) -> float:
        """
        Calculate overall pilot success score (0-100).

        Combines satisfaction, adoption, and performance metrics.
        """
        weights = {"satisfaction": 0.4, "adoption": 0.3, "performance": 0.3}

        satisfaction_component = self.satisfaction_score
        adoption_component = self.adoption_rate
        performance_component = (self.uptime_percentage + (100 - self.error_rate_percentage)) / 2

        overall = (
            weights["satisfaction"] * satisfaction_component
            + weights["adoption"] * adoption_component
            + weights["performance"] * performance_component
        )

        return min(100.0, max(0.0, overall))

    def get_recommendations(self) -> List[str]:
        """
        Generate actionable recommendations based on current metrics.

        Returns:
            List of prioritized recommendations for success manager.
        """
        recommendations = []

        if self.satisfaction_score < 70:
            recommendations.append("Schedule customer feedback session to identify pain points")

        if self.adoption_rate < 60:
            recommendations.append("Provide additional training on underutilized features")

        if self.error_rate_percentage > 5:
            recommendations.append("Investigate and resolve high error rates")

        if self.churn_risk_score > 70:
            recommendations.append("Immediate intervention: high churn risk detected")

        if self.expansion_opportunities > 0:
            recommendations.append(
                f"Explore {self.expansion_opportunities} identified expansion opportunities"
            )

        if not recommendations:
            recommendations.append("Pilot performing well - continue monitoring")

        return recommendations


class DashboardConfig(BaseModel):
    """Configuration for pilot metrics dashboard."""

    tenant_id: str
    refresh_interval_minutes: int = Field(default=15, ge=5, le=60)
    alert_thresholds: Dict[str, float] = Field(default_factory=dict)
    notification_channels: List[str] = Field(default_factory=lambda: ["email"])

    def __init__(self, **data: Any):
        super().__init__(**data)
        # Set default alert thresholds if not provided
        if not self.alert_thresholds:
            self.alert_thresholds = {
                "satisfaction_score": 70.0,
                "adoption_rate": 60.0,
                "error_rate_percentage": 5.0,
                "churn_risk_score": 70.0,
                "uptime_percentage": 99.5,
            }


class PilotMetricsDashboard:
    """
    Real-time metrics dashboard for enterprise pilot monitoring.

    Provides comprehensive analytics and alerting for pilot success tracking.
    """

    def __init__(self, analytics_engine: AnalyticsEngine, config: DashboardConfig):
        """
        Initialize the metrics dashboard.

        Args:
            analytics_engine: Analytics engine for data collection.
            config: Dashboard configuration.
        """
        self.analytics = analytics_engine
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.PilotMetricsDashboard")
        self._alerts_sent: Dict[str, datetime] = {}

    async def get_current_metrics(self) -> PilotMetrics:
        """
        Retrieve current metrics for the pilot tenant.

        Returns:
            Comprehensive pilot metrics snapshot.
        """
        try:
            # Calculate period (last 30 days for meaningful metrics)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)

            # Gather metrics from various sources
            usage_data = await self.analytics.get_tenant_usage(
                tenant_id=self.config.tenant_id, start_date=start_date, end_date=end_date
            )

            feedback_data = await self.analytics.get_tenant_feedback(
                tenant_id=self.config.tenant_id, start_date=start_date
            )

            performance_data = await self.analytics.get_tenant_performance(
                tenant_id=self.config.tenant_id, start_date=start_date, end_date=end_date
            )

            # Calculate derived metrics
            satisfaction_score = self._calculate_satisfaction_score(feedback_data)
            adoption_rate = self._calculate_adoption_rate(usage_data)
            feature_usage = self._calculate_feature_usage(usage_data)

            # Calculate performance metrics
            avg_response_time = performance_data.get("avg_response_time_ms", 0.0)
            error_rate = performance_data.get("error_rate_percentage", 0.0)
            uptime = performance_data.get("uptime_percentage", 100.0)

            # Calculate business metrics
            expansion_opportunities = await self._identify_expansion_opportunities(usage_data)
            churn_risk = self._calculate_churn_risk(usage_data, feedback_data)

            # Check SLA compliance
            sla_status, sla_breaches = await self._check_sla_compliance()

            metrics = PilotMetrics(
                tenant_id=self.config.tenant_id,
                period_start=start_date,
                period_end=end_date,
                satisfaction_score=satisfaction_score,
                adoption_rate=adoption_rate,
                feature_usage_depth=(
                    sum(feature_usage.values()) / len(feature_usage) if feature_usage else 0.0
                ),
                active_users=usage_data.get("active_users", 0),
                total_sessions=usage_data.get("total_sessions", 0),
                ai_tokens_used=usage_data.get("ai_tokens_used", 0),
                api_calls_made=usage_data.get("api_calls_made", 0),
                average_response_time_ms=avg_response_time,
                error_rate_percentage=error_rate,
                uptime_percentage=uptime,
                expansion_opportunities=expansion_opportunities,
                churn_risk_score=churn_risk,
                support_tickets=usage_data.get("support_tickets", 0),
                feature_usage=feature_usage,
                sla_status=sla_status,
                sla_breaches=sla_breaches,
            )

            # Check for alerts
            await self._check_alerts(metrics)

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to retrieve metrics for {self.config.tenant_id}: {e}")
            raise

    async def get_metrics_history(self, days: int = 90) -> List[PilotMetrics]:
        """
        Retrieve historical metrics for trend analysis.

        Args:
            days: Number of days of history to retrieve.

        Returns:
            List of historical metrics snapshots.
        """
        history = []
        end_date = datetime.utcnow()

        # Get metrics for each week in the period
        for i in range(0, days, 7):
            start_date = end_date - timedelta(days=7)

            try:
                # Create a snapshot for this historical period
                # In production, this would query historical data
                metrics = PilotMetrics(
                    tenant_id=self.config.tenant_id,
                    period_start=start_date,
                    period_end=end_date,
                    satisfaction_score=75.0,  # Placeholder historical data
                    adoption_rate=65.0,
                    active_users=20,
                    total_sessions=120,
                )
                history.append(metrics)
            except Exception as e:
                self.logger.warning(
                    f"Could not retrieve metrics for period {start_date} to {end_date}: {e}"
                )
            finally:
                end_date = start_date

        return history

    def _calculate_satisfaction_score(self, feedback_data: Dict[str, Any]) -> float:
        """Calculate satisfaction score from feedback data."""
        if not feedback_data:
            return 50.0  # Neutral default

        # Simple weighted average of NPS and CSAT
        nps_score = float(feedback_data.get("nps", 0))  # -100 to 100
        csat_score = float(feedback_data.get("csat", 0.5)) * 100  # 0-1 to 0-100

        # Weight NPS more heavily for enterprise
        satisfaction = (nps_score + 100) / 2 * 0.7 + csat_score * 0.3
        return min(100.0, max(0.0, satisfaction))

    def _calculate_adoption_rate(self, usage_data: Dict[str, Any]) -> float:
        """Calculate feature adoption rate."""
        total_features = 20  # Expected total features
        used_features = len(usage_data.get("features_used", []))

        if total_features == 0:
            return 0.0

        return (used_features / total_features) * 100.0

    def _calculate_feature_usage(self, usage_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate usage percentage for each feature."""
        feature_usage = usage_data.get("feature_usage", {})
        total_usage = sum(feature_usage.values())

        if total_usage == 0:
            return {}

        return {feature: (usage / total_usage) * 100.0 for feature, usage in feature_usage.items()}

    async def _identify_expansion_opportunities(self, usage_data: Dict[str, Any]) -> int:
        """Identify potential expansion opportunities."""
        opportunities = 0

        # Check for high usage patterns indicating expansion potential
        if usage_data.get("active_users", 0) > 50:
            opportunities += 1

        if usage_data.get("ai_tokens_used", 0) > 100000:
            opportunities += 1

        if len(usage_data.get("integrations_used", [])) > 3:
            opportunities += 1

        return opportunities

    def _calculate_churn_risk(
        self, usage_data: Dict[str, Any], feedback_data: Dict[str, Any]
    ) -> float:
        """Calculate churn risk score based on usage and feedback patterns."""
        risk_factors = []

        # Low usage patterns
        if usage_data.get("active_users", 0) < 5:
            risk_factors.append(30)

        if usage_data.get("total_sessions", 0) < 10:
            risk_factors.append(25)

        # Poor feedback
        if feedback_data.get("nps", 0) < -30:
            risk_factors.append(40)

        if feedback_data.get("csat", 0.5) < 0.3:
            risk_factors.append(35)

        # Recent decrease in usage
        usage_trend = usage_data.get("usage_trend", 0)
        if usage_trend < -20:  # 20% decrease
            risk_factors.append(20)

        # Calculate overall risk
        if not risk_factors:
            return 10.0  # Low base risk

        return min(100.0, sum(risk_factors) / len(risk_factors))

    async def _check_sla_compliance(self) -> tuple[SLAStatus, List[str]]:
        """Check SLA compliance status."""
        # Implementation would check actual SLA metrics
        # For now, return compliant status
        return SLAStatus.COMPLIANT, []

    async def _check_alerts(self, metrics: PilotMetrics) -> None:
        """Check metrics against thresholds and send alerts if needed."""
        alerts_triggered = []

        # Check each threshold
        for metric_name, threshold in self.config.alert_thresholds.items():
            current_value = getattr(metrics, metric_name, 0)

            # Determine if alert condition is met
            should_alert = False
            if metric_name in ["satisfaction_score", "adoption_rate", "uptime_percentage"]:
                should_alert = current_value < threshold
            elif metric_name in ["error_rate_percentage", "churn_risk_score"]:
                should_alert = current_value > threshold

            if should_alert:
                alert_key = f"{metric_name}_{current_value:.1f}"
                last_sent = self._alerts_sent.get(alert_key)

                # Only send alert if not sent in last 24 hours
                if not last_sent or (datetime.utcnow() - last_sent) > timedelta(hours=24):
                    alerts_triggered.append(
                        f"{metric_name}: {current_value:.1f} (threshold: {threshold})"
                    )
                    self._alerts_sent[alert_key] = datetime.utcnow()

        if alerts_triggered:
            await self._send_alerts(alerts_triggered, metrics)

    async def _send_alerts(self, alerts: List[str], metrics: PilotMetrics) -> None:
        """Send alerts through configured channels."""
        alert_message = f"""
Pilot Metrics Alert for {metrics.tenant_id}

The following metrics are outside acceptable thresholds:
{chr(10).join(f"- {alert}" for alert in alerts)}

Overall Score: {metrics.calculate_overall_score():.1f}/100
Recommendations:
{chr(10).join(f"- {rec}" for rec in metrics.get_recommendations())}

View full dashboard: https://app.vertice.ai/pilot/{metrics.tenant_id}/metrics
"""

        # Send through configured channels
        for channel in self.config.notification_channels:
            if channel == "email":
                await self._send_email_alert(alert_message)
            elif channel == "slack":
                await self._send_slack_alert(alert_message)
            # Add other channels as needed

    async def _send_email_alert(self, message: str) -> None:
        """Send alert via email."""
        # Implementation would integrate with email service
        self.logger.warning(f"Email alert triggered: {message[:100]}...")

    async def _send_slack_alert(self, message: str) -> None:
        """Send alert via Slack."""
        # Implementation would integrate with Slack API
        self.logger.warning(f"Slack alert triggered: {message[:100]}...")
