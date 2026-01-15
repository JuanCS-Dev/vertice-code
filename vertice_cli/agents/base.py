"""
Base agent implementation for Vertice CLI.

This module provides the foundation for all specialized agents,
including role and capability enforcement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from vertice_core.types import (
    AgentCapability,
    AgentRole,
    AgentTask,
    AgentResponse,
    CapabilityViolationError,
)


class BaseAgent(ABC):
    """Base class for all Vertice agents."""

    # Tool capability mappings
    TOOL_CAPABILITIES = {
        "read_file": AgentCapability.READ_ONLY,
        "list_files": AgentCapability.READ_ONLY,
        "grep_search": AgentCapability.READ_ONLY,
        "write_file": AgentCapability.FILE_EDIT,
        "edit_file": AgentCapability.FILE_EDIT,
        "delete_file": AgentCapability.FILE_EDIT,
        "bash_command": AgentCapability.BASH_EXEC,
        "git_commit": AgentCapability.GIT_OPS,
        "git_push": AgentCapability.GIT_OPS,
        "network_request": AgentCapability.NETWORK,
        "database_query": AgentCapability.DATABASE,
    }

    def __init__(
        self,
        role: AgentRole,
        capabilities: Optional[List[AgentCapability]] = None,
        llm_client: Optional[Any] = None,
        mcp_client: Optional[Any] = None,
        system_prompt: Optional[str] = None,
        name: Optional[str] = None,
    ):
        """Initialize the agent.

        Args:
            role: The agent's role
            capabilities: List of capabilities this agent has
            llm_client: LLM client for AI interactions
            mcp_client: MCP client for tool interactions
            system_prompt: System prompt for the agent
            name: Optional agent name
        """
        self.role = role
        self.capabilities = capabilities or []
        self.llm_client = llm_client
        self.mcp_client = mcp_client
        self.system_prompt = system_prompt or ""
        self.name = name or f"{role.value}_agent"
        self.execution_count = 0

    def check_capability(self, capability: AgentCapability) -> None:
        """Check if agent has the required capability.

        Args:
            capability: The capability to check

        Raises:
            CapabilityViolationError: If agent doesn't have the capability
        """
        if capability not in self.capabilities:
            raise CapabilityViolationError(
                f"Agent {self.name} does not have capability {capability.value}"
            )

    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has a capability.

        Args:
            capability: The capability to check

        Returns:
            True if agent has the capability, False otherwise
        """
        return capability in self.capabilities

    def _can_use_tool(self, tool_name: str) -> bool:
        """Check if agent can use a specific tool based on capabilities.

        Args:
            tool_name: Name of the tool

        Returns:
            True if agent can use the tool, False otherwise
        """
        required_capability = self.TOOL_CAPABILITIES.get(tool_name)
        if required_capability is None:
            return False
        return self.has_capability(required_capability)

    async def call_llm(self, prompt: str, **kwargs) -> str:
        """Call the LLM with a prompt.

        Args:
            prompt: The prompt to send
            **kwargs: Additional arguments

        Returns:
            The LLM response
        """
        if self.llm_client is None:
            raise ValueError("LLM client not configured")
        self.execution_count += 1
        return await self.llm_client.generate(prompt, **kwargs)

    async def _call_llm(self, prompt: str, **kwargs) -> str:
        """Internal LLM call method."""
        return await self.call_llm(prompt, **kwargs)

    async def _execute_tool(self, tool_name: str, args: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a tool if capability allows.

        Args:
            tool_name: Name of the tool to execute
            args: Tool arguments dict

        Returns:
            Tool execution result

        Raises:
            CapabilityViolationError: If agent doesn't have required capability
        """
        if not self._can_use_tool(tool_name):
            raise CapabilityViolationError(f"Agent {self.role.value} cannot use tool {tool_name}")

        if self.mcp_client is None:
            raise ValueError("MCP client not configured")

        kwargs = args or {}
        return await self.mcp_client.call_tool(tool_name=tool_name, arguments=kwargs)

    @abstractmethod
    async def execute(self, task: AgentTask) -> AgentResponse:
        """Execute a task.

        Args:
            task: The task to execute

        Returns:
            The task response
        """
        pass
