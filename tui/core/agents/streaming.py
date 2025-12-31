"""
Streaming Utilities - Normalize agent streaming output.

Handles multiple agent streaming protocols for unified display.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from typing import Any


def normalize_streaming_chunk(chunk: Any) -> str:
    """
    Normalize streaming chunk from any agent protocol to displayable string.

    Handles multiple agent streaming protocols:
    1. StreamingChunk dataclass - New standard (preferred)
    2. Protocol A: {"content": "text"} - LLMAdapter style
    3. Protocol B: {"type": "thinking"/"status"/"result", "data": "text"} - Agent style
    4. Protocol C: tuple[str, Optional[AgentResponse]] - SofiaAgent style
    5. Plain string - Direct passthrough

    This unifies the streaming output from all agents to a single string format
    suitable for UI rendering.

    Args:
        chunk: Raw chunk from agent streaming

    Returns:
        String suitable for display/streaming to UI
    """
    # Case 0: StreamingChunk dataclass (new standard - preferred)
    # Uses duck typing to avoid import
    if hasattr(chunk, 'type') and hasattr(chunk, 'data') and hasattr(chunk, '__dataclass_fields__'):
        return str(chunk)  # StreamingChunk has __str__ method

    # Case 1: Already a string
    if isinstance(chunk, str):
        return chunk

    # Case 2: Tuple (SofiaAgent style) - (chunk_text, optional_response)
    if isinstance(chunk, tuple) and len(chunk) >= 1:
        return str(chunk[0]) if chunk[0] else ""

    # Case 3: Dict - multiple protocols
    if isinstance(chunk, dict):
        chunk_type = chunk.get('type', '')

        # Protocol A: {"content": "..."} - LLMAdapter
        if 'content' in chunk:
            return str(chunk['content'])

        # Protocol B: {"type": "...", "data": "..."} - Most agents
        if 'data' in chunk:
            data = chunk['data']

            # Skip certain types that are not for display
            if chunk_type == 'error':
                error_data = data if isinstance(data, dict) else {'error': str(data)}
                return f"❌ Error: {error_data.get('error', data)}\n"

            # Status messages - display with formatting
            if chunk_type == 'status':
                return f"{data}\n"

            # Thinking tokens - display raw for streaming effect
            if chunk_type == 'thinking':
                return str(data)

            # Command - display with syntax highlighting marker
            if chunk_type == 'command':
                return f"\n```bash\n{data}\n```\n"

            # Executing - show status
            if chunk_type == 'executing':
                return f"⚡ Executing: {data}\n"

            # Result - format appropriately (Claude Code style)
            if chunk_type == 'result':
                return _format_result_data(data)

            # Other types with data - just return data as string
            return str(data)

        # Protocol C: {"type": "...", "text": "..."} - Legacy executor
        if 'text' in chunk:
            return str(chunk['text'])

        # Fallback: silent - don't dump raw dicts
        return ""

    # Case 4: Has common attributes
    if hasattr(chunk, 'data'):
        return str(chunk.data)
    if hasattr(chunk, 'content'):
        return str(chunk.content)
    if hasattr(chunk, 'to_markdown'):
        return chunk.to_markdown()

    # Last resort: stringify
    return str(chunk) if chunk else ""


def _format_result_data(data: Any) -> str:
    """Format result data from agent response.

    Args:
        data: Result data to format

    Returns:
        Formatted string for display
    """
    # Extract the actual displayable content from result
    result_data = data

    # If it's an AgentResponse, get the inner data
    if hasattr(data, 'data'):
        result_data = data.data

    # Now handle the result_data appropriately
    if isinstance(result_data, dict):
        # Priority 1: formatted_markdown (PlannerAgent style)
        if 'formatted_markdown' in result_data:
            return result_data['formatted_markdown']

        # Priority 2: markdown field
        if 'markdown' in result_data:
            return result_data['markdown']

        # Priority 3: response/result text
        if 'response' in result_data:
            return str(result_data['response'])
        if 'result' in result_data:
            return str(result_data['result'])

        # Priority 4: stdout for executor results
        if 'stdout' in result_data:
            output_parts = []
            if result_data.get('command'):
                output_parts.append(f"$ {result_data['command']}")
            if result_data.get('stdout'):
                output_parts.append(result_data['stdout'])
            if result_data.get('stderr'):
                output_parts.append(f"stderr: {result_data['stderr']}")
            return '\n'.join(output_parts) if output_parts else ""

        # Priority 5: Don't dump raw dicts
        return ""

    elif hasattr(result_data, 'to_markdown'):
        return result_data.to_markdown()

    return str(result_data) if result_data else ""
