"""
Streaming Markdown Types - Core Data Structures.

This module provides:
- RenderMode: Enum for rendering mode (markdown vs plain text)
- PerformanceMetrics: Dataclass for streaming performance tracking

Philosophy:
    "Types define the contract, implementation follows."
"""

from dataclasses import dataclass
from enum import Enum


class RenderMode(Enum):
    """Rendering mode for streaming markdown."""
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"


@dataclass
class PerformanceMetrics:
    """Performance metrics for streaming markdown rendering."""
    frames_rendered: int = 0
    total_render_time_ms: float = 0.0
    last_fps: float = 30.0
    min_fps: float = 30.0
    dropped_frames: int = 0
    fallback_count: int = 0

    @property
    def avg_render_time_ms(self) -> float:
        """Calculate average render time in milliseconds."""
        if self.frames_rendered == 0:
            return 0.0
        return self.total_render_time_ms / self.frames_rendered

    @property
    def current_fps(self) -> float:
        """Return current FPS."""
        return self.last_fps


__all__ = ["RenderMode", "PerformanceMetrics"]
