"""
JUSTICA Monitor Package - Real-time agent behavior monitoring.

"Acesso ao chain-of-thought melhora dramaticamente a deteccao"
"Threshold: Score >= 80 = violacao detectada"

Baseado em SHADE-Arena Monitoring (Anthropic, 2025)

Modulos:
    types: SuspicionLevel enum, SuspicionScore dataclass
    events: MonitoringEvent dataclass
    session: AgentSession dataclass
    patterns: Suspicious behavior patterns
    core: JusticaMonitor main class

Exemplo de uso:
    >>> from vertice_governance.justica.monitor import JusticaMonitor, SuspicionLevel
    >>> monitor = JusticaMonitor(constitution)
    >>> score = monitor.monitor_agent("agent-001", "transcript here")
    >>> if score.is_violation:
    ...     report = monitor.create_violation_report("agent-001")
"""

from __future__ import annotations

# Types
from .types import SuspicionLevel, SuspicionScore

# Events
from .events import MonitoringEvent

# Session
from .session import AgentSession

# Patterns (for extension/customization)
from .patterns import PATTERN_WEIGHTS, SUSPICIOUS_PATTERNS

# Core
from .core import JusticaMonitor


__all__ = [
    # Types
    "SuspicionLevel",
    "SuspicionScore",
    # Events
    "MonitoringEvent",
    # Session
    "AgentSession",
    # Patterns
    "SUSPICIOUS_PATTERNS",
    "PATTERN_WEIGHTS",
    # Core
    "JusticaMonitor",
]
