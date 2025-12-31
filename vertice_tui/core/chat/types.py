"""
Chat Types - Protocols and data structures for chat module.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Protocol


class LLMClientProtocol(Protocol):
    """Protocol for LLM clients (Gemini, Prometheus, Maximus)."""

    async def stream(
        self,
        message: str,
        system_prompt: str,
        context: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
    ) -> AsyncIterator[str]:
        """Stream response from LLM."""
        ...


class ToolBridgeProtocol(Protocol):
    """Protocol for tool bridge."""

    def get_schemas_for_llm(self) -> List[Dict[str, Any]]:
        """Get tool schemas for LLM."""
        ...

    async def execute(self, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a tool."""
        ...


class HistoryProtocol(Protocol):
    """Protocol for history manager."""

    def add_command(self, command: str) -> None:
        """Add command to history."""
        ...

    def add_context(self, role: str, content: str) -> None:
        """Add message to context."""
        ...

    def get_context(self) -> List[Dict[str, str]]:
        """Get conversation context."""
        ...


class GovernanceProtocol(Protocol):
    """Protocol for governance observer."""

    def observe(self, action: str, data: Any) -> str:
        """Observe an action and return report."""
        ...

    @property
    def config(self) -> Any:
        """Get governance config."""
        ...


class AgentRouterProtocol(Protocol):
    """Protocol for agent router."""

    def route(self, message: str) -> Optional[tuple]:
        """Route message to appropriate agent."""
        ...

    def get_routing_suggestion(self, message: str) -> Optional[str]:
        """Get routing suggestion for ambiguous messages."""
        ...


class AgentManagerProtocol(Protocol):
    """Protocol for agent manager."""

    @property
    def router(self) -> AgentRouterProtocol:
        """Get the router."""
        ...

    async def invoke(self, agent_name: str, message: str) -> AsyncIterator[str]:
        """Invoke an agent."""
        ...


@dataclass
class ChatConfig:
    """Configuration for chat behavior."""

    max_tool_iterations: int = 5
    max_parallel_tools: int = 5
    show_provider_indicator: bool = True
    show_parallel_stats: bool = True
    show_governance_alerts: bool = True
    auto_route_enabled: bool = True


@dataclass
class ToolExecutionResult:
    """Result of tool execution."""

    tool_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class ChatResult:
    """Result of a chat interaction."""

    response_parts: List[str] = field(default_factory=list)
    tool_calls_made: int = 0
    agent_used: Optional[str] = None
    provider_used: str = ""

    @property
    def full_response(self) -> str:
        """Get concatenated response."""
        return "".join(self.response_parts)
