"""
Token Sparkline - Historical token usage visualization.

Uses Textual's Sparkline widget for token history display.

Phase 11: Visual Upgrade - Polish & Delight.
"""

from __future__ import annotations

from collections import deque
from typing import Optional, Sequence

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static, Sparkline
from textual.reactive import reactive
from textual.widget import Widget


class TokenSparkline(Widget):
    """
    Sparkline visualization of token usage over time.

    Features:
    - Rolling history window
    - Color-coded thresholds
    - Current/peak/average stats
    """

    DEFAULT_CSS = """
    TokenSparkline {
        width: 100%;
        height: 3;
        background: $surface;
        padding: 0 1;
    }

    TokenSparkline > Horizontal {
        width: 100%;
        height: 100%;
    }

    TokenSparkline .sparkline-chart {
        width: 1fr;
        height: 100%;
    }

    TokenSparkline .sparkline-stats {
        width: auto;
        min-width: 15;
        height: 100%;
        padding-left: 1;
        text-align: right;
    }

    TokenSparkline Sparkline {
        width: 100%;
        height: 100%;
    }
    """

    history_size: reactive[int] = reactive(50)

    def __init__(
        self,
        history_size: int = 50,
        limit: int = 32000,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(id=id)
        self._limit = limit
        self._history: deque[float] = deque(maxlen=history_size)
        self._sparkline: Optional[Sparkline] = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            self._sparkline = Sparkline(
                data=[],
                summary_function=max,
                id="spark",
                classes="sparkline-chart",
            )
            yield self._sparkline
            yield Static("", classes="sparkline-stats", id="stats")

    def on_mount(self) -> None:
        # Initialize with zeros
        for _ in range(10):
            self._history.append(0)
        self._update_display()

    def add_sample(self, tokens: int) -> None:
        """Add a token count sample."""
        # Normalize to percentage of limit
        pct = (tokens / self._limit) * 100 if self._limit > 0 else 0
        self._history.append(pct)
        self._update_display()

    def set_limit(self, limit: int) -> None:
        """Update the token limit."""
        self._limit = limit

    def _update_display(self) -> None:
        """Update sparkline and stats."""
        data = list(self._history)

        if self._sparkline and data:
            self._sparkline.data = data

        # Update stats
        try:
            stats = self.query_one("#stats", Static)
            if data:
                current = data[-1]
                peak = max(data)
                avg = sum(data) / len(data)
                stats.update(f"[bold]{current:.0f}%[/]\n" f"[dim]↑{peak:.0f}% ⌀{avg:.0f}%[/]")
            else:
                stats.update("--")
        except (AttributeError, ValueError):
            pass

    def clear(self) -> None:
        """Clear history."""
        self._history.clear()
        for _ in range(10):
            self._history.append(0)
        self._update_display()


class CompactSparkline(Static):
    """
    Compact inline sparkline using ASCII characters.

    For use in status bars and tight spaces.
    """

    SPARK_CHARS = "▁▂▃▄▅▆▇█"

    DEFAULT_CSS = """
    CompactSparkline {
        width: auto;
        height: 1;
        color: $accent;
    }
    """

    def __init__(
        self,
        history_size: int = 20,
        id: Optional[str] = None,
    ) -> None:
        super().__init__("", id=id)
        self._history: deque[float] = deque(maxlen=history_size)

    def add_sample(self, value: float, max_value: float = 100) -> None:
        """Add a sample value."""
        # Normalize to 0-1
        normalized = min(1.0, max(0.0, value / max_value)) if max_value > 0 else 0
        self._history.append(normalized)
        self._render()

    def _render(self) -> None:
        """Render sparkline as ASCII."""
        if not self._history:
            self.update("")
            return

        chars = []
        for value in self._history:
            idx = int(value * (len(self.SPARK_CHARS) - 1))
            chars.append(self.SPARK_CHARS[idx])

        self.update("".join(chars))

    def clear(self) -> None:
        """Clear history."""
        self._history.clear()
        self._render()


class MultiSparkline(Widget):
    """
    Multiple sparklines for comparing metrics.

    Shows multiple data series side by side.
    """

    DEFAULT_CSS = """
    MultiSparkline {
        width: 100%;
        height: auto;
    }

    MultiSparkline .sparkline-row {
        width: 100%;
        height: 2;
    }

    MultiSparkline .sparkline-label {
        width: 10;
        height: 1;
        color: $text-muted;
    }

    MultiSparkline Sparkline {
        width: 1fr;
        height: 1;
    }
    """

    def __init__(
        self,
        labels: Optional[Sequence[str]] = None,
        history_size: int = 30,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(id=id)
        self._labels = list(labels) if labels else ["Series 1"]
        self._history_size = history_size
        self._data: dict[str, deque[float]] = {
            label: deque(maxlen=history_size) for label in self._labels
        }

    def compose(self) -> ComposeResult:
        for label in self._labels:
            with Horizontal(classes="sparkline-row"):
                yield Static(label, classes="sparkline-label")
                yield Sparkline(
                    data=[0] * 10,
                    summary_function=max,
                    id=f"spark-{label.lower().replace(' ', '-')}",
                )

    def add_samples(self, **values: float) -> None:
        """Add samples for multiple series."""
        for label, value in values.items():
            if label in self._data:
                self._data[label].append(value)

        self._update_sparklines()

    def _update_sparklines(self) -> None:
        """Update all sparklines."""
        for label, data in self._data.items():
            try:
                spark_id = f"spark-{label.lower().replace(' ', '-')}"
                spark = self.query_one(f"#{spark_id}", Sparkline)
                spark.data = list(data) if data else [0]
            except (AttributeError, ValueError):
                pass
