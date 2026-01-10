"""
Performance HUD - Real-time metrics overlay
===========================================

HUD minimalista mostrando métricas de performance em tempo real.
Latência P99, throughput, confidence scores.
"""

from __future__ import annotations

import time
from typing import Optional

from textual.widget import Widget
from textual.widgets import Static
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message


class PerformanceHUD(Widget):
    """
    Minimalist performance HUD showing real-time metrics.

    Features:
    - Latência P99 com cores semáforo
    - Confidence Score
    - Throughput (tokens/seg)
    - Queue time
    - Toggleable (F12)
    """

    DEFAULT_CSS = """
    PerformanceHUD {
        width: auto;
        height: 3;
        background: $surface;
        border: solid $primary;
        border-radius: 0;
        padding: 0 1;
        color: $text;
    }

    PerformanceHUD .metric {
        margin-right: 2;
    }

    PerformanceHUD .latency-good {
        color: $success;
    }

    PerformanceHUD .latency-warning {
        color: $warning;
    }

    PerformanceHUD .latency-critical {
        color: $error;
    }

    PerformanceHUD .confidence-high {
        color: $success;
    }

    PerformanceHUD .confidence-medium {
        color: $warning;
    }

    PerformanceHUD .confidence-low {
        color: $error;
    }
    """

    class MetricsUpdate(Message):
        """Update performance metrics."""

        def __init__(
            self, latency_ms: float, confidence: float, throughput: float, queue_time: float
        ):
            self.latency_ms = latency_ms
            self.confidence = confidence
            self.throughput = throughput
            self.queue_time = queue_time
            super().__init__()

    def __init__(self, visible: bool = False, id: Optional[str] = None):
        super().__init__(id=id)
        self.visible = visible
        self._latency_ms = 0.0
        self._confidence = 0.0
        self._throughput = 0.0
        self._queue_time = 0.0
        self._last_update = time.time()

    def compose(self) -> ComposeResult:
        """Compose the HUD."""
        with Horizontal():
            yield Static("", id="latency-metric", classes="metric")
            yield Static("", id="confidence-metric", classes="metric")
            yield Static("", id="throughput-metric", classes="metric")
            yield Static("", id="queue-metric", classes="metric")

    def on_mount(self) -> None:
        """Initialize HUD."""
        self._update_display()
        if not self.visible:
            self.add_class("hidden")

    async def on_performance_hud_metrics_update(self, event: MetricsUpdate) -> None:
        """Update metrics from external source."""
        self._latency_ms = event.latency_ms
        self._confidence = event.confidence
        self._throughput = event.throughput
        self._queue_time = event.queue_time
        self._last_update = time.time()
        self._update_display()

    def update_metrics(
        self,
        latency_ms: Optional[float] = None,
        confidence: Optional[float] = None,
        throughput: Optional[float] = None,
        queue_time: Optional[float] = None,
    ) -> None:
        """Update individual metrics."""
        if latency_ms is not None:
            self._latency_ms = latency_ms
        if confidence is not None:
            self._confidence = confidence
        if throughput is not None:
            self._throughput = throughput
        if queue_time is not None:
            self._queue_time = queue_time

        self._last_update = time.time()
        # Only update display if widget is mounted
        try:
            self._update_display()
        except Exception:
            pass  # Silently fail if not mounted yet

    def toggle_visibility(self) -> None:
        """Toggle HUD visibility."""
        self.visible = not self.visible
        if self.visible:
            self.remove_class("hidden")
        else:
            self.add_class("hidden")

    def _update_display(self) -> None:
        """Update the display with current metrics."""
        # Latency with traffic light colors
        latency_class = self._get_latency_class(self._latency_ms)
        latency_text = f"⚡ {self._latency_ms:.0f}ms"

        # Confidence with appropriate color
        confidence_class = self._get_confidence_class(self._confidence)
        confidence_text = f"🎯 {self._confidence:.0f}%"

        # Throughput
        throughput_text = f"🚀 {self._throughput:.1f}t/s"

        # Queue time
        queue_text = f"⏱️ {self._queue_time:.0f}ms"

        # Update widgets
        self.query_one("#latency-metric", Static).update(
            f"[{latency_class}]{latency_text}[/{latency_class}]"
        )
        self.query_one("#confidence-metric", Static).update(
            f"[{confidence_class}]{confidence_text}[/{confidence_class}]"
        )
        self.query_one("#throughput-metric", Static).update(f"[blue]{throughput_text}[/blue]")
        self.query_one("#queue-metric", Static).update(f"[yellow]{queue_text}[/yellow]")

    def _get_latency_class(self, latency_ms: float) -> str:
        """Get CSS class for latency based on thresholds."""
        if latency_ms <= 500:  # Good
            return "latency-good"
        elif latency_ms <= 1000:  # Warning
            return "latency-warning"
        else:  # Critical
            return "latency-critical"

    def _get_confidence_class(self, confidence: float) -> str:
        """Get CSS class for confidence score."""
        if confidence >= 90:  # High
            return "confidence-high"
        elif confidence >= 75:  # Medium
            return "confidence-medium"
        else:  # Low
            return "confidence-low"

    @property
    def current_metrics(self) -> dict:
        """Get current metrics as dict."""
        return {
            "latency_ms": self._latency_ms,
            "confidence": self._confidence,
            "throughput": self._throughput,
            "queue_time": self._queue_time,
            "last_update": self._last_update,
        }
