"""
Vercel AI SDK Data Stream Protocol Helper

Implements the streaming text format expected by @ai-sdk/react useChat hook.
Reference: https://sdk.vercel.ai/docs/ai-sdk-ui/stream-protocol#data-stream-protocol

Protocol format:
- 0:"text" - Text chunk
- 2:[array] - Data array (for tool calls, etc.)
- d:{"finishReason":"stop"} - Finish signal
- 3:"error" - Error message
"""

import json
from typing import Any


def escape_text(text: str) -> str:
    """
    Escape text for JSON string embedding in stream protocol.
    Handles newlines, quotes, backslashes, and other special chars.
    """
    # Use json.dumps to properly escape, then strip the outer quotes
    return json.dumps(text)[1:-1]


def format_text_chunk(text: str) -> str:
    """
    Format a text chunk for streaming.

    Format: 0:"escaped_text"\n
    Type 0 = text-delta in Vercel AI SDK protocol

    Example:
        format_text_chunk("Hello") -> '0:"Hello"\n'
        format_text_chunk("Line1\nLine2") -> '0:"Line1\\nLine2"\n'
    """
    escaped = escape_text(text)
    return f'0:"{escaped}"\n'


def format_data(data: Any) -> str:
    """
    Format a data payload for streaming.

    Format: 2:[data]\n
    Type 2 = data in Vercel AI SDK protocol
    """
    return f"2:{json.dumps(data)}\n"


def format_message_annotation(annotation: dict) -> str:
    """
    Format a message annotation (metadata).

    Format: 8:[annotation]\n
    Type 8 = message-annotation in Vercel AI SDK protocol
    """
    return f"8:[{json.dumps(annotation)}]\n"


def format_finish(reason: str = "stop", usage: dict | None = None) -> str:
    """
    Format the finish signal.

    Format: d:{"finishReason":"stop",...}\n
    Type d = finish in Vercel AI SDK protocol

    Args:
        reason: The finish reason (stop, length, tool-calls, etc.)
        usage: Optional token usage stats
    """
    finish_data = {"finishReason": reason}
    if usage:
        finish_data["usage"] = usage
    return f"d:{json.dumps(finish_data)}\n"


def format_error(message: str) -> str:
    """
    Format an error message for streaming.

    Format: 3:"error_message"\n
    Type 3 = error in Vercel AI SDK protocol
    """
    escaped = escape_text(message)
    return f'3:"{escaped}"\n'


def format_tool_call(tool_call_id: str, tool_name: str, args: dict) -> str:
    """
    Format a tool call for streaming.

    Format: 9:{...}\n
    Type 9 = tool-call in Vercel AI SDK protocol
    """
    tool_data = {"toolCallId": tool_call_id, "toolName": tool_name, "args": args}
    return f"9:{json.dumps(tool_data)}\n"


def format_tool_result(tool_call_id: str, result: Any) -> str:
    """
    Format a tool result for streaming.

    Format: a:{...}\n
    Type a = tool-result in Vercel AI SDK protocol
    """
    result_data = {"toolCallId": tool_call_id, "result": result}
    return f"a:{json.dumps(result_data)}\n"


# OpenAI Responses Protocol Functions (for protocol="open_responses")
def format_done() -> str:
    """Format done signal for OpenAI Responses protocol."""
    return "event: done\ndata: [DONE]\n\n"


def format_response_created(response_id: str, model: str) -> str:
    """Format response.created event."""
    data = {"type": "response.created", "response_id": response_id, "model": model}
    return f"event: response.created\ndata: {json.dumps(data)}\n\n"


def format_response_in_progress(response_id: str) -> str:
    """Format response.in_progress event."""
    data = {"type": "response.in_progress", "response_id": response_id}
    return f"event: response.in_progress\ndata: {json.dumps(data)}\n\n"


def format_response_failed(response_id: str, error: dict, sequence: int) -> str:
    """Format response.failed event."""
    data = {"type": "response.failed", "response_id": response_id, "error": error, "sequence": sequence}
    return f"event: response.failed\ndata: {json.dumps(data)}\n\n"


def format_response_completed(response_id: str, usage: dict, sequence: int) -> str:
    """Format response.completed event."""
    data = {"type": "response.completed", "response_id": response_id, "usage": usage, "sequence": sequence}
    return f"event: response.completed\ndata: {json.dumps(data)}\n\n"


def format_output_item_added(item_id: str) -> str:
    """Format output_item.added event."""
    data = {"type": "output_item.added", "item_id": item_id}
    return f"event: output_item.added\ndata: {json.dumps(data)}\n\n"


def format_output_item_done(item_id: str, sequence: int) -> str:
    """Format output_item.done event."""
    data = {"type": "output_item.done", "item_id": item_id, "sequence": sequence}
    return f"event: output_item.done\ndata: {json.dumps(data)}\n\n"


def format_content_part_added(item_id: str) -> str:
    """Format content_part.added event."""
    data = {"type": "content_part.added", "item_id": item_id}
    return f"event: content_part.added\ndata: {json.dumps(data)}\n\n"


def format_content_part_done(item_id: str, sequence: int) -> str:
    """Format content_part.done event."""
    data = {"type": "content_part.done", "item_id": item_id, "sequence": sequence}
    return f"event: content_part.done\ndata: {json.dumps(data)}\n\n"


def format_output_text_delta(item_id: str, text: str, sequence: int) -> str:
    """Format output_text.delta event."""
    data = {"type": "output_text.delta", "item_id": item_id, "text": text, "sequence": sequence}
    return f"event: output_text.delta\ndata: {json.dumps(data)}\n\n"


def format_output_text_done(item_id: str, text: str, sequence: int) -> str:
    """Format output_text.done event."""
    data = {"type": "output_text.done", "item_id": item_id, "text": text, "sequence": sequence}
    return f"event: output_text.done\ndata: {json.dumps(data)}\n\n"


# Convenience function for safe streaming with error handling
def create_error_stream():
    """
    Generator that yields a properly formatted error response.
    Use when LLM fails but you want to still send a valid stream.
    """
    yield format_text_chunk(
        "I apologize, but I encountered an error processing your request. Please try again."
    )
    yield format_finish("error")
