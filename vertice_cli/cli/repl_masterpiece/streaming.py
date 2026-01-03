"""
REPL Masterpiece Streaming - Streaming Response Handler.

This module provides streaming response handling with
minimal output style.

Features:
- Token-by-token streaming
- Performance metrics
- Minimal output mode

Philosophy:
    "Streaming should feel like magic."
"""

from __future__ import annotations

import sys
import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .repl import MasterpieceREPL


async def stream_response(
    repl: "MasterpieceREPL",
    message: str,
    system: Optional[str] = None
) -> None:
    """
    Stream with MINIMAL OUTPUT (Nov 2025 style).

    Args:
        repl: Reference to MasterpieceREPL
        message: User message to process
        system: Optional system prompt
    """
    from vertice_cli.tui.minimal_output import StreamingMinimal

    repl.console.print("[dim]" + "─" * 60 + "[/dim]")

    buffer = []
    word_count = 0
    char_count = 0
    start_time = time.time()

    # Initialize streaming minimal
    streamer = StreamingMinimal() if repl.minimal_output else None

    # Initialize metrics
    if repl.token_metrics:
        repl.token_metrics.input_tokens = len(message.split())
        repl.token_metrics.output_tokens = 0

    try:
        async for chunk in repl.llm_client.stream_chat(
            prompt=message,
            context=system,
            max_tokens=4000,
            temperature=0.7
        ):
            buffer.append(chunk)
            char_count += len(chunk)

            # Streaming minimal mode
            if streamer:
                streamer.add_chunk(chunk)

                # Only show if under threshold
                if not streamer.should_truncate:
                    repl.console.print(chunk, end="", style="white")
            else:
                repl.console.print(chunk, end="", style="white")

            # Count words
            if ' ' in chunk or '\n' in chunk:
                word_count += len(chunk.split())

                # Update metrics
                if repl.token_metrics:
                    repl.token_metrics.output_tokens = word_count
                    elapsed = time.time() - start_time
                    if elapsed > 0:
                        repl.token_metrics.tokens_per_second = word_count / elapsed

            sys.stdout.flush()

        # Store full response for /expand
        full_response = ''.join(buffer)
        repl.last_response = full_response

        # Enhanced stats (minimal style)
        duration = time.time() - start_time
        wps = int(word_count / duration) if duration > 0 else 0

        repl.console.print()

        # Compact stats (Nov 2025 style)
        repl.console.print()
        repl.console.print("─" * 60)

        cost = None
        if repl.token_metrics and repl.token_metrics.estimated_cost > 0:
            cost = repl.token_metrics.cost_formatted

        stats_parts = [f"✓ {word_count} words in {duration:.1f}s ({wps} wps)"]
        if cost:
            stats_parts.append(cost)

        repl.console.print(f"[dim green]{' • '.join(stats_parts)}[/dim green]")
        repl.console.print()

    except Exception as e:
        repl.console.print(f"\n[red]❌ Error: {e}[/red]")
        repl.console.print("[yellow]💡 Tip: Check connection[/yellow]\n")


__all__ = ["stream_response"]
