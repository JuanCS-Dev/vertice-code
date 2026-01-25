"""
Span and Metrics Exporters

Export observability data to various backends.

References:
- OpenTelemetry OTLP specification
- Prometheus exposition format
- arXiv:2401.02009 (LLM Observability)
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path

from .types import ObservabilityConfig

logger = logging.getLogger(__name__)


class BaseExporter(ABC):
    """Abstract base class for exporters."""

    @abstractmethod
    def export(self, data: List[Dict[str, Any]]) -> bool:
        """Export data to backend."""
        raise NotImplementedError

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown exporter and flush any pending data."""
        raise NotImplementedError


class SpanExporter(BaseExporter):
    """
    Exports spans to various backends.

    Supports:
    - Console (for development)
    - JSON file (for local storage)
    - OTLP HTTP (for OpenTelemetry collectors)
    """

    def __init__(
        self,
        config: Optional[ObservabilityConfig] = None,
        export_path: Optional[Path] = None,
    ):
        """
        Initialize span exporter.

        Args:
            config: Observability configuration
            export_path: Path for file-based export
        """
        self._config = config or ObservabilityConfig()
        self._export_path = export_path
        self._batch: List[Dict[str, Any]] = []
        self._last_export = time.time()

    def export(self, spans: List[Dict[str, Any]]) -> bool:
        """
        Export spans to configured backend.

        Args:
            spans: List of span dictionaries

        Returns:
            True if export successful
        """
        if not spans:
            return True

        self._batch.extend(spans)

        # Check if batch should be flushed
        should_flush = (
            len(self._batch) >= self._config.batch_size
            or time.time() - self._last_export >= self._config.export_interval_seconds
        )

        if should_flush:
            return self._flush()

        return True

    def _flush(self) -> bool:
        """Flush pending spans to backend."""
        if not self._batch:
            return True

        success = True

        # Export to file if configured
        if self._export_path:
            success = self._export_to_file()

        # Export to OTLP if configured
        if self._config.otlp_endpoint:
            success = success and self._export_to_otlp()

        if success:
            self._batch.clear()
            self._last_export = time.time()

        return success

    def _export_to_file(self) -> bool:
        """Export spans to JSON file."""
        try:
            self._export_path.parent.mkdir(parents=True, exist_ok=True)

            # Append to existing file or create new
            existing_data = []
            if self._export_path.exists():
                with open(self._export_path) as f:
                    existing_data = json.load(f)

            existing_data.extend(self._batch)

            with open(self._export_path, "w") as f:
                json.dump(existing_data, f, indent=2, default=str)

            logger.debug(f"[Exporter] Exported {len(self._batch)} spans to {self._export_path}")
            return True

        except Exception as e:
            logger.error(f"[Exporter] Failed to export to file: {e}")
            return False

    def _export_to_otlp(self) -> bool:
        """Export spans to OTLP endpoint."""
        # Note: In production, use opentelemetry-exporter-otlp
        # This is a simplified implementation for demonstration
        try:
            import urllib.request
            import urllib.error

            payload = {
                "resourceSpans": [
                    {
                        "resource": {
                            "attributes": [
                                {
                                    "key": "service.name",
                                    "value": {"stringValue": self._config.service_name},
                                },
                                {
                                    "key": "service.version",
                                    "value": {"stringValue": self._config.service_version},
                                },
                            ]
                        },
                        "scopeSpans": [{"spans": self._batch}],
                    }
                ]
            }

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self._config.otlp_endpoint}/v1/traces",
                data=data,
                headers={"Content-Type": "application/json"},
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    logger.debug(f"[Exporter] Exported {len(self._batch)} spans to OTLP")
                    return True

            return False

        except Exception as e:
            logger.warning(f"[Exporter] Failed to export to OTLP: {e}")
            return False

    def shutdown(self) -> None:
        """Shutdown exporter and flush pending data."""
        self._flush()


class MetricsExporter(BaseExporter):
    """
    Exports metrics to various backends.

    Supports:
    - Prometheus format (text exposition)
    - JSON file
    - OTLP HTTP
    """

    def __init__(
        self,
        config: Optional[ObservabilityConfig] = None,
        export_path: Optional[Path] = None,
    ):
        """
        Initialize metrics exporter.

        Args:
            config: Observability configuration
            export_path: Path for file-based export
        """
        self._config = config or ObservabilityConfig()
        self._export_path = export_path

    def export(self, metrics: List[Dict[str, Any]]) -> bool:
        """
        Export metrics to configured backend.

        Args:
            metrics: List of metric dictionaries

        Returns:
            True if export successful
        """
        if not metrics:
            return True

        success = True

        if self._export_path:
            success = self._export_to_file(metrics)

        return success

    def _export_to_file(self, metrics: List[Dict[str, Any]]) -> bool:
        """Export metrics to JSON file."""
        try:
            self._export_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self._export_path, "w") as f:
                json.dump(
                    {
                        "timestamp": time.time(),
                        "metrics": metrics,
                    },
                    f,
                    indent=2,
                    default=str,
                )

            logger.debug(f"[Exporter] Exported metrics to {self._export_path}")
            return True

        except Exception as e:
            logger.error(f"[Exporter] Failed to export metrics: {e}")
            return False

    def to_prometheus_format(self, metrics: Dict[str, Any]) -> str:
        """
        Convert metrics to Prometheus text exposition format.

        Args:
            metrics: Metrics dictionary

        Returns:
            Prometheus-format string
        """
        lines = []

        # Counters
        for name, values in metrics.get("counters", {}).items():
            metric_name = name.replace(".", "_").replace("-", "_")
            lines.append(f"# TYPE {metric_name} counter")

            for labels, value in values.items():
                if labels:
                    label_str = "{" + labels + "}"
                else:
                    label_str = ""
                lines.append(f"{metric_name}{label_str} {value}")

        # Gauges
        for name, values in metrics.get("gauges", {}).items():
            metric_name = name.replace(".", "_").replace("-", "_")
            lines.append(f"# TYPE {metric_name} gauge")

            for labels, value in values.items():
                if labels:
                    label_str = "{" + labels + "}"
                else:
                    label_str = ""
                lines.append(f"{metric_name}{label_str} {value}")

        # Histograms (simplified)
        for name, label_hists in metrics.get("histograms", {}).items():
            metric_name = name.replace(".", "_").replace("-", "_")
            lines.append(f"# TYPE {metric_name} histogram")

            for labels, hist_data in label_hists.items():
                if labels:
                    label_str = "{" + labels + "}"
                else:
                    label_str = ""
                lines.append(f"{metric_name}_count{label_str} {hist_data['count']}")
                lines.append(f"{metric_name}_sum{label_str} {hist_data['sum']}")

        return "\n".join(lines)

    def shutdown(self) -> None:
        """Shutdown exporter."""
        pass


class ConsoleExporter(BaseExporter):
    """Simple console exporter for development/debugging."""

    def export(self, data: List[Dict[str, Any]]) -> bool:
        """Print data to console."""
        for item in data:
            logger.info(f"[ConsoleExporter] {json.dumps(item, indent=2, default=str)}")
        return True

    def shutdown(self) -> None:
        """No-op for console exporter."""
        pass
