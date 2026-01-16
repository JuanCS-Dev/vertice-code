"""
Streaming Adapter - Bridge between vertice_tui and streaming components.

Phase 9 Visual Refresh:
- 60fps for code blocks (16.67ms frame budget)
- 30fps for markdown (33.33ms frame budget)
- Smooth cursor animation (50ms)

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import asyncio
import threading
from typing import Callable, List, Optional

from textual.widgets import Static
from textual.containers import Container
from textual.reactive import reactive
from textual.message import Message

from rich.text import Text
from rich.markdown import Markdown as RichMarkdown
from rich.console import RenderableType, Group

# Import dos componentes de streaming de vertice_cli
from vertice_cli.tui.components.block_detector import BlockDetector
from vertice_cli.tui.components.streaming_markdown import (
    BlockWidgetFactory,
    RenderMode,
    PerformanceMetrics,
)

# Import colors for brand consistency
from vertice_tui.core.formatting import Colors

# Import tool sanitizer
from .tool_sanitizer import sanitize_tool_call_json


class StreamingResponseWidget(Static):
    """
    Drop-in replacement for SelectableStatic with streaming markdown.

    Interface compatível com ResponseView.append_chunk() - método SYNC!

    Features:
    - Markdown rendering durante streaming
    - Detecção de blocos (code, table, checklist)
    - Renderização especializada por tipo de bloco
    - Cursor pulsante durante streaming
    - Fallback para plain text em caso de performance baixa
    - 60fps code blocks, 30fps markdown

    Uso:
        # Em ResponseView.append_chunk():
        if self._response_widget is None:
            self._response_widget = StreamingResponseWidget()
            self.mount(self._response_widget)

        self._response_widget.append_chunk(chunk)  # SYNC!
    """

    DEFAULT_CSS = """
    StreamingResponseWidget {
        width: 100%;
        height: auto;
        min-height: 1;
        color: $foreground;
    }

    StreamingResponseWidget.streaming {
        border-left: solid $accent;
        padding-left: 1;
    }

    StreamingResponseWidget.plain-mode {
        border-left: dashed $warning;
    }
    """

    # Cursor animation frames (smoother animation)
    CURSOR_FRAMES = ["▋", "▌", "▍", "▎", "▏", "▏", "▎", "▍", "▌", "▋"]

    # Frame budgets (Phase 9: 60fps for code, 30fps for markdown)
    CODE_FRAME_BUDGET_MS = 16.67  # 60fps
    MARKDOWN_FRAME_BUDGET_MS = 33.33  # 30fps
    CURSOR_ANIMATION_MS = 50  # 20fps cursor (smooth enough)

    # Reactive properties
    is_streaming = reactive(False)

    class StreamCompleted(Message):
        """Emitido quando streaming termina."""

        def __init__(self, content: str, metrics: PerformanceMetrics):
            self.content = content
            self.metrics = metrics
            super().__init__()

    def __init__(self, *args, enable_markdown: bool = True, **kwargs):
        """
        Inicializa StreamingResponseWidget.

        Args:
            enable_markdown: Habilita renderização markdown (default: True)
        """
        # Always initialize with an empty string to prevent NotRenderableError
        # Static widget requires a valid renderable at all times
        super().__init__("", *args, **kwargs)

        self._content = ""
        self._enable_markdown = enable_markdown

        # Streaming components
        self._block_detector = BlockDetector()
        self._widget_factory = BlockWidgetFactory()
        self._metrics = PerformanceMetrics()

        # Cursor state with thread-safety lock
        self._cursor_index = 0
        self._cursor_lock = threading.Lock()  # Protege _cursor_index
        self._cursor_task: Optional[asyncio.Task] = None

        # Render mode
        self._render_mode = RenderMode.MARKDOWN if enable_markdown else RenderMode.PLAIN_TEXT

        # Flag para cleanup seguro (with async lock for thread-safety)
        self._is_finalizing = False
        self._finalize_lock = asyncio.Lock()

        # Deduplication: track last N lines to detect LLM repetitions
        self._last_lines: List[str] = []
        self._max_line_history = 10

    def on_mount(self) -> None:
        """Chamado quando widget é montado."""
        self.is_streaming = True
        self.add_class("streaming")

        # Inicia animação do cursor
        self._cursor_task = asyncio.create_task(self._animate_cursor())

    def append_chunk(self, chunk: str) -> None:
        """
        Append chunk - SYNC interface compatível com ResponseView.

        Esta é a interface principal. É chamada de forma síncrona
        pelo ResponseView.append_chunk().

        Implements throttling to maintain 60fps (16.67ms between renders).

        Args:
            chunk: Texto a adicionar ao stream
        """
        import time
        import re

        # =================================================================
        # BLINDAGEM 1: Sanitizar Rich markup que o LLM gerou erroneamente
        # =================================================================
        chunk = re.sub(
            r"\[/?(?:bold|italic|dim|underline|strike|blink|reverse|#[0-9a-fA-F]{6}|"
            r"red|green|blue|yellow|magenta|cyan|white|black|"
            r"bright_\w+|rgb\([^)]+\)|on\s+\w+)[^\]]*\]",
            "",
            chunk,
        )

        # =================================================================
        # BLINDAGEM 2: Converter JSON tool calls em exibição amigável
        # Detecta {"tool": "bash_command", "args": {...}} e converte
        # =================================================================
        chunk = sanitize_tool_call_json(chunk)

        # =================================================================
        # BLINDAGEM 3: Fix malformed code fences from Gemini
        # Based on 2026 research: Gemini CLI has known markdown bugs (P1)
        # Patterns:
        #   - ```markdown → render as actual markdown, not code
        #   - ```html<html> → ```html\n<html>  (language + content on same line)
        #   - ```lang```lang → ```lang  (duplicated fence marker)
        # =================================================================
        # Fix: Remove ```markdown wrapper (LLM outputs markdown as code block)
        # This allows the content to be rendered as actual formatted markdown
        chunk = re.sub(r"^```markdown\s*\n?", "", chunk)
        chunk = re.sub(r"\n?```\s*$", "", chunk)  # Closing fence at end

        # Fix: ```lang```lang duplication (e.g., ```html```html)
        chunk = re.sub(r"```(\w+)```\1", r"```\1", chunk)

        # Fix: ```lang<content> on same line → split to newline
        # Match: ```html<html> (HTML/XML tags immediately after language)
        # Simplified pattern to avoid false positives with identifiers
        chunk = re.sub(r"```(\w+)(<[^>\n]+>)", r"```\1\n\2", chunk)

        # Fix: ```lang{ or ```lang[ (JSON/object literals after language)
        chunk = re.sub(r"```(\w+)([\{\[])", r"```\1\n\2", chunk)

        # =================================================================
        # BLINDAGEM 4: Inline deduplication (same-line repetition)
        # Based on 2026 research: LLMs can repeat content within same line
        # Patterns:
        #   - </body></body> → </body>  (HTML tag duplication)
        #   - </div></div> → </div>
        #   - word word → word  (immediate word repetition at boundaries)
        # =================================================================
        # Fix: Duplicated HTML closing tags
        chunk = re.sub(r"(</\w+>)\1+", r"\1", chunk)

        # Fix: Duplicated HTML opening tags (less common but possible)
        chunk = re.sub(r"(<\w+[^>]*>)\1+", r"\1", chunk)

        # Fix: Immediate word/token duplication (word word → word)
        # Only at word boundaries to avoid false positives
        chunk = re.sub(r"\b(\w{3,})\s+\1\b", r"\1", chunk)

        # DEDUPLICATION: Remove LLM-generated duplicate lines
        # Split chunk into lines and filter duplicates
        if "\n" in chunk:
            lines = chunk.split("\n")
            filtered_lines = []

            for line in lines:
                line_stripped = line.strip()

                # Skip empty lines
                if not line_stripped:
                    filtered_lines.append(line)
                    continue

                # Check if this line is a duplicate of recent lines
                is_duplicate = False
                for prev_line in self._last_lines[-5:]:  # Check last 5 lines
                    prev_stripped = prev_line.strip()

                    # Exact match
                    if line_stripped == prev_stripped:
                        is_duplicate = True
                        break

                    # PREFIX DEDUPLICATION: Detect "echo" pattern where partial
                    # line was shown and now full line arrives
                    # e.g., prev="Verde (Pronto para" curr="Verde (Pronto para Deploy):"
                    # In this case, we should REPLACE the prefix with the full line
                    if len(prev_stripped) > 10 and line_stripped.startswith(prev_stripped):
                        # Current line extends previous - not a dup, but remove prefix from content
                        # Actually, this means the previous line was incomplete
                        # We should keep the new (complete) line
                        is_duplicate = False
                        # Don't break - allow this line through
                        continue

                    # REVERSE PREFIX: New line is prefix of existing line
                    # e.g., curr="Verde (Pronto para" prev="Verde (Pronto para Deploy):"
                    # This means LLM is echoing a partial - skip the new partial
                    if len(line_stripped) > 10 and prev_stripped.startswith(line_stripped):
                        is_duplicate = True
                        break

                if not is_duplicate:
                    filtered_lines.append(line)
                    # Track this line for future dedup
                    self._last_lines.append(line_stripped)
                    # Keep only last N lines
                    if len(self._last_lines) > self._max_line_history:
                        self._last_lines.pop(0)

            chunk = "\n".join(filtered_lines)

        self._content += chunk

        # Processa com block detector (incremental)
        self._block_detector.process_chunk(chunk)

        # Adaptive frame budget: 60fps for code, 30fps for markdown
        current_time = time.time()
        if not hasattr(self, "_last_update_time"):
            self._last_update_time = 0.0
            self._pending_update = False
            self._in_code_block = False

        # Detect if we're inside a code block (``` markers)
        if "```" in chunk:
            self._in_code_block = not getattr(self, "_in_code_block", False)

        # Select frame budget based on content type
        frame_budget_ms = (
            self.CODE_FRAME_BUDGET_MS if self._in_code_block else self.MARKDOWN_FRAME_BUDGET_MS
        )
        frame_budget_s = frame_budget_ms / 1000.0

        time_since_last = current_time - self._last_update_time

        # Update if frame budget exceeded or newline (flush)
        if time_since_last >= frame_budget_s or chunk.endswith("\n"):
            self._update_display()
            self._last_update_time = current_time
            self._pending_update = False
        else:
            self._pending_update = True

    def _update_display(self) -> None:
        """Atualiza o display com conteúdo atual."""
        if self._is_finalizing:
            return  # Não atualiza durante finalização

        if self._render_mode == RenderMode.PLAIN_TEXT:
            renderable = self._render_plain_text()
        else:
            try:
                renderable = self._render_with_blocks()
            except Exception as e:
                # Log para debugging (não silencia mais)
                import logging

                logging.warning(f"StreamingResponseWidget render error: {e}")
                renderable = self._render_plain_text()

        self.update(renderable)

    def _get_cursor_index(self) -> int:
        """Thread-safe access ao cursor index."""
        with self._cursor_lock:
            return self._cursor_index

    def _advance_cursor(self) -> None:
        """Thread-safe advance do cursor."""
        with self._cursor_lock:
            self._cursor_index = (self._cursor_index + 1) % len(self.CURSOR_FRAMES)

    def _render_plain_text(self) -> Text:
        """Renderiza como plain text."""
        text = Text(self._content)

        # Cursor pulsante (thread-safe) - Orange brand color
        if self.is_streaming and not self._is_finalizing:
            cursor = self.CURSOR_FRAMES[self._get_cursor_index()]
            text.append(cursor, style=f"bold {Colors.PRIMARY}")

        return text

    def _render_with_blocks(self) -> RenderableType:
        """Renderiza usando Widget Factory para blocos especializados."""
        blocks = self._block_detector.get_all_blocks()

        if not blocks:
            # Sem blocos, usa markdown simples
            content = self._content
            if self.is_streaming and not self._is_finalizing:
                content += self.CURSOR_FRAMES[self._get_cursor_index()]
            try:
                return RichMarkdown(content)
            except Exception as e:
                import logging

                logging.warning(f"RichMarkdown error: {e}")
                return Text(content)

        # Renderiza cada bloco com widget especializado
        renderables = []
        for block in blocks:
            rendered = self._widget_factory.render_block(block)
            renderables.append(rendered)

        # Cursor no final (thread-safe) - Orange brand color
        if self.is_streaming and not self._is_finalizing:
            cursor_text = Text()
            cursor_text.append(
                self.CURSOR_FRAMES[self._get_cursor_index()], style=f"bold {Colors.PRIMARY}"
            )
            renderables.append(cursor_text)

        return Group(*renderables) if renderables else Text("")

    async def _animate_cursor(self) -> None:
        """
        Anima o cursor durante streaming.

        Also flushes any pending updates from throttling.
        Phase 9: 50ms cursor animation (20fps - smooth enough)
        """
        while self.is_streaming and not self._is_finalizing:
            self._advance_cursor()  # Thread-safe

            # Flush pending updates if any (from throttling)
            if getattr(self, "_pending_update", False):
                self._pending_update = False

            self._update_display()
            await asyncio.sleep(self.CURSOR_ANIMATION_MS / 1000.0)  # 50ms

    async def finalize(self) -> None:
        """
        Finaliza streaming e aplica formatação final.

        Thread-safe: uses asyncio.Lock to prevent concurrent finalization.
        Deve ser chamado quando o streaming terminar.
        """
        async with self._finalize_lock:
            # Skip if already finalized
            if self._is_finalizing:
                return

            # Set flag BEFORE cleanup to prevent race conditions
            self._is_finalizing = True
            self.is_streaming = False
            self.remove_class("streaming")

            # Cancel cursor animation safely with timeout
            if self._cursor_task and not self._cursor_task.done():
                self._cursor_task.cancel()
                try:
                    await asyncio.wait_for(asyncio.shield(self._cursor_task), timeout=1.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
                except Exception as e:
                    import logging

                    logging.warning(f"Error cancelling cursor task: {e}")
                finally:
                    self._cursor_task = None

            # Final render (without cursor) - still inside lock
            self._update_display()

            # Emit completion event
            self.post_message(self.StreamCompleted(self._content, self._metrics))

            # Reset flag AFTER all cleanup is complete
            self._is_finalizing = False

    def finalize_sync(self) -> None:
        """
        Versão sync de finalize() para uso em contextos síncronos.

        Uses call_later to execute async finalization.
        FIX 2.2: Delegate entirely to async version to avoid race conditions.
        """
        # FIX 2.2: Don't set flags here - let the async version handle it
        # with proper locking to avoid race conditions
        self.call_later(self._finalize_async_safe)

    async def _finalize_async_safe(self) -> None:
        """
        FIX 2.2: Thread-safe async finalization with proper locking.
        Delegates to finalize() which already uses the lock.
        """
        await self.finalize()

    async def _finalize_async(self) -> None:
        """Helper async para finalize_sync (legacy, use _finalize_async_safe)."""
        if self._cursor_task and not self._cursor_task.done():
            self._cursor_task.cancel()
            try:
                await self._cursor_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                import logging

                logging.warning(f"Error cancelling cursor task: {e}")
            finally:
                self._cursor_task = None

        # Render final
        self._is_finalizing = False
        self._update_display()
        self.post_message(self.StreamCompleted(self._content, self._metrics))

    def get_content(self) -> str:
        """Retorna o conteúdo acumulado."""
        return self._content

    def get_metrics(self) -> PerformanceMetrics:
        """Retorna métricas de performance."""
        return self._metrics

    def set_render_mode(self, mode: str) -> None:
        """
        Define modo de renderização.

        Args:
            mode: "markdown" ou "plain_text"
        """
        if mode == "markdown":
            self._render_mode = RenderMode.MARKDOWN
            self.remove_class("plain-mode")
        else:
            self._render_mode = RenderMode.PLAIN_TEXT
            self.add_class("plain-mode")

        self._update_display()


class StreamingMarkdownAdapter:
    """
    Adapter de alto nível para integração com ResponseView.

    Encapsula a lógica de criação e gerenciamento do widget,
    expondo uma interface ainda mais simples.

    Uso:
        adapter = StreamingMarkdownAdapter(response_view)
        adapter.start()
        for chunk in stream:
            adapter.append(chunk)
        adapter.finish()
    """

    def __init__(
        self,
        container: Container,
        on_complete: Optional[Callable[[str], None]] = None,
    ):
        """
        Inicializa o adapter.

        Args:
            container: Container onde montar o widget (ex: ResponseView)
            on_complete: Callback chamado quando streaming termina
        """
        self._container = container
        self._on_complete = on_complete
        self._widget: Optional[StreamingResponseWidget] = None
        self._content = ""

    def start(self) -> StreamingResponseWidget:
        """
        Inicia sessão de streaming.

        Returns:
            Widget criado
        """
        self._widget = StreamingResponseWidget()
        self._container.mount(self._widget)
        self._content = ""
        return self._widget

    def append(self, chunk: str) -> None:
        """
        Adiciona chunk ao stream.

        Args:
            chunk: Texto a adicionar
        """
        if self._widget:
            self._widget.append_chunk(chunk)
            self._content += chunk

    def finish(self) -> str:
        """
        Finaliza streaming.

        Returns:
            Conteúdo completo
        """
        if self._widget:
            self._widget.finalize_sync()

            if self._on_complete:
                self._on_complete(self._content)

        return self._content

    def get_widget(self) -> Optional[StreamingResponseWidget]:
        """Retorna o widget atual."""
        return self._widget

    def get_content(self) -> str:
        """Retorna o conteúdo acumulado."""
        return self._content
