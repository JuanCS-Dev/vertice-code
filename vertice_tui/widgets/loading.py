"""
Loading Animations - Skeleton screens, shimmer, spinners.

Uses Textual's LoadingIndicator plus custom animations.

Phase 11: Visual Upgrade - Polish & Delight.
"""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, LoadingIndicator, ProgressBar
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
        self._render()

    def _render(self) -> None:
        frame = self._frames[self.frame_index]
        if self._text:
            self.update(f"[bold cyan]{frame}[/] {self._text}")
        else:
            self.update(f"[bold cyan]{frame}[/]")

    def set_text(self, text: str) -> None:
        """Update spinner text."""
        self._text = text
        self._render()


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
                yield SpinnerWidget(variant="dots", classes="loading-spinner")
                yield Static(self._message, classes="loading-text", id="loading-text")
            if self._show_progress:
                yield ProgressBar(total=100, show_eta=False, id="progress-bar")

    def set_message(self, message: str) -> None:
        """Update loading message."""
        self._message = message
        try:
            self.query_one("#loading-text", Static).update(message)
        except Exception:
            pass

    def set_progress(self, value: float) -> None:
        """Update progress (0-100)."""
        self.progress = value
        try:
            bar = self.query_one("#progress-bar", ProgressBar)
            bar.update(progress=value)
        except Exception:
            pass


class ThinkingIndicator(Widget):
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

    dots: reactive[int] = reactive(0)

    def __init__(
        self,
        text: str = "Thinking",
        id: Optional[str] = None,
    ) -> None:
        super().__init__(id=id)
        self._text = text
        self._timer = None

    def on_mount(self) -> None:
        self._timer = self.set_interval(0.4, self._advance_dots)
        self._render()

    def on_unmount(self) -> None:
        if self._timer:
            self._timer.stop()

    def _advance_dots(self) -> None:
        self.dots = (self.dots + 1) % 4

    def watch_dots(self) -> None:
        self._render()

    def _render(self) -> None:
        dots_str = "." * self.dots
        self.update(f"[italic]{self._text}{dots_str}[/]")


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
        self._render()

    def _render(self) -> None:
        if self.pulse:
            self.update("[bold green]●[/]")
        else:
            self.update("[dim green]○[/]")
