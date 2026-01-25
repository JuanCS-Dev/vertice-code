"""
AG-UI protocol utilities (Phase 3).

MVP, stability-first schema for SSE streaming between Agent Gateway and clients.
"""

from __future__ import annotations

from .protocol import (
    AGUIEvent,
    AGUIEventType,
    AGUIErrorData,
    AGUIFinalData,
    AGUIToolData,
    AGUIDeltaData,
    sse_encode_event,
)
from .ag_ui_adk import adk_event_to_agui, adk_events_to_agui

__all__ = [
    "AGUIEvent",
    "AGUIEventType",
    "AGUIErrorData",
    "AGUIFinalData",
    "AGUIToolData",
    "AGUIDeltaData",
    "sse_encode_event",
    "adk_event_to_agui",
    "adk_events_to_agui",
]
