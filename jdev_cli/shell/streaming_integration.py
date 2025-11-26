"""Phase 2: Streaming integration for InteractiveShell.

This module provides streaming LLM responses with real-time visual feedback.
Integrates StreamingEngine and WorkflowVisualizer for a premium UX.
"""

import asyncio
import logging
from typing import AsyncGenerator

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

logger = logging.getLogger(__name__)


async def stream_llm_response(
    llm_client,
    prompt: str,
    console: Console,
    workflow_viz=None,
    context_engine=None,
    system_prompt: str = None
) -> str:
    """Stream LLM response with live visual feedback.
    
    Args:
        llm_client: LLM client with stream_chat method
        prompt: User prompt
        console: Rich console for output
        workflow_viz: Optional workflow visualizer
        context_engine: Optional context awareness engine
        system_prompt: Optional system prompt
        
    Returns:
        Complete response text
    """
    # Start workflow step
    step_id = "llm_response"
    if workflow_viz:
        workflow_viz.start_step(step_id, "Generating response")
    
    # Build messages
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    # Streaming output
    response_buffer = []
    token_count = 0
    
    try:
        # Show thinking indicator
        console.print()
        console.print("💭 ", end="", style="cyan")
        
        # Stream tokens
        async for token in llm_client.stream_chat(prompt=prompt, context=system_prompt):
            # Append to buffer
            response_buffer.append(token)
            token_count += 1
            
            # Live render token
            console.print(token, end="", markup=False)
            
            # Update workflow visualizer
            if workflow_viz:
                workflow_viz.add_streaming_token(step_id, token)
            
            # Update context engine
            if context_engine:
                context_engine.update_streaming_tokens(1)
        
        # Complete
        console.print()  # Newline
        console.print()
        
        if workflow_viz:
            workflow_viz.complete_step(step_id, "success")
        
        if context_engine:
            context_engine.finalize_streaming_session(token_count)
        
        # Return complete response
        complete_response = "".join(response_buffer)
        return complete_response
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        
        if workflow_viz:
            workflow_viz.complete_step(step_id, "failure")
        
        console.print(f"\n[red]❌ Streaming error: {e}[/red]")
        raise


async def stream_with_status_panel(
    llm_client,
    prompt: str,
    console: Console,
    title: str = "AI Response"
) -> str:
    """Stream response with live updating panel.
    
    This creates a beautiful live-updating panel with streaming text.
    Inspired by Claude Code and Cursor.
    """
    response_buffer = []
    
    def create_panel(text: str, done: bool = False) -> Panel:
        """Create panel with current response."""
        status_icon = "✅" if done else "💭"
        border_style = "green" if done else "cyan"
        
        return Panel(
            text or "[dim]Thinking...[/dim]",
            title=f"{status_icon} {title}",
            border_style=border_style,
            padding=(1, 2)
        )
    
    # Use Live for real-time updates
    with Live(create_panel(""), console=console, refresh_per_second=10) as live:
        try:
            async for token in llm_client.stream_chat(prompt=prompt):
                response_buffer.append(token)
                current_text = "".join(response_buffer)
                live.update(create_panel(current_text))
            
            # Final update with checkmark
            final_text = "".join(response_buffer)
            live.update(create_panel(final_text, done=True))
            
            return final_text
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            live.update(Panel(
                f"[red]Error: {e}[/red]",
                title="❌ Streaming Failed",
                border_style="red"
            ))
            raise


async def stream_command_execution(
    console: Console,
    command: str,
    executor_func,
    *args,
    **kwargs
) -> dict:
    """Execute command with streaming progress indicator.
    
    Args:
        console: Rich console
        command: Command being executed
        executor_func: Async function to execute
        *args, **kwargs: Args for executor_func
        
    Returns:
        Execution result
    """
    with console.status(
        f"[cyan]Executing:[/cyan] {command[:60]}...",
        spinner="dots"
    ):
        result = await executor_func(*args, **kwargs)
    
    return result
