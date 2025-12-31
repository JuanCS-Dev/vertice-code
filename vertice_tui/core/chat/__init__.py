"""
Chat Module - Core chat functionality.

Semantic Domain: All chat-related operations including:
- Streaming responses from LLM
- Tool call detection and execution
- Agent routing
- Context management

Architecture (CODE_CONSTITUTION compliant):
- controller.py: ChatController (<500 lines)
- loop.py: AgenticLoop - tool execution loop (<500 lines)
- types.py: Chat-related types and protocols

Following CODE_CONSTITUTION: <500 lines per file, 100% type hints
"""

from .controller import ChatController
from .types import ChatConfig, ChatResult

__all__ = [
    "ChatController",
    "ChatConfig",
    "ChatResult",
]
