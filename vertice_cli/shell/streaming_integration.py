"""
Streaming Integration - LLM streaming response handling.

Provides unified streaming interface for LLM responses with:
- Visual feedback during streaming
- Token tracking
- Error handling
- Context integration

Design Principles:
- Single entry point for streaming
- Provider-agnostic (works with any LLM client)
- Integrated with context awareness engine
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console

logger = logging.getLogger(__name__)


async def stream_llm_response(
    llm_client: Any,
    prompt: str,
    console: "Console",
    workflow_viz: Optional[Any] = None,
    context_engine: Optional[Any] = None,
    system_prompt: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """
    Stream LLM response with visual feedback.

    This is the main entry point for streaming LLM responses in the shell.
    It handles:
    - Streaming text chunks to console
    - Token tracking (if context_engine provided)
    - Workflow visualization (if workflow_viz provided)
    - Error recovery

    Args:
        llm_client: LLM client with generate or stream method
        prompt: User prompt
        console: Rich console for output
        workflow_viz: Optional workflow visualizer
        context_engine: Optional context awareness engine
        system_prompt: System instructions
        temperature: Generation temperature
        max_tokens: Maximum tokens to generate

    Returns:
        Complete response text

    Raises:
        Exception: If LLM call fails
    """
    # Build messages
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    # Track input tokens
    input_tokens = len(prompt) // 4  # Rough estimate
    if context_engine:
        context_engine.track_input(input_tokens)

    # Try streaming first
    if hasattr(llm_client, "stream_async"):
        return await _stream_async(
            llm_client,
            messages,
            console,
            context_engine,
            temperature,
            max_tokens,
        )

    # Fall back to non-streaming
    return await _generate_async(
        llm_client,
        messages,
        console,
        context_engine,
        temperature,
        max_tokens,
    )


async def _stream_async(
    llm_client: Any,
    messages: list,
    console: "Console",
    context_engine: Optional[Any],
    temperature: float,
    max_tokens: int,
) -> str:
    """Stream response using async streaming API."""
    chunks = []
    output_tokens = 0

    try:
        async for chunk in llm_client.stream_async(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            if chunk:
                chunks.append(chunk)
                console.print(chunk, end="")
                output_tokens += len(chunk) // 4

        console.print()  # Newline after stream

        # Track output tokens
        if context_engine:
            context_engine.track_output(output_tokens)

        return "".join(chunks)

    except Exception as e:
        logger.error(f"Streaming failed: {e}")
        raise


async def _generate_async(
    llm_client: Any,
    messages: list,
    console: "Console",
    context_engine: Optional[Any],
    temperature: float,
    max_tokens: int,
) -> str:
    """Generate response using non-streaming API with progress indicator."""
    try:
        with console.status("[cyan]Generating response...[/cyan]", spinner="dots"):
            response = await llm_client.generate_async(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        # Extract response text
        if isinstance(response, dict):
            text = response.get("content", response.get("text", str(response)))
            tokens = response.get("tokens_used", len(text) // 4)
        else:
            text = str(response)
            tokens = len(text) // 4

        # Display response
        console.print(text)

        # Track output tokens
        if context_engine:
            context_engine.track_output(tokens)

        return text

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise


class StreamingResponseHandler:
    """
    Handles streaming responses with state management.

    Provides more control over streaming behavior including:
    - Cancellation support
    - Progress tracking
    - Error recovery
    """

    def __init__(
        self,
        llm_client: Any,
        console: "Console",
        context_engine: Optional[Any] = None,
    ):
        self.llm_client = llm_client
        self.console = console
        self.context_engine = context_engine
        self._cancelled = False

    def cancel(self) -> None:
        """Cancel ongoing streaming."""
        self._cancelled = True

    def reset(self) -> None:
        """Reset handler state."""
        self._cancelled = False

    async def stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        show_progress: bool = True,
    ) -> str:
        """
        Stream LLM response with full control.

        Args:
            prompt: User prompt
            system_prompt: System instructions
            temperature: Generation temperature
            max_tokens: Maximum tokens
            show_progress: Whether to show progress indicator

        Returns:
            Complete response text
        """
        self.reset()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Track input
        if self.context_engine:
            self.context_engine.track_input(len(prompt) // 4)

        chunks = []
        output_tokens = 0

        try:
            if hasattr(self.llm_client, "stream_async"):
                async for chunk in self.llm_client.stream_async(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ):
                    if self._cancelled:
                        self.console.print("\n[yellow]Cancelled[/yellow]")
                        break

                    if chunk:
                        chunks.append(chunk)
                        self.console.print(chunk, end="")
                        output_tokens += len(chunk) // 4

                self.console.print()  # Newline

            else:
                # Non-streaming fallback
                if show_progress:
                    with self.console.status("[cyan]Generating...[/cyan]"):
                        response = await self.llm_client.generate_async(
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                        )
                else:
                    response = await self.llm_client.generate_async(
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )

                if isinstance(response, dict):
                    text = response.get("content", "")
                    output_tokens = response.get("tokens_used", len(text) // 4)
                else:
                    text = str(response)
                    output_tokens = len(text) // 4

                chunks.append(text)
                self.console.print(text)

            # Track output
            if self.context_engine:
                self.context_engine.track_output(output_tokens)

            return "".join(chunks)

        except asyncio.CancelledError:
            self.console.print("\n[yellow]Cancelled[/yellow]")
            return "".join(chunks)

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            raise
