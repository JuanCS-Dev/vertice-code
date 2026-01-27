"""
NEXUS GCloud Metrics Integration

Reports Nervous System metrics to Google Cloud Monitoring for observability.

Metrics reported:
- nervous_system/autonomous_resolution_rate
- nervous_system/latency (by layer)
- nervous_system/reflex_activations
- nervous_system/homeostasis_score

Integration:
- Project: vertice-ai
- Uses google-cloud-monitoring SDK
- Custom metrics with descriptors
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# GCloud Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "vertice-ai")
REGION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# Try to import Cloud Monitoring
MONITORING_AVAILABLE = False
try:
    from google.cloud import monitoring_v3
    from google.api import metric_pb2 as ga_metric
    from google.api import label_pb2 as ga_label

    MONITORING_AVAILABLE = True
except ImportError:
    logger.warning("google-cloud-monitoring not available, metrics will be logged only")


class NervousSystemMetrics:
    """
    Reports Nervous System metrics to Google Cloud Monitoring.

    Custom metrics:
    - custom.googleapis.com/nervous_system/autonomous_resolution_rate
    - custom.googleapis.com/nervous_system/latency
    - custom.googleapis.com/nervous_system/reflex_activations
    - custom.googleapis.com/nervous_system/homeostasis_score
    """

    METRIC_PREFIX = "custom.googleapis.com/nervous_system"

    def __init__(self, project_id: str = PROJECT_ID):
        self.project_id = project_id
        self.project_name = f"projects/{project_id}"
        self._client: Optional[Any] = None
        self._initialized = False

        if MONITORING_AVAILABLE:
            try:
                self._client = monitoring_v3.MetricServiceClient()
                self._initialized = True
                logger.info("🔬 Cloud Monitoring client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Cloud Monitoring: {e}")

    async def report_resolution(
        self,
        layer: str,
        success: bool,
        latency_ms: float,
        service: str = "vertice-agent-gateway",
    ) -> None:
        """Report a resolution event to Cloud Monitoring."""
        if not self._initialized:
            logger.debug(f"Metrics (local): {layer=}, {success=}, {latency_ms=}")
            return

        try:
            await asyncio.to_thread(
                self._write_resolution_metrics,
                layer,
                success,
                latency_ms,
                service,
            )
        except Exception as e:
            logger.warning(f"Failed to report resolution metric: {e}")

    def _write_resolution_metrics(
        self,
        layer: str,
        success: bool,
        latency_ms: float,
        service: str,
    ) -> None:
        """Write resolution metrics (sync, for thread pool)."""
        now = time.time()

        # Create time series for latency
        latency_series = monitoring_v3.TimeSeries()
        latency_series.metric.type = f"{self.METRIC_PREFIX}/latency"
        latency_series.metric.labels["layer"] = layer
        latency_series.resource.type = "global"

        point = monitoring_v3.Point()
        point.value.double_value = latency_ms
        point.interval.end_time.seconds = int(now)
        point.interval.end_time.nanos = int((now % 1) * 1e9)
        latency_series.points = [point]

        # Create time series for resolution rate
        rate_series = monitoring_v3.TimeSeries()
        rate_series.metric.type = f"{self.METRIC_PREFIX}/autonomous_resolution_rate"
        rate_series.metric.labels["layer"] = layer
        rate_series.metric.labels["service"] = service
        rate_series.resource.type = "global"

        rate_point = monitoring_v3.Point()
        rate_point.value.double_value = 1.0 if success else 0.0
        rate_point.interval.end_time.seconds = int(now)
        rate_point.interval.end_time.nanos = int((now % 1) * 1e9)
        rate_series.points = [rate_point]

        # Write all series
        self._client.create_time_series(
            name=self.project_name,
            time_series=[latency_series, rate_series],
        )

    async def report_reflex_activation(
        self,
        neuron: str,
        action: str,
        latency_ms: float,
    ) -> None:
        """Report reflex arc activation."""
        if not self._initialized:
            logger.debug(f"Reflex (local): {neuron=}, {action=}, {latency_ms=}")
            return

        try:
            await asyncio.to_thread(
                self._write_reflex_metric,
                neuron,
                action,
                latency_ms,
            )
        except Exception as e:
            logger.warning(f"Failed to report reflex metric: {e}")

    def _write_reflex_metric(
        self,
        neuron: str,
        action: str,
        latency_ms: float,
    ) -> None:
        """Write reflex metric (sync)."""
        now = time.time()

        series = monitoring_v3.TimeSeries()
        series.metric.type = f"{self.METRIC_PREFIX}/reflex_activations"
        series.metric.labels["neuron"] = neuron
        series.metric.labels["action"] = action
        series.resource.type = "global"

        point = monitoring_v3.Point()
        point.value.int64_value = 1
        point.interval.end_time.seconds = int(now)
        point.interval.end_time.nanos = int((now % 1) * 1e9)
        series.points = [point]

        self._client.create_time_series(
            name=self.project_name,
            time_series=[series],
        )

    async def report_homeostasis(
        self,
        metrics: Dict[str, float],
    ) -> None:
        """Report homeostasis metrics."""
        if not self._initialized:
            logger.debug(f"Homeostasis (local): {metrics}")
            return

        try:
            await asyncio.to_thread(self._write_homeostasis_metrics, metrics)
        except Exception as e:
            logger.warning(f"Failed to report homeostasis metrics: {e}")

    def _write_homeostasis_metrics(self, metrics: Dict[str, float]) -> None:
        """Write homeostasis metrics (sync)."""
        now = time.time()
        time_series = []

        # Autonomous resolution rate
        rate_series = monitoring_v3.TimeSeries()
        rate_series.metric.type = f"{self.METRIC_PREFIX}/autonomous_resolution_rate"
        rate_series.metric.labels["layer"] = "total"
        rate_series.metric.labels["service"] = "vertice-agent-gateway"
        rate_series.resource.type = "global"

        rate_point = monitoring_v3.Point()
        rate_point.value.double_value = metrics.get("autonomous_resolution_rate", 0)
        rate_point.interval.end_time.seconds = int(now)
        rate_point.interval.end_time.nanos = int((now % 1) * 1e9)
        rate_series.points = [rate_point]
        time_series.append(rate_series)

        # Homeostasis score (0-100)
        score_series = monitoring_v3.TimeSeries()
        score_series.metric.type = f"{self.METRIC_PREFIX}/homeostasis_score"
        score_series.resource.type = "global"

        score = metrics.get("autonomous_resolution_rate", 0) * 100
        score_point = monitoring_v3.Point()
        score_point.value.double_value = score
        score_point.interval.end_time.seconds = int(now)
        score_point.interval.end_time.nanos = int((now % 1) * 1e9)
        score_series.points = [score_point]
        time_series.append(score_series)

        self._client.create_time_series(
            name=self.project_name,
            time_series=time_series,
        )

    async def create_metric_descriptors(self) -> bool:
        """Create custom metric descriptors (run once during setup)."""
        if not self._initialized:
            return False

        try:
            descriptors = [
                {
                    "type": f"{self.METRIC_PREFIX}/autonomous_resolution_rate",
                    "metric_kind": "GAUGE",
                    "value_type": "DOUBLE",
                    "description": "Rate of events resolved autonomously",
                    "display_name": "Autonomous Resolution Rate",
                    "labels": [
                        {"key": "layer", "value_type": "STRING"},
                        {"key": "service", "value_type": "STRING"},
                    ],
                },
                {
                    "type": f"{self.METRIC_PREFIX}/latency",
                    "metric_kind": "GAUGE",
                    "value_type": "DOUBLE",
                    "unit": "ms",
                    "description": "Event processing latency by layer",
                    "display_name": "Nervous System Latency",
                    "labels": [
                        {"key": "layer", "value_type": "STRING"},
                    ],
                },
                {
                    "type": f"{self.METRIC_PREFIX}/reflex_activations",
                    "metric_kind": "CUMULATIVE",
                    "value_type": "INT64",
                    "description": "Number of reflex arc activations",
                    "display_name": "Reflex Activations",
                    "labels": [
                        {"key": "neuron", "value_type": "STRING"},
                        {"key": "action", "value_type": "STRING"},
                    ],
                },
                {
                    "type": f"{self.METRIC_PREFIX}/homeostasis_score",
                    "metric_kind": "GAUGE",
                    "value_type": "DOUBLE",
                    "description": "Overall homeostasis score (0-100)",
                    "display_name": "Homeostasis Score",
                    "labels": [],
                },
            ]

            for desc in descriptors:
                await asyncio.to_thread(self._create_descriptor, desc)

            logger.info("✅ Metric descriptors created")
            return True

        except Exception as e:
            logger.warning(f"Failed to create metric descriptors: {e}")
            return False

    def _create_descriptor(self, desc: Dict[str, Any]) -> None:
        """Create a single metric descriptor (sync)."""
        descriptor = ga_metric.MetricDescriptor()
        descriptor.type = desc["type"]
        descriptor.metric_kind = getattr(
            ga_metric.MetricDescriptor.MetricKind,
            desc["metric_kind"],
        )
        descriptor.value_type = getattr(
            ga_metric.MetricDescriptor.ValueType,
            desc["value_type"],
        )
        descriptor.description = desc["description"]
        descriptor.display_name = desc["display_name"]

        if "unit" in desc:
            descriptor.unit = desc["unit"]

        for label_def in desc.get("labels", []):
            label = ga_label.LabelDescriptor()
            label.key = label_def["key"]
            label.value_type = getattr(
                ga_label.LabelDescriptor.ValueType,
                label_def["value_type"],
            )
            descriptor.labels.append(label)

        try:
            self._client.create_metric_descriptor(
                name=self.project_name,
                metric_descriptor=descriptor,
            )
        except Exception as e:
            if "already exists" not in str(e).lower():
                raise


# Global instance
_metrics_instance: Optional[NervousSystemMetrics] = None


def get_metrics() -> NervousSystemMetrics:
    """Get global metrics instance."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = NervousSystemMetrics()
    return _metrics_instance
