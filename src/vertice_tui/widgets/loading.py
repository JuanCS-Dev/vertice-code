"""
Loading Animations - Skeleton screens, shimmer, spinners.

Uses Textual's LoadingIndicator plus custom animations.

Phase 11: Visual Upgrade - Polish & Delight.
"""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, ProgressBar
from textual.reactive import reactive
from textual.widget import Widget


class SkeletonLine(Static):
    """Single skeleton line with shimmer effect."""

    DEFAULT_CSS = """
    SkeletonLine {
        width: 100%;
        height: 1;
        background: $surface-lighten-1;
    }

    SkeletonLine.short {
        width: 30%;
    }

    SkeletonLine.medium {
        width: 60%;
    }

    SkeletonLine.long {
        width: 90%;
    }
    """

    def __init__(
        self,
        length: str = "long",
        id: Optional[str] = None,
    ) -> None:
        super().__init__("", id=id)
        if length in ("short", "medium", "long"):
            self.add_class(length)


class SkeletonBlock(Widget):
    """
    Skeleton loading placeholder.

    Shows animated placeholder lines while content loads.
    """

    DEFAULT_CSS = """
    SkeletonBlock {
        width: 100%;
        height: auto;
        padding: 1;
        background: $surface;
        border: solid $border;
    }

    SkeletonBlock > Vertical {
        width: 100%;
        height: auto;
    }

    SkeletonBlock SkeletonLine {
        margin-bottom: 1;
    }
    """

    def __init__(
        self,
        lines: int = 3,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(id=id)
        self._lines = lines

    def compose(self) -> ComposeResult:
        with Vertical():
            patterns = ["long", "medium", "short", "long", "medium"]
            for i in range(self._lines):
                length = patterns[i % len(patterns)]
                yield SkeletonLine(length=length)


class SpinnerWidget(Static):
    """
    Animated spinner widget.

    Variants: dots, braille, line, bounce, arc
    """

    SPINNER_FRAMES = {
        "dots": ["◐", "◓", "◑", "◒"],
        "braille": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
        "line": ["|", "/", "-", "\\"],
        "bounce": ["⠁", "⠂", "⠄", "⠂"],
        "arc": ["◜", "◠", "◝", "◞", "◡", "◟"],
        "clock": ["🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚", "🕛"],
    }

    DEFAULT_CSS = """
    SpinnerWidget {
        width: auto;
        height: 1;
        color: $accent;
    }
    """

    frame_index: reactive[int] = reactive(0)

    def __init__(
        self,
        text: str = "",
        variant: str = "dots",
        id: Optional[str] = None,
    ) -> None:
        super().__init__("", id=id)
        self._text = text
        self._variant = variant
        self._frames = self.SPINNER_FRAMES.get(variant, self.SPINNER_FRAMES["dots"])
        self._timer = None

    def on_mount(self) -> None:
        self._timer = self.set_interval(0.1, self._advance_frame)
        self._render()

    def on_unmount(self) -> None:
        if self._timer:
            self._timer.stop()

    def _advance_frame(self) -> None:
        self.frame_index = (self.frame_index + 1) % len(self._frames)

    def watch_frame_index(self) -> None:
        self._update_display()

    def _update_display(self) -> None:
        frame = self._frames[self.frame_index]
        if self._text:
            self.update(f"[bold cyan]{frame}[/] {self._text}")
        else:
            self.update(f"[bold cyan]{frame}[/]")

    def set_text(self, text: str) -> None:
        """Update spinner text."""
        self._text = text
        self._update_display()


class LoadingCard(Widget):
    """
    Loading card with spinner and message.

    Shows animated loading state with optional progress.
    """

    DEFAULT_CSS = """
    LoadingCard {
        width: 100%;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: solid $primary;
    }

    LoadingCard > Horizontal {
        width: 100%;
        height: auto;
    }

    LoadingCard .loading-spinner {
        width: 3;
    }

    LoadingCard .loading-text {
        width: 1fr;
        padding-left: 1;
    }

    LoadingCard ProgressBar {
        margin-top: 1;
        width: 100%;
    }
    """

    progress: reactive[float] = reactive(0.0)

    def __init__(
        self,
        message: str = "Loading...",
        show_progress: bool = False,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(id=id)
        self._message = message
        self._show_progress = show_progress

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal():
                yield SpinnerWidget(variant="dots")
                yield Static(self._message, id="loading-text")
            if self._show_progress:
                yield ProgressBar(total=100, show_eta=False, id="progress-bar")

    def set_message(self, message: str) -> None:
        """Update loading message."""
        self._message = message
        try:
            self.query_one("#loading-text", Static).update(message)
        except (AttributeError, ValueError):
            pass

    def set_progress(self, value: float) -> None:
        """Update progress (0-100)."""
        self.progress = value
        try:
            bar = self.query_one("#progress-bar", ProgressBar)
            bar.update(progress=value)
        except (AttributeError, ValueError):
            pass


class ThinkingIndicator(Static):
    """
    AI thinking indicator with animated dots.

    Claude/ChatGPT style "thinking..." animation.
    """

    DEFAULT_CSS = """
    ThinkingIndicator {
        width: auto;
        height: 1;
        color: $text-muted;
    }
    """

    def __init__(
        self,
        text: str = "Thinking",
        id: Optional[str] = None,
    ) -> None:
        super().__init__("", id=id)
        self._text = text
        self._timer = None
        self._dots = 0
        self._update_display()

    def on_mount(self) -> None:
        self._timer = self.set_interval(0.4, self._advance_dots)

    def on_unmount(self) -> None:
        if self._timer:
            self._timer.stop()

    def _advance_dots(self) -> None:
        self._dots = (self._dots + 1) % 4
        self._update_display()

    def _update_display(self) -> None:
        dots_str = "." * self._dots
        self.update(f"[italic]{self._text}{dots_str}[/]")


class ReasoningStream(Static):
    """
    Advanced reasoning indicator showing Maestro's thought process in real-time.

    Shows keywords and phases of the Maestro's thinking:
    - "Analyzing request..."
    - "Decomposing task..."
    - "Routing to agents..."
    - "Coordinating execution..."
    - "Synthesizing results..."
    """

    DEFAULT_CSS = """
    ReasoningStream {
        width: 100%;
        height: 2;
        color: $accent;
        background: $surface;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        id: Optional[str] = None,
    ) -> None:
        super().__init__("", id=id)
        self._timer = None
        self._phase_index = 0
        self._reasoning_phases = [
            "Analyzing request",
            "Decomposing task",
            "Routing to agents",
            "Coordinating execution",
            "Synthesizing results",
            "Finalizing response",
        ]
        self._confidence_score = 0.0
        self._show_confidence = False
        self._update_display()

    def on_mount(self) -> None:
        """Start the reasoning animation."""
        self._timer = self.set_interval(0.8, self._advance_reasoning)

    def on_unmount(self) -> None:
        """Stop the reasoning animation."""
        if self._timer:
            self._timer.stop()

    def _advance_reasoning(self) -> None:
        """Advance to next reasoning phase."""
        self._phase_index = (self._phase_index + 1) % len(self._reasoning_phases)

        # Simulate increasing confidence
        if self._confidence_score < 95.0:
            self._confidence_score += 5.0

        self._update_display()

    def update_reasoning_phase(self, phase: str, confidence: Optional[float] = None) -> None:
        """Manually update the reasoning phase."""
        # Find closest matching phase or use custom
        if phase in self._reasoning_phases:
            self._phase_index = self._reasoning_phases.index(phase)
        else:
            # Insert custom phase temporarily
            self._reasoning_phases[self._phase_index] = phase

        if confidence is not None:
            self._confidence_score = confidence
            self._show_confidence = True

        self._update_display()

    def _update_display(self) -> None:
        """Update the display text."""
        phase = self._reasoning_phases[self._phase_index]
        phase_text = f"🤖 Maestro: {phase}..."

        if self._show_confidence and self._confidence_score > 0:
            confidence_text = f" ({self._confidence_score:.0f}% confidence)"
        else:
            confidence_text = ""

        # Add thinking dots animation
        dots = "." * ((self._phase_index % 3) + 1)

        full_text = f"[cyan]{phase_text}{confidence_text} {dots}[/cyan]"
        self.update(full_text)


class PulseIndicator(Static):
    """
    Pulsing dot indicator.

    Simple visual heartbeat for background processes.
    """

    DEFAULT_CSS = """
    PulseIndicator {
        width: 1;
        height: 1;
    }
    """

    pulse: reactive[bool] = reactive(True)

    def __init__(self, id: Optional[str] = None) -> None:
        super().__init__("", id=id)
        self._timer = None

    def on_mount(self) -> None:
        self._timer = self.set_interval(0.5, self._toggle_pulse)
        self._render()

    def on_unmount(self) -> None:
        if self._timer:
            self._timer.stop()

    def _toggle_pulse(self) -> None:
        self.pulse = not self.pulse

    def watch_pulse(self) -> None:
        self._update_display()

    def _update_display(self) -> None:
        if self.pulse:
            self.update("[bold green]●[/]")
        else:
            self.update("[dim green]○[/]")


__all__ = [
    "LoadingCard",
    "ThinkingIndicator",
    "ReasoningStream",
    "PulseIndicator",
]
