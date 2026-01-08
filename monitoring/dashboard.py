"""
Production Monitoring Dashboard for Vertice-Code.

Real-time monitoring, alerting, and observability for production deployments.
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import logging
from datetime import datetime, timedelta

# Import our monitoring systems
from vertice_tui.core.logging import get_system_logger
from vertice_tui.core.error_tracking import get_error_tracker
from vertice_tui.core.bridge import get_bridge
from vertice_tui.core.http_pool import get_http_pool
from vertice_tui.core.caching import get_llm_cache, get_api_cache

logger = get_system_logger()


@dataclass
class AlertRule:
    """Alert rule configuration."""

    name: str
    condition: str  # Python expression to evaluate
    severity: str  # 'info', 'warning', 'error', 'critical'
    message: str
    cooldown_minutes: int = 5
    last_triggered: Optional[float] = None

    def should_trigger(self, metrics: Dict[str, Any]) -> bool:
        """Check if alert should trigger."""
        try:
            # Safe evaluation of condition
            allowed_names = {
                "metrics": metrics,
                "len": len,
                "sum": sum,
                "max": max,
                "min": min,
                "avg": lambda x: sum(x) / len(x) if x else 0,
            }

            # Evaluate condition safely
            result = eval(self.condition, {"__builtins__": {}}, allowed_names)

            # Check cooldown
            if self.last_triggered:
                cooldown_end = self.last_triggered + (self.cooldown_minutes * 60)
                if time.time() < cooldown_end:
                    return False

            return bool(result)

        except Exception as e:
            logger.error(f"Alert condition evaluation failed: {self.name} - {e}")
            return False

    def trigger(self):
        """Mark alert as triggered."""
        self.last_triggered = time.time()


@dataclass
class MonitoringDashboard:
    """Production monitoring dashboard."""

    # Core metrics
    system_health: Dict[str, Any] = field(default_factory=dict)
    error_stats: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)

    # Alert rules
    alert_rules: List[AlertRule] = field(
        default_factory=lambda: [
            AlertRule(
                name="high_error_rate",
                condition="metrics.get('error_rate', 0) > 5.0",
                severity="warning",
                message="Error rate above 5%: {error_rate:.1f}%",
            ),
            AlertRule(
                name="critical_memory_usage",
                condition="metrics.get('memory_usage_percent', 0) > 90",
                severity="critical",
                message="Memory usage critical: {memory_usage_percent:.1f}%",
            ),
            AlertRule(
                name="llm_unavailable",
                condition="not metrics.get('llm_available', True)",
                severity="error",
                message="LLM service unavailable",
            ),
            AlertRule(
                name="slow_responses",
                condition="metrics.get('avg_response_time', 0) > 5.0",
                severity="warning",
                message="Average response time > 5s: {avg_response_time:.2f}s",
            ),
            AlertRule(
                name="cache_miss_high",
                condition="metrics.get('cache_hit_rate', 100) < 50",
                severity="info",
                message="Cache hit rate low: {cache_hit_rate:.1f}%",
            ),
        ]
    )

    # Alert history
    alert_history: List[Dict[str, Any]] = field(default_factory=list)

    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics."""
        try:
            # Bridge health
            bridge = get_bridge()
            health = bridge.check_health()

            # Error tracking
            error_tracker = get_error_tracker()
            error_stats = error_tracker.get_error_stats()

            # HTTP pool metrics
            http_pool = asyncio.run(get_http_pool())
            pool_stats = asyncio.run(http_pool.get_stats())

            # Cache metrics
            llm_cache = get_llm_cache()
            api_cache = get_api_cache()

            llm_cache_stats = llm_cache.get_stats()
            api_cache_stats = api_cache.get_stats()

        # Aggregate metrics
        overall = health.get("Overall", {})
        metrics = {
            # System health
            "overall_health": overall.get("status", "unknown"),
            "critical_issues": overall.get("critical_issues", 0),
            "warning_issues": overall.get("warning_issues", 0),

            # Component status
            "llm_available": health.get("LLM", {}).get("ok", False),
            "tools_count": health.get("Tools", {}).get("count", 0),
            "agents_count": health.get("Agents", {}).get("count", 0),

            # Error metrics
            "total_errors": error_stats.get("total_errors", 0),
            "error_rate": error_stats.get("most_common_error_types", {}),
            "error_patterns": len(error_stats.get("patterns", [])),

            # Performance metrics
            "http_success_rate": pool_stats.get("success_rate", 0),
            "http_avg_response_time": pool_stats.get("average_response_time", 0),
            "cache_hit_rate": llm_cache_stats.get("hit_rate", 0),
            "memory_usage_percent": health.get("System", {}).get("memory", {}).get("usage_percent", 0),

            # Resource usage
            "cpu_usage": health.get("System", {}).get("cpu", {}).get("usage_percent", 0),
            "active_connections": pool_stats.get("active_connections", 0),

            # Cache stats
            "llm_cache_entries": llm_cache_stats.get("entries", 0),
            "api_cache_entries": api_cache_stats.get("entries", 0),

            # Timestamp
            "collected_at": time.time(),
            "timestamp": datetime.now().isoformat()
        }

            self.system_health = health
            self.error_stats = error_stats
            self.performance_metrics = metrics

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {"error": str(e), "collected_at": time.time(), "status": "collection_failed"}

    def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check all alert rules against current metrics."""
        triggered_alerts = []

        for rule in self.alert_rules:
            if rule.should_trigger(metrics):
                # Format message with metrics
                message = rule.message.format(**metrics)

                alert = {
                    "rule_name": rule.name,
                    "severity": rule.severity,
                    "message": message,
                    "timestamp": time.time(),
                    "metrics_snapshot": metrics.copy(),
                }

                triggered_alerts.append(alert)
                rule.trigger()

                # Log alert
                log_method = getattr(logger, rule.severity, logger.info)
                log_method(f"ALERT [{rule.name}]: {message}", extra={"alert": alert})

        # Add to history
        self.alert_history.extend(triggered_alerts)

        # Keep only last 100 alerts
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]

        return triggered_alerts

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data."""
        metrics = self.collect_system_metrics()
        alerts = self.check_alerts(metrics)

        return {
            "timestamp": time.time(),
            "metrics": metrics,
            "alerts": {
                "active": alerts,
                "recent_history": self.alert_history[-10:],  # Last 10 alerts
                "total_today": len(
                    [a for a in self.alert_history if a["timestamp"] > time.time() - 86400]
                ),  # Last 24h
            },
            "health_status": self.system_health,
            "error_summary": self.error_stats,
            "performance_trends": self._calculate_trends(),
        }

    def _calculate_trends(self) -> Dict[str, Any]:
        """Calculate metric trends (would need historical data in real implementation)."""
        # Placeholder for trend calculation
        # In a real system, this would compare current metrics with historical data
        return {
            "error_rate_trend": "stable",  # increasing, decreasing, stable
            "performance_trend": "stable",
            "memory_trend": "stable",
            "cache_trend": "stable",
        }

    def export_dashboard_json(self, filename: str = "monitoring-dashboard.json"):
        """Export dashboard data to JSON file."""
        data = self.get_dashboard_data()

        try:
            with open(filename, "w") as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Dashboard exported to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to export dashboard: {e}")
            return False

    async def run_continuous_monitoring(self, interval_seconds: int = 60):
        """Run continuous monitoring with periodic checks."""
        logger.info(f"Starting continuous monitoring (interval: {interval_seconds}s)")

        try:
            while True:
                dashboard_data = self.get_dashboard_data()

                # Log summary
                health_status = dashboard_data["metrics"].get("overall_health", "unknown")
                error_count = dashboard_data["metrics"].get("total_errors", 0)
                active_alerts = len(dashboard_data["alerts"]["active"])

                logger.info(
                    f"Monitoring cycle: Health={health_status}, Errors={error_count}, Alerts={active_alerts}"
                )

                # Export dashboard periodically
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    self.export_dashboard_json()

                await asyncio.sleep(interval_seconds)

        except KeyboardInterrupt:
            logger.info("Continuous monitoring stopped by user")
        except Exception as e:
            logger.error(f"Continuous monitoring failed: {e}")


# Global dashboard instance
_monitoring_dashboard = MonitoringDashboard()


def get_monitoring_dashboard() -> MonitoringDashboard:
    """Get global monitoring dashboard instance."""
    return _monitoring_dashboard


def quick_health_check() -> Dict[str, Any]:
    """Quick health check for immediate status."""
    dashboard = get_monitoring_dashboard()
    return dashboard.get_dashboard_data()


# Alert notification functions (would integrate with external systems)
def send_slack_alert(alert: Dict[str, Any]):
    """Send alert to Slack (placeholder)."""
    logger.warning(f"SLACK ALERT: {alert['message']}")


def send_email_alert(alert: Dict[str, Any]):
    """Send alert via email (placeholder)."""
    logger.warning(f"EMAIL ALERT: {alert['message']}")


def send_pagerduty_alert(alert: Dict[str, Any]):
    """Send alert to PagerDuty (placeholder)."""
    logger.critical(f"PAGERDUTY ALERT: {alert['message']}")


def dispatch_alert(alert: Dict[str, Any]):
    """Dispatch alert to appropriate channels based on severity."""
    severity = alert.get("severity", "info")

    if severity == "critical":
        send_pagerduty_alert(alert)
        send_slack_alert(alert)
        send_email_alert(alert)
    elif severity == "error":
        send_slack_alert(alert)
        send_email_alert(alert)
    elif severity == "warning":
        send_slack_alert(alert)
    else:
        logger.info(f"Info alert: {alert['message']}")


if __name__ == "__main__":
    # Run monitoring dashboard
    dashboard = get_monitoring_dashboard()

    # Single check
    print("Running single health check...")
    data = dashboard.get_dashboard_data()
    print(json.dumps(data, indent=2, default=str))

    # Export to file
    dashboard.export_dashboard_json()

    # Continuous monitoring (uncomment for production)
    # asyncio.run(dashboard.run_continuous_monitoring())
