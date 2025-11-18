"""Reactive TUI renderer with zero UI blocking."""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from collections import deque

from rich.console import Console


class RenderEventType(Enum):
    """Render event types."""
    OUTPUT = "output"
    PROGRESS = "progress"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class RenderEvent:
    """UI render event."""
    event_type: RenderEventType
    content: str
    metadata: dict


class ReactiveRenderer:
    """Reactive TUI renderer with zero blocking."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._render_task: Optional[asyncio.Task] = None
        self._output_buffer = deque(maxlen=1000)
    
    async def start(self) -> None:
        """Start renderer loop."""
        if self._running:
            return
        
        self._running = True
        self._render_task = asyncio.create_task(self._render_loop())
    
    async def stop(self) -> None:
        """Stop renderer loop."""
        if not self._running:
            return
        
        self._running = False
        if self._render_task:
            self._render_task.cancel()
            try:
                await self._render_task
            except asyncio.CancelledError:
                pass
    
    async def emit(self, event: RenderEvent) -> None:
        """Emit render event (non-blocking)."""
        await self._event_queue.put(event)
    
    async def _render_loop(self) -> None:
        """Main render loop (UI thread)."""
        try:
            while self._running:
                try:
                    event = await asyncio.wait_for(
                        self._event_queue.get(),
                        timeout=0.1
                    )
                except asyncio.TimeoutError:
                    continue
                
                await self._render_event(event)
        
        except asyncio.CancelledError:
            pass
    
    async def _render_event(self, event: RenderEvent) -> None:
        """Render single event."""
        if event.event_type == RenderEventType.OUTPUT:
            self.console.print(event.content, end='')
            self._output_buffer.append(event.content)
        
        elif event.event_type == RenderEventType.COMPLETE:
            self.console.print(f"[green]✓[/green] {event.content}")
        
        elif event.event_type == RenderEventType.ERROR:
            self.console.print(f"[red]✗[/red] {event.content}")
    
    def get_output_buffer(self) -> list[str]:
        """Get current output buffer."""
        return list(self._output_buffer)
