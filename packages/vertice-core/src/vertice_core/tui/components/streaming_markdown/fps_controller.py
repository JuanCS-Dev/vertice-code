"""
Streaming Markdown FPS Controller - Adaptive Performance Management.

This module provides AdaptiveFPSController that monitors rendering
performance and automatically switches to plain text mode when
FPS drops too low.

Behavior:
- FPS >= 30: Full markdown rendering
- FPS 25-29: Visual warning, continues markdown
- FPS < 25: Fallback to plain text
- After 60 frames in plain: Try markdown again

Philosophy:
    "Performance is a feature, not an afterthought."
"""

from __future__ import annotations

import time
from typing import List

from .types import RenderMode


class AdaptiveFPSController:
    """
    Monitors FPS and switches to plain text automatically.

    Provides smooth degradation of rendering quality when
    the system cannot keep up with full markdown rendering.
    """

    FPS_THRESHOLD_WARNING = 29
    FPS_THRESHOLD_FALLBACK = 25
    RECOVERY_FRAMES = 60  # Frames to try returning to markdown
    CONSECUTIVE_LOW_FRAMES = 5  # Low frames before fallback

    def __init__(self):
        """Initialize FPS controller."""
        self.mode = RenderMode.MARKDOWN
        self.frames_in_plain = 0
        self.low_fps_count = 0
        self._frame_times: List[float] = []
        self._last_frame_time: float = time.perf_counter()

    def record_frame(self) -> float:
        """
        Record a frame and return current FPS.

        Returns:
            Current FPS based on moving average
        """
        now = time.perf_counter()
        delta = now - self._last_frame_time
        self._last_frame_time = now

        # Keep last 10 frames for moving average
        self._frame_times.append(delta)
        if len(self._frame_times) > 10:
            self._frame_times.pop(0)

        # Calculate average FPS
        if self._frame_times:
            avg_delta = sum(self._frame_times) / len(self._frame_times)
            return 1.0 / avg_delta if avg_delta > 0 else 60.0
        return 30.0

    def check_and_adapt(self, current_fps: float) -> tuple[RenderMode, str]:
        """
        Check FPS and adapt rendering mode.

        Args:
            current_fps: Current frames per second

        Returns:
            Tuple of (mode, status message)

        Status messages:
        - "OK": Normal operation
        - "WARNING_LOW_FPS": FPS below warning threshold
        - "FALLBACK_TO_PLAIN": Switched to plain text
        - "TRY_MARKDOWN_AGAIN": Attempting markdown recovery
        """
        if self.mode == RenderMode.MARKDOWN:
            if current_fps < self.FPS_THRESHOLD_FALLBACK:
                self.low_fps_count += 1
                if self.low_fps_count >= self.CONSECUTIVE_LOW_FRAMES:
                    self.mode = RenderMode.PLAIN_TEXT
                    self.frames_in_plain = 0
                    self.low_fps_count = 0
                    return self.mode, "FALLBACK_TO_PLAIN"
            else:
                self.low_fps_count = 0

            if current_fps < self.FPS_THRESHOLD_WARNING:
                return self.mode, "WARNING_LOW_FPS"
        else:
            self.frames_in_plain += 1
            if self.frames_in_plain >= self.RECOVERY_FRAMES:
                self.mode = RenderMode.MARKDOWN
                self.frames_in_plain = 0
                return self.mode, "TRY_MARKDOWN_AGAIN"

        return self.mode, "OK"

    def reset(self) -> None:
        """Reset controller to initial state."""
        self.mode = RenderMode.MARKDOWN
        self.frames_in_plain = 0
        self.low_fps_count = 0
        self._frame_times.clear()
        self._last_frame_time = time.perf_counter()


__all__ = ["AdaptiveFPSController"]
