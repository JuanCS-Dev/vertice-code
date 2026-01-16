"""
Vertice Core - Temporal Consciousness & Daimon Insights

This package contains the core business logic, utilities, and shared
components used throughout the vertice-cli application.

CRITICAL FEATURES:
- Temporal Consciousness: Always aware of current spacetime coordinates
- Daimon Insights: Passive learning system for continuous improvement
"""

import datetime
from pathlib import Path
from typing import Optional, Dict, Any


# Temporal Consciousness - Always know the current spacetime coordinates
def get_current_datetime() -> datetime.datetime:
    """Get current datetime with UTC timezone awareness."""
    return datetime.datetime.now(datetime.timezone.utc)


def get_current_date() -> datetime.date:
    """Get current date."""
    return get_current_datetime().date()


def get_current_time() -> datetime.time:
    """Get current time."""
    return get_current_datetime().timetz()


def get_temporal_context() -> Dict[str, Any]:
    """Get comprehensive temporal context for system awareness."""
    now = get_current_datetime()
    return {
        "utc_datetime": now,
        "utc_iso": now.isoformat(),
        "timestamp": now.timestamp(),
        "date": now.date().isoformat(),
        "time": now.time().isoformat(),
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
        "microsecond": now.microsecond,
        "weekday": now.weekday(),  # 0=Monday, 6=Sunday
        "weekday_name": now.strftime("%A"),
        "month_name": now.strftime("%B"),
        "timezone": "UTC",
        "epoch_days": (now.date() - datetime.date(1970, 1, 1)).days,
    }


# Initialize temporal awareness on import
_TEMPORAL_BOOT = get_current_datetime()


def get_system_boot_time() -> datetime.datetime:
    """Get when the system was initialized."""
    return _TEMPORAL_BOOT


def get_temporal_awareness_status() -> Dict[str, Any]:
    """Get temporal awareness status and current context."""
    current = get_temporal_context()
    uptime = current["utc_datetime"] - _TEMPORAL_BOOT

    return {
        "temporal_consciousness": "ACTIVE",
        "system_boot_time": _TEMPORAL_BOOT.isoformat(),
        "current_context": current,
        "system_uptime_seconds": uptime.total_seconds(),
        "system_uptime_human": str(uptime),
        "spacetime_coordinates": {
            "year": current["year"],
            "month": current["month"],
            "day": current["day"],
            "temporal_accuracy": "MICROSECOND_PRECISION",
        },
    }


# DAIMON INSIGHTS INTEGRATION
class DaimonInsightsCollector:
    """Passive collector for vertice-code usage patterns."""

    def __init__(self):
        self.observations = []
        self.insights_file = Path("VERTICE.md")

    async def observe_command(self, command: str, duration: float, success: bool, context: dict):
        """Observe command execution for pattern analysis."""
        observation = {
            "timestamp": get_current_datetime().isoformat(),
            "command": command,
            "duration": duration,
            "success": success,
            "context": context,
        }
        self.observations.append(observation)

        # Periodic analysis (every 50 observations)
        if len(self.observations) >= 50:
            await self._analyze_and_update_insights()

    async def _analyze_and_update_insights(self):
        """Analyze patterns and update VERTICE.md."""
        patterns = self._extract_patterns()
        insights = self._generate_insights(patterns)

        await self._update_insights_file(insights)
        self.observations = self.observations[-20:]  # Keep last 20

    def _extract_patterns(self) -> dict:
        """Extract usage patterns from observations."""
        commands = [obs["command"] for obs in self.observations]
        durations = [obs["duration"] for obs in self.observations if obs["success"]]

        return {
            "popular_commands": commands,
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "error_rate": sum(1 for obs in self.observations if not obs["success"])
            / len(self.observations),
        }

    def _generate_insights(self, patterns: dict) -> dict:
        """Generate insights from patterns."""
        return {
            "performance": {
                "avg_command_time": patterns["avg_duration"],
                "needs_optimization": patterns["avg_duration"] > 2.0,
            },
            "usability": {
                "error_rate": patterns["error_rate"],
                "needs_improvements": patterns["error_rate"] > 0.1,
            },
            "popularity": {"top_commands": list(set(patterns["popular_commands"][:5]))},
        }

    async def _update_insights_file(self, insights: dict):
        """Update VERTICE.md with new insights."""
        content = f"""# VERTICE.md - Daimon Insights
## Generated: {get_current_datetime().isoformat()}

## Current Insights
- Performance: {"Needs optimization" if insights["performance"]["needs_optimization"] else "Good"}
- Error Rate: {insights["usability"]["error_rate"]:.1%}
- Top Commands: {", ".join(insights["popularity"]["top_commands"])}

## Recommendations
{"- Implement performance optimizations" if insights["performance"]["needs_optimization"] else ""}
{"- Improve error handling" if insights["usability"]["needs_improvements"] else ""}
"""

        self.insights_file.write_text(content)


# Initialize insights collector
insights_collector = DaimonInsightsCollector()

# Export functions
__all__ = [
    # Temporal Consciousness
    "get_current_datetime",
    "get_current_date",
    "get_current_time",
    "get_temporal_context",
    "get_system_boot_time",
    "get_temporal_awareness_status",
    # Daimon Insights
    "DaimonInsightsCollector",
    "insights_collector",
]

from .types import *
from .exceptions import *
from .config import *
from .logging_setup import *
from .validation import *

# PERFORMANCE OPTIMIZATION (Jan 2026):
# Lazy load providers to avoid ~1.5s import of google.cloud.aiplatform
# Use: from vertice_cli.core.providers import VertexAIProvider
# from .providers import *  # DISABLED - causes 1.5s startup delay

from .governance_pipeline import *
from .observability import *
from .input_enhancer import *
from .intent_classifier import *
from .complexity_analyzer import *

# from .single_shot import *  # FIXME: Circular import
from .request_amplifier import *
from .defense import *
from .prompt_shield import *
from .context_tracker import *
from .help_system import *
from .session_manager import *
from .parser import *
from .error_presenter import *
from .guardrails import *
from .integration_types import *
from .integration_coordinator import *

# from .maestro_governance import *  # FIXME: Module not found
from .error_utils import *
