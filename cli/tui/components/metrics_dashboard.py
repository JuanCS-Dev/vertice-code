"""
MAESTRO v10.0 - Metrics Dashboard Component

Mini metrics dashboard for inline performance monitoring.
"""

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.style import Style
from rich.box import ROUNDED, SIMPLE

from ..theme import COLORS
from .maestro_data_structures import MetricsData


class MetricsDashboard:
    """
    Mini metrics dashboard for performance monitoring.

    Features:
    - Success rate with color coding
    - Token usage and efficiency
    - Cost savings calculation
    - Latency monitoring
    """

    def __init__(self, metrics: MetricsData):
        """
        Initialize metrics dashboard.

        Args:
            metrics: MetricsData instance to display
        """
        self.metrics = metrics

    def render(self, compact: bool = True) -> Panel | Text:
        """
        Render metrics dashboard.

        Args:
            compact: If True, render as inline text. If False, render as panel.

        Returns:
            Rich Panel or Text ready for rendering
        """
        if compact:
            return self._render_compact()
        else:
            return self._render_full()

    def _render_compact(self) -> Text:
        """
        Render compact inline metrics.

        Returns:
            Formatted Text object
        """
        text = Text()

        # Success rate
        text.append("Success: ", style=COLORS['text_secondary'])
        success_color = self._get_success_color(self.metrics.success_rate)
        text.append(f"{self.metrics.success_rate:.1f}%", style=f"bold {success_color}")
        text.append(" | ", style=COLORS['text_tertiary'])

        # Tokens (show in thousands)
        text.append("Tokens: ", style=COLORS['text_secondary'])
        tokens_k = self.metrics.tokens_used / 1000
        text.append(f"{tokens_k:.1f}K", style=f"bold {COLORS['neon_cyan']}")

        # Token efficiency indicator
        if self.metrics.tokens_saved > 0:
            text.append(" ↓", style=COLORS['neon_green'])
            text.append(f"{self.metrics.tokens_saved:.0f}%", style=f"bold {COLORS['neon_green']}")

        text.append(" | ", style=COLORS['text_tertiary'])

        # Savings
        if self.metrics.saved_money > 0:
            text.append("Saved: ", style=COLORS['text_secondary'])
            text.append(f"${self.metrics.saved_money:,.2f}", style=f"bold {COLORS['neon_green']}")
        else:
            text.append("Latency: ", style=COLORS['text_secondary'])
            latency_color = self._get_latency_color(self.metrics.latency_ms)
            text.append(f"{self.metrics.latency_ms}ms", style=f"bold {latency_color}")

        return text

    def _render_full(self) -> Panel:
        """
        Render full metrics panel with detailed breakdown.

        Returns:
            Rich Panel with metrics table
        """
        # Create metrics table
        table = Table(
            show_header=False,
            box=SIMPLE,
            padding=(0, 2),
            expand=False
        )
        table.add_column("Metric", style=COLORS['text_secondary'])
        table.add_column("Value", justify="right")

        # Success rate
        success_color = self._get_success_color(self.metrics.success_rate)
        success_icon = self._get_success_icon(self.metrics.success_rate)
        table.add_row(
            "Success Rate",
            Text(f"{success_icon} {self.metrics.success_rate:.1f}%", style=f"bold {success_color}")
        )

        # Executions
        table.add_row(
            "Executions",
            Text(f"{self.metrics.execution_count}", style=f"bold {COLORS['neon_cyan']}")
        )

        # Tokens
        tokens_k = self.metrics.tokens_used / 1000
        table.add_row(
            "Tokens Used",
            Text(f"{tokens_k:.1f}K", style=f"bold {COLORS['neon_cyan']}")
        )

        # Token efficiency
        if self.metrics.tokens_saved > 0:
            table.add_row(
                "Token Efficiency",
                Text(f"↓ {self.metrics.tokens_saved:.1f}%", style=f"bold {COLORS['neon_green']}")
            )

        # Cost savings
        if self.metrics.saved_money > 0:
            table.add_row(
                "Cost Savings",
                Text(f"${self.metrics.saved_money:,.2f}", style=f"bold {COLORS['neon_green']}")
            )

        # Latency
        latency_color = self._get_latency_color(self.metrics.latency_ms)
        latency_icon = self._get_latency_icon(self.metrics.latency_ms)
        table.add_row(
            "Avg Latency",
            Text(f"{latency_icon} {self.metrics.latency_ms}ms", style=f"bold {latency_color}")
        )

        # Errors (if any)
        if self.metrics.error_count > 0:
            error_rate = (self.metrics.error_count / self.metrics.execution_count) * 100
            table.add_row(
                "Errors",
                Text(f"{self.metrics.error_count} ({error_rate:.1f}%)", style=f"bold {COLORS['neon_red']}")
            )

        return Panel(
            table,
            title=Text("📊 METRICS", style=f"bold {COLORS['neon_cyan']}"),
            border_style=COLORS['border_default'],
            box=ROUNDED,
            padding=(1, 2),
            style=Style(bgcolor=COLORS['bg_card'])
        )

    def _get_success_color(self, rate: float) -> str:
        """
        Get color for success rate.

        Args:
            rate: Success rate percentage

        Returns:
            Hex color string
        """
        if rate >= 95.0:
            return COLORS['neon_green']
        elif rate >= 80.0:
            return COLORS['neon_yellow']
        else:
            return COLORS['neon_red']

    def _get_success_icon(self, rate: float) -> str:
        """
        Get icon for success rate.

        Args:
            rate: Success rate percentage

        Returns:
            Icon string
        """
        if rate >= 95.0:
            return "✓"
        elif rate >= 80.0:
            return "⚠"
        else:
            return "✗"

    def _get_latency_color(self, latency_ms: int) -> str:
        """
        Get color for latency.

        Args:
            latency_ms: Latency in milliseconds

        Returns:
            Hex color string
        """
        if latency_ms < 200:
            return COLORS['neon_green']
        elif latency_ms < 500:
            return COLORS['neon_yellow']
        else:
            return COLORS['neon_red']

    def _get_latency_icon(self, latency_ms: int) -> str:
        """
        Get icon for latency.

        Args:
            latency_ms: Latency in milliseconds

        Returns:
            Icon string
        """
        if latency_ms < 200:
            return "⚡"
        elif latency_ms < 500:
            return "⏱️"
        else:
            return "🐌"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_metrics_text(metrics: MetricsData) -> Text:
    """
    Create compact metrics text for inline display.

    Args:
        metrics: MetricsData to display

    Returns:
        Formatted Text object
    """
    dashboard = MetricsDashboard(metrics)
    return dashboard.render(compact=True)


def create_metrics_panel(metrics: MetricsData) -> Panel:
    """
    Create full metrics panel for detailed display.

    Args:
        metrics: MetricsData to display

    Returns:
        Rich Panel
    """
    dashboard = MetricsDashboard(metrics)
    return dashboard.render(compact=False)


def format_token_count(count: int) -> str:
    """
    Format token count for display.

    Args:
        count: Raw token count

    Returns:
        Formatted string (e.g., "2.1K", "145.7K", "1.2M")
    """
    if count < 1000:
        return str(count)
    elif count < 1_000_000:
        return f"{count / 1000:.1f}K"
    else:
        return f"{count / 1_000_000:.1f}M"


def format_money(amount: float) -> str:
    """
    Format money amount for display.

    Args:
        amount: Money amount in dollars

    Returns:
        Formatted string (e.g., "$1,234.56")
    """
    if amount < 0.01:
        return "$0.00"
    elif amount < 1000:
        return f"${amount:.2f}"
    else:
        return f"${amount:,.2f}"
