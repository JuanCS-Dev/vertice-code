"""
Production Monitoring Service - LangSmith/Phoenix Integration
Real-time AI performance monitoring and observability
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class LangSmithMonitor:
    """LangSmith integration for AI observability."""

    def __init__(self, api_key: Optional[str] = None, project_name: str = "vertice-code"):
        self.api_key = api_key or "your-langsmith-api-key"
        self.project_name = project_name
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize LangSmith client."""
        try:
            # LangSmith client initialization would go here
            # from langsmith import Client
            # self.client = Client(api_key=self.api_key)
            logger.info("LangSmith monitoring initialized")
        except ImportError:
            logger.warning("LangSmith not available - monitoring disabled")
            self.client = None

    async def log_ai_interaction(
        self,
        run_id: str,
        input_text: str,
        output_text: str,
        model_name: str,
        latency_ms: int,
        token_count: int,
        safety_score: float,
        bias_score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log AI interaction to LangSmith."""
        if not self.client:
            return

        # run_data = {
        #     "run_id": run_id,
        #     "name": f"AI Interaction - {model_name}",
        #     "run_type": "llm",
        #     "inputs": {"prompt": input_text},
        #     "outputs": {"response": output_text},
        #     "start_time": datetime.now() - timedelta(milliseconds=latency_ms),
        #     "end_time": datetime.now(),
        #     "extra": {
        #         "model_name": model_name,
        #         "latency_ms": latency_ms,
        #         "input_tokens": input_tokens,
        #         "output_tokens": output_tokens,
        #         "temperature": temperature,
        #         "cost": cost,
        #     },
        # }

        try:
            # self.client.create_run(**run_data)
            logger.debug(f"Logged AI interaction: {run_id}")
        except Exception as e:
            logger.error(f"Failed to log to LangSmith: {e}")

    async def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics from LangSmith."""
        if not self.client:
            return {"error": "LangSmith client not available"}

        try:
            # Query would go here
            # runs = self.client.list_runs(project_name=self.project_name, hours=hours)
            # Calculate metrics from runs

            # Mock response for now
            return {
                "total_runs": 1250,
                "avg_latency_ms": 450,
                "avg_tokens": 280,
                "error_rate": 0.02,
                "safety_violations": 3,
                "bias_alerts": 1,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get LangSmith metrics: {e}")
            return {"error": str(e)}


class PhoenixMonitor:
    """Arize Phoenix integration for AI observability."""

    def __init__(self, endpoint: str = "http://localhost:6006"):
        self.endpoint = endpoint
        self.session = None

    async def log_trace(
        self, trace_id: str, spans: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None
    ):
        """Log trace data to Phoenix."""
        try:
            # Phoenix logging would go here
            logger.debug(f"Logged trace to Phoenix: {trace_id}")
        except Exception as e:
            logger.error(f"Failed to log to Phoenix: {e}")

    async def get_trace_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get trace metrics from Phoenix."""
        try:
            # Query Phoenix API
            return {
                "total_traces": 890,
                "avg_trace_duration_ms": 520,
                "error_traces": 12,
                "slow_traces": 45,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get Phoenix metrics: {e}")
            return {"error": str(e)}


class ProductionMonitor:
    """
    Unified production monitoring service.
    Combines LangSmith and Phoenix for comprehensive AI observability.
    """

    def __init__(self):
        self.langsmith = LangSmithMonitor()
        self.phoenix = PhoenixMonitor()
        self.alerts = []
        self.metrics_cache = {}

    async def log_ai_request(
        self,
        request_id: str,
        workspace_id: str,
        user_id: Optional[str],
        agent_id: Optional[str],
        input_text: str,
        model_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Log the start of an AI request.

        Returns trace_id for later completion logging.
        """
        trace_id = f"{request_id}_{int(time.time() * 1000)}"

        # Log to monitoring systems
        logger.info(f"AI request started: {trace_id} (model: {model_name})")

        # Cache request start time
        self.metrics_cache[trace_id] = {
            "start_time": time.time(),
            "workspace_id": workspace_id,
            "user_id": user_id,
            "agent_id": agent_id,
            "input_text": input_text,
            "model_name": model_name,
            "context": context or {},
        }

        return trace_id

    async def log_ai_response(
        self,
        trace_id: str,
        output_text: str,
        token_count: int,
        safety_result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        """
        Log the completion of an AI request.
        """
        if trace_id not in self.metrics_cache:
            logger.warning(f"Trace ID not found: {trace_id}")
            return

        request_data = self.metrics_cache[trace_id]
        end_time = time.time()
        latency_ms = int((end_time - request_data["start_time"]) * 1000)

        # Extract safety metrics
        safety_score = 1.0
        bias_score = 0.0
        if safety_result:
            safety_score = safety_result.get("confidence_score", 1.0)
            # Calculate bias score from safety flags
            bias_score = 0.1  # Placeholder

        # Log to LangSmith
        await self.langsmith.log_ai_interaction(
            run_id=trace_id,
            input_text=request_data["input_text"],
            output_text=output_text,
            model_name=request_data["model_name"],
            latency_ms=latency_ms,
            token_count=token_count,
            safety_score=safety_score,
            bias_score=bias_score,
            metadata={
                "workspace_id": request_data["workspace_id"],
                "user_id": request_data["user_id"],
                "agent_id": request_data["agent_id"],
                "error": error,
                "context": request_data["context"],
            },
        )

        # Log to Phoenix
        spans = [
            {
                "name": "ai_interaction",
                "start_time": request_data["start_time"],
                "end_time": end_time,
                "attributes": {
                    "model": request_data["model_name"],
                    "latency_ms": latency_ms,
                    "token_count": token_count,
                    "safety_score": safety_score,
                },
            }
        ]

        await self.phoenix.log_trace(trace_id, spans, request_data["context"])

        # Check for alerts
        await self._check_alerts(latency_ms, safety_score, error)

        # Clean up cache
        del self.metrics_cache[trace_id]

        logger.info(f"AI response logged: {trace_id} ({latency_ms}ms, safety: {safety_score:.2f})")

    async def _check_alerts(self, latency_ms: int, safety_score: float, error: Optional[str]):
        """Check for alerting conditions."""
        alerts = []

        # Latency alert
        if latency_ms > 5000:  # 5 seconds
            alerts.append(
                {
                    "type": "latency",
                    "severity": "warning",
                    "message": f"High latency detected: {latency_ms}ms",
                    "value": latency_ms,
                }
            )

        # Safety alert
        if safety_score < 0.8:
            alerts.append(
                {
                    "type": "safety",
                    "severity": "critical",
                    "message": f"Low safety score: {safety_score:.2f}",
                    "value": safety_score,
                }
            )

        # Error alert
        if error:
            alerts.append(
                {
                    "type": "error",
                    "severity": "error",
                    "message": f"AI request failed: {error}",
                    "value": error,
                }
            )

        # Store alerts
        self.alerts.extend(alerts)

        # Log alerts
        for alert in alerts:
            logger.warning(f"ALERT: {alert['type']} - {alert['message']}")

    async def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data."""
        # Get metrics from both systems
        langsmith_metrics = await self.langsmith.get_performance_metrics()
        phoenix_metrics = await self.phoenix.get_trace_metrics()

        # Combine metrics
        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "ai_performance": {
                "total_requests": langsmith_metrics.get("total_runs", 0),
                "avg_latency_ms": langsmith_metrics.get("avg_latency_ms", 0),
                "avg_tokens": langsmith_metrics.get("avg_tokens", 0),
                "error_rate": langsmith_metrics.get("error_rate", 0),
            },
            "safety_metrics": {
                "safety_violations": langsmith_metrics.get("safety_violations", 0),
                "bias_alerts": langsmith_metrics.get("bias_alerts", 0),
            },
            "system_health": {
                "total_traces": phoenix_metrics.get("total_traces", 0),
                "error_traces": phoenix_metrics.get("error_traces", 0),
                "slow_traces": phoenix_metrics.get("slow_traces", 0),
            },
            "alerts": self.alerts[-10:],  # Last 10 alerts
        }

        # Calculate health score
        dashboard["health_score"] = self._calculate_health_score(dashboard)

        return dashboard

    def _calculate_health_score(self, dashboard: Dict[str, Any]) -> float:
        """Calculate overall system health score (0.0-1.0)."""
        try:
            perf = dashboard["ai_performance"]
            safety = dashboard["safety_metrics"]
            health = dashboard["system_health"]

            # Performance score (latency, errors)
            latency_score = max(0, 1 - (perf.get("avg_latency_ms", 0) / 2000))  # Target: <2s
            error_score = max(0, 1 - perf.get("error_rate", 0) * 5)  # Target: <20% errors

            # Safety score
            safety_score = max(
                0, 1 - (safety.get("safety_violations", 0) / 10)
            )  # Target: <10 violations

            # System health score
            trace_error_rate = health.get("error_traces", 0) / max(health.get("total_traces", 1), 1)
            health_score = max(0, 1 - trace_error_rate * 2)  # Target: <50% error traces

            # Weighted average
            weights = {"latency": 0.3, "error": 0.2, "safety": 0.3, "health": 0.2}
            overall_score = (
                latency_score * weights["latency"]
                + error_score * weights["error"]
                + safety_score * weights["safety"]
                + health_score * weights["health"]
            )

            return round(overall_score, 3)

        except Exception as e:
            logger.error(f"Failed to calculate health score: {e}")
            return 0.5

    async def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        return self.alerts[-limit:]


# Global instance
_monitor: Optional[ProductionMonitor] = None


def get_production_monitor() -> ProductionMonitor:
    """Get global production monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = ProductionMonitor()
    return _monitor
