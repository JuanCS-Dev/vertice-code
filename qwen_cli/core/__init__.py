"""
QWEN CLI Core - Integration Bridge
===================================

Minimal bridge connecting the beautiful TUI to the powerful agent system.

Components:
- GeminiClient: Streaming LLM via Gemini API (optimized Nov 2025)
- AgentManager: Lazy loading of 13 agents
- GovernanceObserver: ELP alerts without blocking
- ToolBridge: 47 tools via registry
- CommandPaletteBridge: Fuzzy search commands
- AutocompleteBridge: Context-aware fuzzy matching
- HistoryManager: Persistent command & context history
- OutputFormatter: Rich Panel formatting for responses
- ToolCallParser: Extract and execute tool calls from LLM
"""

from .bridge import (
    Bridge,
    GeminiClient,
    AgentManager,
    GovernanceObserver,
    RiskLevel,
    ToolBridge,
    CommandPaletteBridge,
    AutocompleteBridge,
    HistoryManager,
    ToolCallParser,
    get_bridge,
)
from .output_formatter import OutputFormatter

__all__ = [
    "Bridge",
    "GeminiClient",
    "AgentManager",
    "GovernanceObserver",
    "RiskLevel",
    "ToolBridge",
    "CommandPaletteBridge",
    "AutocompleteBridge",
    "HistoryManager",
    "ToolCallParser",
    "OutputFormatter",
    "get_bridge",
]
