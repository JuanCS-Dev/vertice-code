"""
Image Preview - Display images in terminal using textual-image.

Uses textual-image package for rendering via:
- Terminal Graphics Protocol (Kitty, WezTerm)
- Sixel (xterm, Windows Terminal)
- Unicode fallback

Phase 11: Visual Upgrade - Polish & Delight.

Install: pip install textual-image[textual]
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static
from textual.widget import Widget
from textual.message import Message

# Try to import textual-image
try:
    from textual_image.widget import Image as TextualImage

    TEXTUAL_IMAGE_AVAILABLE = True
except ImportError:
    TEXTUAL_IMAGE_AVAILABLE = False


class ImagePreview(Widget):
    """
    Image preview widget using textual-image.

    Falls back to placeholder if textual-image not installed.

    Usage:
        yield ImagePreview("/path/to/image.png")
        yield ImagePreview(image_bytes, format="png")
    """

    DEFAULT_CSS = """
    ImagePreview {
        width: 100%;
        height: auto;
        min-height: 5;
        background: $surface;
        border: solid $border;
    }

    ImagePreview .image-header {
        height: 1;
        background: $panel;
        padding: 0 1;
    }

    ImagePreview .image-content {
        width: 100%;
        height: auto;
        min-height: 3;
    }

    ImagePreview .image-fallback {
        padding: 1;
        text-align: center;
        color: $text-muted;
    }
    """

    class ImageLoaded(Message):
        """Image was loaded successfully."""

        def __init__(self, path: str) -> None:
            self.path = path
            super().__init__()

    class ImageError(Message):
        """Failed to load image."""

        def __init__(self, error: str) -> None:
            self.error = error
            super().__init__()

    def __init__(
        self,
        source: Union[str, Path, bytes],
        format: Optional[str] = None,
        title: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(id=id)
        self._source = source
        self._format = format
        self._title = title or self._get_title()

    def _get_title(self) -> str:
        """Get title from source."""
        if isinstance(self._source, (str, Path)):
            return Path(self._source).name
        return "Image"

    def compose(self) -> ComposeResult:
        yield Static(f"🖼️ {self._title}", classes="image-header")

        if TEXTUAL_IMAGE_AVAILABLE:
            try:
                if isinstance(self._source, bytes):
                    # For bytes, textual-image needs file-like or path
                    yield Static("[Image from bytes - save to view]", classes="image-fallback")
                else:
                    yield TextualImage(str(self._source), classes="image-content")
            except Exception as e:
                yield Static(f"[Error: {e}]", classes="image-fallback")
        else:
            yield Static(
                "[textual-image not installed]\n" "pip install textual-image[textual]",
                classes="image-fallback",
            )

    def on_mount(self) -> None:
        if isinstance(self._source, (str, Path)):
            self.post_message(self.ImageLoaded(str(self._source)))


class ImageGallery(Widget):
    """
    Gallery widget for multiple images.

    Displays images in a grid or list layout.
    """

    DEFAULT_CSS = """
    ImageGallery {
        width: 100%;
        height: auto;
    }

    ImageGallery > Vertical {
        width: 100%;
        height: auto;
    }

    ImageGallery ImagePreview {
        margin-bottom: 1;
    }
    """

    def __init__(
        self,
        images: Optional[list[Union[str, Path]]] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(id=id)
        self._images = list(images) if images else []

    def compose(self) -> ComposeResult:
        with Vertical():
            for img_path in self._images:
                yield ImagePreview(img_path)

    def add_image(self, path: Union[str, Path]) -> None:
        """Add image to gallery."""
        self._images.append(path)
        try:
            container = self.query_one("Vertical")
            container.mount(ImagePreview(path))
        except (AttributeError, ValueError, RuntimeError):
            pass

    def clear(self) -> None:
        """Clear all images."""
        self._images.clear()
        try:
            container = self.query_one("Vertical")
            container.remove_children()
        except (AttributeError, ValueError, RuntimeError):
            pass


def check_image_support() -> dict:
    """Check available image rendering support."""
    result = {
        "textual_image": TEXTUAL_IMAGE_AVAILABLE,
        "protocols": [],
    }

    if TEXTUAL_IMAGE_AVAILABLE:
        try:
            from textual_image import renderable

            # Check available protocols
            result["protocols"] = ["unicode"]  # Always available
            # TGP and Sixel detection would need terminal query
        except (ImportError, AttributeError):
            pass

    return result
