"""
Premium Spinner - Phase 9 Visual Refresh.

Minimalist async spinner with status text.
Uses Unicode Braille for smooth animation.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import asyncio
import itertools
from typing import AsyncIterator, Iterator


# Spinner frame sets (ordered by visual style)
SPINNER_BRAILLE = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
SPINNER_DOTS = ["◐", "◓", "◑", "◒"]
SPINNER_LINE = ["|", "/", "-", "\\"]
SPINNER_BOUNCE = ["⠁", "⠂", "⠄", "⠂"]
SPINNER_ARC = ["◜", "◠", "◝", "◞", "◡", "◟"]


class PremiumSpinner:
    """
    Premium async spinner with status text.

    Usage:
        spinner = PremiumSpinner()
        async for frame in spinner.spin("Processing..."):
            print(f"\\r{frame}", end="")
            if done:
                break
    """

    def __init__(
        self,
        frames: list[str] | None = None,
        interval: float = 0.1,
        color: str = "#22D3EE",
    ) -> None:
        """
        Initialize spinner.

        Args:
            frames: Animation frames (default: Braille dots)
            interval: Frame interval in seconds
            color: Rich markup color
        """
        self.frames = frames or SPINNER_DOTS
        self.interval = interval
        self.color = color
        self._running = False

    async def spin(self, status: str = "") -> AsyncIterator[str]:
        """
        Async generator that yields spinner frames with status.

        Args:
            status: Status text to show next to spinner

        Yields:
            Formatted frame string with Rich markup
        """
        self._running = True
        for frame in itertools.cycle(self.frames):
            if not self._running:
                break
            yield self._format_frame(frame, status)
            await asyncio.sleep(self.interval)

    def stop(self) -> None:
        """Stop the spinner."""
        self._running = False

    def _format_frame(self, frame: str, status: str) -> str:
        """Format frame with color and status."""
        if status:
            return f"[{self.color}]{frame}[/{self.color}] {status}"
        return f"[{self.color}]{frame}[/{self.color}]"

    def frames_sync(self, count: int = 10) -> Iterator[str]:
        """
        Synchronous frame iterator (for non-async contexts).

        Args:
            count: Number of frames to yield

        Yields:
            Frame strings
        """
        for i, frame in enumerate(itertools.cycle(self.frames)):
            if i >= count:
                break
            yield frame


class SpinnerContext:
    """
    Context manager for spinner with auto-cleanup.

    Usage:
        async with SpinnerContext("Loading...") as spinner:
            # Do work
            await spinner.update("Almost done...")
    """

    def __init__(
        self,
        initial_status: str = "",
        frames: list[str] | None = None,
        interval: float = 0.1,
        color: str = "#22D3EE",
    ) -> None:
        """Initialize context manager."""
        self.spinner = PremiumSpinner(frames, interval, color)
        self.status = initial_status
        self._task: asyncio.Task | None = None

    async def __aenter__(self) -> "SpinnerContext":
        """Start spinner task."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop spinner and cleanup."""
        self.spinner.stop()
        if self._task:
            self._task.cancel()

    def update(self, status: str) -> None:
        """Update status text."""
        self.status = status


def create_spinner(
    style: str = "dots",
    interval: float = 0.1,
    color: str = "#22D3EE",
) -> PremiumSpinner:
    """
    Create spinner with predefined style.

    Args:
        style: Spinner style ('dots', 'braille', 'line', 'bounce', 'arc')
        interval: Frame interval in seconds
        color: Rich markup color

    Returns:
        Configured PremiumSpinner instance
    """
    styles = {
        "dots": SPINNER_DOTS,
        "braille": SPINNER_BRAILLE,
        "line": SPINNER_LINE,
        "bounce": SPINNER_BOUNCE,
        "arc": SPINNER_ARC,
    }
    frames = styles.get(style, SPINNER_DOTS)
    return PremiumSpinner(frames, interval, color)
