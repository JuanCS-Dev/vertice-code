# Message and conversation types - Domain level

from __future__ import annotations

from typing import List, TypedDict
from enum import Enum


class MessageRole(str, Enum):
    """Role of a message in a conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(TypedDict, total=False):
    """Single message in a conversation.

    Required fields:
        role: Who sent the message
        content: The message text

    Optional fields:
        name: Name of the tool/function (for role="tool")
        tool_call_id: ID of the tool call this message responds to
    """

    role: MessageRole
    content: str
    name: str  # Optional
    tool_call_id: str  # Optional


MessageList = List[Message]
