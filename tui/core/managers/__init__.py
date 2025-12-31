"""
Managers Module - Extracted Bridge Responsibilities.

Phase 5.1 TUI Lightweight - Complete Manager Extraction.

This module contains specialized managers extracted from the Bridge class
following the Facade pattern (Google Style Guide + Anthropic patterns).

Original Managers (Phase 1.1):
- TodoManager: TODO list management
- StatusManager: System health and permissions
- PullRequestManager: GitHub PR operations
- MemoryManager: Persistent memory (MEMORY.md)
- ContextManager: Conversation context management
- AuthenticationManager: API key management

New Managers (Phase 5.1):
- StreamingManager: Core chat streaming with tool execution loop
- ProviderManager: LLM provider selection and initialization

References:
- Anthropic: Single-threaded master loop pattern
- Google: https://google.github.io/styleguide/pyguide.html
- Facade: https://refactoring.guru/design-patterns/facade

Author: JuanCS Dev
Date: 2025-11-26 (Updated: 2025-12-30)
"""

from .todo_manager import TodoManager
from .status_manager import StatusManager
from .pr_manager import PullRequestManager
from .memory_manager import MemoryManager
from .context_manager import ContextManager
from .auth_manager import AuthenticationManager

# Phase 5.1: New streaming and provider managers
from .streaming_manager import StreamingManager, StreamingConfig
from .provider_manager import ProviderManager, ProviderConfig, TaskComplexity

# Phase 6.2: MCP integration
from .mcp_manager import MCPManager, MCPServerState, MCPClientConnection

# Phase 6.3: A2A integration
from .a2a_manager import A2AManager, A2AServerState, DiscoveredAgent

__all__ = [
    # Original managers
    'TodoManager',
    'StatusManager',
    'PullRequestManager',
    'MemoryManager',
    'ContextManager',
    'AuthenticationManager',
    # Phase 5.1 managers
    'StreamingManager',
    'StreamingConfig',
    'ProviderManager',
    'ProviderConfig',
    'TaskComplexity',
    # Phase 6.2: MCP
    'MCPManager',
    'MCPServerState',
    'MCPClientConnection',
    # Phase 6.3: A2A
    'A2AManager',
    'A2AServerState',
    'DiscoveredAgent',
]
