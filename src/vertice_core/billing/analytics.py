"""
Enterprise Analytics Engine - Real-time analytics for enterprise dashboards.

Provides comprehensive analytics including usage metrics, AI performance,
revenue analytics, and predictive insights for enterprise customers.
"""

import asyncio
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .types import AnalyticsMetrics, UsageRecord, UsageType


class AnalyticsEngine:
    """
    Real-time analytics engine for enterprise usage tracking and insights.

    Provides comprehensive analytics including:
    - Real-time usage dashboards
    - AI performance metrics
    - Revenue analytics
    - Predictive insights
    """

    def __init__(self, retention_days: int = 90):
        """
        Initialize analytics engine.

        Args:
            retention_days: How long to retain detailed usage data
        """
        self.retention_days = retention_days

        # In-memory storage (in production, this would be a time-series database)
        self.usage_records: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.performance_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.revenue_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Real-time caches
        self.current_metrics: Dict[str, AnalyticsMetrics] = {}
        self.last_updated: Dict[str, float] = {}

    async def record_usage(self, record: UsageRecord) -> None:
        """
        Record usage event for analytics.

        Args:
            record: Usage record to store
        """
        tenant_id = record.tenant_id

        # Store usage record
        self.usage_records[tenant_id].append(record)

        # Update real-time metrics
        await self._update_realtime_metrics(tenant_id)

        # Clean old data
        self._cleanup_old_data()

    async def record_performance(
        self,
        tenant_id: str,
        agent_type: str,
        response_time_ms: float,
        success: bool,
        tokens_used: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record AI performance metrics.

        Args:
            tenant_id: Tenant identifier
            agent_type: Type of agent used
            response_time_ms: Response time in milliseconds
            success: Whether the operation succeeded
            tokens_used: AI tokens consumed
            metadata: Additional performance data
        """
        perf_record = {
            "timestamp": time.time(),
            "agent_type": agent_type,
            "response_time_ms": response_time_ms,
            "success": success,
            "tokens_used": tokens_used,
            "metadata": metadata or {},
        }

        self.performance_metrics[tenant_id].append(perf_record)
        await self._update_realtime_metrics(tenant_id)

    def get_analytics(self, tenant_id: str, period: str = "monthly") -> AnalyticsMetrics:
        """
        Get comprehensive analytics for a tenant.

        Args:
            tenant_id: Tenant identifier
            period: Time period ("daily", "weekly", "monthly")

        Returns:
            Complete analytics metrics
        """
        if tenant_id not in self.current_metrics:
            # Return empty metrics if no data
            return AnalyticsMetrics(tenant_id=tenant_id, period=period)

        return self.current_metrics[tenant_id]

    async def get_dashboard_data(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get dashboard-ready analytics data.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dashboard-formatted analytics data
        """
        metrics = self.get_analytics(tenant_id)
        return metrics.to_dashboard_format()

    async def get_usage_trends(
        self, tenant_id: str, usage_type: UsageType, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get usage trends over time.

        Args:
            tenant_id: Tenant identifier
            usage_type: Type of usage to analyze
            days: Number of days to look back

        Returns:
            Daily usage data points
        """
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        daily_usage: Dict[str, int] = defaultdict(int)

        for record in self.usage_records[tenant_id]:
            if record.timestamp.timestamp() >= cutoff_time and record.usage_type == usage_type:
                day_key = record.timestamp.strftime("%Y-%m-%d")
                daily_usage[day_key] += record.quantity

        # Convert to sorted list
        return [{"date": date, "usage": usage} for date, usage in sorted(daily_usage.items())]

    async def get_performance_insights(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get AI performance insights and recommendations.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Performance insights and recommendations
        """
        perf_data = list(self.performance_metrics[tenant_id])

        if not perf_data:
            return {"insights": [], "recommendations": []}

        # Analyze performance patterns
        insights: List[str] = []
        recommendations: List[str] = []

        # Response time analysis
        response_times = [p["response_time_ms"] for p in perf_data]
        avg_response_time = sum(response_times) / len(response_times)

        if avg_response_time > 5000:  # 5 seconds
            insights.append("High average response time detected")
            recommendations.append("Consider upgrading to Enterprise tier for better performance")
        elif avg_response_time > 2000:  # 2 seconds
            insights.append("Moderate response time - room for optimization")
            recommendations.append("Monitor agent performance during peak hours")

        # Success rate analysis
        total_requests = len(perf_data)
        successful_requests = sum(1 for p in perf_data if p["success"])
        success_rate = (successful_requests / total_requests) * 100

        if success_rate < 95:
            insights.append(f"Success rate: {success_rate:.1f}% - below optimal")
            recommendations.append("Review error patterns and agent configurations")
        elif success_rate < 99:
            insights.append(f"Success rate: {success_rate:.1f}% - good but improvable")
            recommendations.append("Monitor for intermittent failures")

        # Agent usage analysis
        agent_usage: Dict[str, int] = defaultdict(int)
        for p in perf_data:
            agent_usage[p["agent_type"]] += 1

        top_agent = max(agent_usage.items(), key=lambda x: x[1])
        insights.append(f"Most used agent: {top_agent[0]} ({top_agent[1]} requests)")

        return {
            "insights": insights,
            "recommendations": recommendations,
            "metrics": {
                "avg_response_time_ms": avg_response_time,
                "success_rate_percent": success_rate,
                "total_requests": total_requests,
                "agent_usage": dict(agent_usage),
            },
        }

    async def generate_predictive_insights(self, tenant_id: str) -> Dict[str, Any]:
        """
        Generate predictive analytics for usage forecasting.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Predictive insights including churn risk and expansion potential
        """
        # Simple predictive model based on recent usage patterns
        recent_usage = list(self.usage_records[tenant_id])[-30:]  # Last 30 records

        if len(recent_usage) < 7:  # Need at least a week of data
            return {
                "churn_risk": 50.0,  # Neutral
                "expansion_potential": 50.0,  # Neutral
                "confidence": "low",
                "reasoning": "Insufficient data for predictions",
            }

        # Calculate usage trends
        daily_usage: Dict[str, Dict[UsageType, int]] = defaultdict(lambda: defaultdict(int))
        for record in recent_usage:
            day_key = record.timestamp.strftime("%Y-%m-%d")
            daily_usage[day_key][record.usage_type] += record.quantity

        # Simple trend analysis
        days = sorted(daily_usage.keys())[-7:]  # Last 7 days
        usage_trends = {}

        for usage_type in UsageType:
            values = [daily_usage[day].get(usage_type, 0) for day in days]
            if values:
                avg_recent = sum(values[-3:]) / 3  # Last 3 days
                avg_earlier = sum(values[:-3]) / max(1, len(values) - 3)  # Earlier days
                trend = ((avg_recent - avg_earlier) / max(1, avg_earlier)) * 100
                usage_trends[usage_type] = trend

        # Calculate churn risk (simplified model)
        churn_indicators = [
            usage_trends.get(UsageType.AI_TOKENS, 0) < -20,  # 20% usage decline
            usage_trends.get(UsageType.ACTIVE_USERS, 0) < -10,  # 10% user decline
            len(days) < 5,  # Less than 5 days of activity
        ]

        churn_risk = min(100, sum(churn_indicators) * 30 + 10)  # Scale to 0-100

        # Calculate expansion potential (simplified model)
        expansion_indicators = [
            usage_trends.get(UsageType.AI_TOKENS, 0) > 25,  # 25% usage growth
            usage_trends.get(UsageType.ACTIVE_USERS, 0) > 15,  # 15% user growth
            usage_trends.get(UsageType.STORAGE_GB, 0) > 20,  # Storage growth
        ]

        expansion_potential = min(100, sum(expansion_indicators) * 25 + 20)  # Scale to 0-100

        return {
            "churn_risk": churn_risk,
            "expansion_potential": expansion_potential,
            "confidence": "medium" if len(days) >= 14 else "low",
            "usage_trends": {k.value: v for k, v in usage_trends.items()},
            "reasoning": f"Based on {len(days)} days of usage data",
        }

    async def _update_realtime_metrics(self, tenant_id: str) -> None:
        """Update real-time metrics cache for a tenant."""
        # Aggregate usage data
        usage_summary: Dict[UsageType, int] = defaultdict(int)
        for record in self.usage_records[tenant_id]:
            usage_summary[record.usage_type] += record.quantity

        # Aggregate performance data
        perf_data = list(self.performance_metrics[tenant_id])
        if perf_data:
            total_response_time = sum(p["response_time_ms"] for p in perf_data)
            successful_requests = sum(1 for p in perf_data if p["success"])
            total_tokens = sum(p.get("tokens_used", 0) for p in perf_data)

            avg_response_time = total_response_time / len(perf_data)
            success_rate = (successful_requests / len(perf_data)) * 100
        else:
            avg_response_time = 0.0
            success_rate = 100.0
            total_tokens = 0

        # Get predictive insights
        predictive_data = await self.generate_predictive_insights(tenant_id)

        # Create metrics object
        metrics = AnalyticsMetrics(
            tenant_id=tenant_id,
            period="monthly",
            total_ai_tokens=usage_summary[UsageType.AI_TOKENS],
            total_api_calls=usage_summary[UsageType.API_CALLS],
            active_users=usage_summary[UsageType.ACTIVE_USERS],
            storage_used_gb=usage_summary[UsageType.STORAGE_GB],
            avg_response_time_ms=avg_response_time,
            success_rate_percent=success_rate,
            agent_execution_count=usage_summary[UsageType.AGENT_EXECUTIONS],
            churn_risk_score=predictive_data["churn_risk"],
            expansion_opportunity_score=predictive_data["expansion_potential"],
        )

        # Update agent performance metrics
        agent_perf = defaultdict(
            lambda: {"requests": 0, "success_rate": 100.0, "avg_response_time": 0.0}
        )
        for record in perf_data:
            agent = record["agent_type"]
            agent_perf[agent]["requests"] += 1
            if record["success"]:
                agent_perf[agent]["success_rate"] = (
                    agent_perf[agent]["success_rate"] * (agent_perf[agent]["requests"] - 1) + 100
                ) / agent_perf[agent]["requests"]
            else:
                agent_perf[agent]["success_rate"] = (
                    agent_perf[agent]["success_rate"] * (agent_perf[agent]["requests"] - 1)
                ) / agent_perf[agent]["requests"]
            agent_perf[agent]["avg_response_time"] = (
                agent_perf[agent]["avg_response_time"] * (agent_perf[agent]["requests"] - 1)
                + record["response_time_ms"]
            ) / agent_perf[agent]["requests"]

        metrics.agent_performance = dict(agent_perf)

        # Update cache
        self.current_metrics[tenant_id] = metrics
        self.last_updated[tenant_id] = time.time()

    def _cleanup_old_data(self) -> None:
        """Clean up old usage records beyond retention period."""
        cutoff_time = time.time() - (self.retention_days * 24 * 60 * 60)

        for tenant_records in self.usage_records.values():
            # Remove old records from deque
            while tenant_records and tenant_records[0].timestamp.timestamp() < cutoff_time:
                tenant_records.popleft()


__all__ = ["AnalyticsEngine"]
