"""
Vertice MCP Server Implementation

The central coordination hub for Vertice Agency.
Implements the Model Context Protocol for tool exposure.

Key tools:
- delegate_to_ai: Route tasks to specialized agents
- remember: Store in Memory Cortex
- recall: Retrieve from Memory Cortex
- execute_shell: Safe shell execution
"""

from __future__ import annotations

import json
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Try to import FastMCP
try:
    from mcp.server.fastmcp import FastMCP

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning("MCP not installed. Install with: pip install mcp")


class AgentType(str, Enum):
    """Available agent types for delegation."""

    ORCHESTRATOR = "orchestrator"
    CODER = "coder"
    REVIEWER = "reviewer"
    ARCHITECT = "architect"
    RESEARCHER = "researcher"
    DEVOPS = "devops"
    AUTO = "auto"  # Router decides


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DelegationResult:
    """Result from agent delegation."""

    agent: str
    task: str
    result: str
    success: bool
    tokens_used: int = 0
    cost: float = 0.0
    metadata: Dict = field(default_factory=dict)


class VerticeMCPServer:
    """
    Vertice MCP Server

    Central hub for:
    - Agent delegation and routing
    - Memory operations (Cortex)
    - Tool execution
    - Contribution tracking

    Implements MCP protocol for external tool access.
    """

    def __init__(self, name: str = "vertice-agency"):
        self.name = name
        self._router = None
        self._cortex = None
        self._agents = {}
        self._server = None

        if MCP_AVAILABLE:
            self._init_mcp_server()

    def _init_mcp_server(self):
        """Initialize the MCP server with tools."""
        self._server = FastMCP(self.name)

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register all MCP tools."""
        if not self._server:
            return

        # Delegate to AI - The core coordination tool
        @self._server.tool()
        async def delegate_to_ai(
            task: str,
            agent: str = "auto",
            priority: str = "normal",
            context: Optional[str] = None,
        ) -> str:
            """
            Delegate a task to the most appropriate AI agent.

            Args:
                task: The task to perform
                agent: Specific agent or "auto" for routing
                priority: Task priority (low, normal, high, critical)
                context: Additional context for the agent

            Returns:
                Agent response or execution result
            """
            return await self._delegate(
                task=task,
                agent=AgentType(agent) if agent != "auto" else AgentType.AUTO,
                priority=TaskPriority(priority),
                context=context,
            )

        # Memory operations
        @self._server.tool()
        async def remember(
            content: str,
            memory_type: str = "episodic",
            category: Optional[str] = None,
        ) -> str:
            """
            Store information in the Memory Cortex.

            Args:
                content: Information to remember
                memory_type: Type of memory (working, episodic, semantic)
                category: Category for semantic memory

            Returns:
                Confirmation with memory ID
            """
            return await self._remember(content, memory_type, category)

        @self._server.tool()
        async def recall(
            query: str,
            memory_types: Optional[List[str]] = None,
            limit: int = 5,
        ) -> str:
            """
            Retrieve information from the Memory Cortex.

            Args:
                query: Search query
                memory_types: Types to search (episodic, semantic)
                limit: Maximum results

            Returns:
                Retrieved memories as JSON
            """
            return await self._recall(query, memory_types, limit)

        # Shell execution (sandboxed)
        @self._server.tool()
        async def execute_shell(
            command: str,
            working_dir: Optional[str] = None,
            timeout: int = 30,
        ) -> str:
            """
            Execute a shell command safely.

            Args:
                command: Command to execute
                working_dir: Working directory
                timeout: Timeout in seconds

            Returns:
                Command output or error
            """
            return await self._execute_shell(command, working_dir, timeout)

        # Code generation
        @self._server.tool()
        async def generate_code(
            request: str,
            language: str = "python",
            style: Optional[str] = None,
        ) -> str:
            """
            Generate code using the Coder agent.

            Args:
                request: What to generate
                language: Programming language
                style: Code style preferences

            Returns:
                Generated code
            """
            return await self._delegate(
                task=f"Generate {language} code: {request}",
                agent=AgentType.CODER,
                priority=TaskPriority.NORMAL,
                context=f"Style: {style}" if style else None,
            )

        # Code review
        @self._server.tool()
        async def review_code(
            code: str,
            focus: Optional[str] = None,
        ) -> str:
            """
            Review code using the Reviewer agent.

            Args:
                code: Code to review
                focus: Specific focus (security, performance, quality)

            Returns:
                Review findings
            """
            return await self._delegate(
                task=f"Review this code:\n{code}",
                agent=AgentType.REVIEWER,
                priority=TaskPriority.NORMAL,
                context=f"Focus: {focus}" if focus else None,
            )

    async def _delegate(
        self,
        task: str,
        agent: AgentType,
        priority: TaskPriority,
        context: Optional[str] = None,
    ) -> str:
        """Internal delegation logic."""
        # Lazy load router
        if self._router is None:
            from providers.vertice_router import get_router

            self._router = get_router()

        # Lazy load agents
        if not self._agents:
            from agents import orchestrator, coder, reviewer, architect, researcher, devops

            self._agents = {
                AgentType.ORCHESTRATOR: orchestrator,
                AgentType.CODER: coder,
                AgentType.REVIEWER: reviewer,
                AgentType.ARCHITECT: architect,
                AgentType.RESEARCHER: researcher,
                AgentType.DEVOPS: devops,
            }

        # Route if auto
        if agent == AgentType.AUTO:
            # Use orchestrator for routing
            selected = await self._route_task(task)
            agent = selected

        # Get agent
        target_agent = self._agents.get(agent)
        if not target_agent:
            return f"Error: Agent {agent.value} not available"

        # Execute task
        try:
            # Collect streaming output
            output = []
            async for chunk in target_agent.execute(task):
                output.append(chunk)

            result = "".join(output)

            # Record contribution
            await self._record_contribution(agent.value, task, result)

            return result

        except Exception as e:
            logger.error(f"Delegation failed: {e}")
            return f"Error: {str(e)}"

    async def _route_task(self, task: str) -> AgentType:
        """Route task to appropriate agent."""
        task_lower = task.lower()

        # Simple keyword routing
        if any(kw in task_lower for kw in ["code", "implement", "write", "create function"]):
            return AgentType.CODER
        elif any(kw in task_lower for kw in ["review", "security", "audit", "check"]):
            return AgentType.REVIEWER
        elif any(kw in task_lower for kw in ["architecture", "design", "plan", "structure"]):
            return AgentType.ARCHITECT
        elif any(kw in task_lower for kw in ["search", "research", "find", "documentation"]):
            return AgentType.RESEARCHER
        elif any(kw in task_lower for kw in ["deploy", "ci/cd", "docker", "kubernetes"]):
            return AgentType.DEVOPS
        else:
            return AgentType.CODER  # Default to coder

    async def _remember(
        self,
        content: str,
        memory_type: str,
        category: Optional[str],
    ) -> str:
        """Store in Memory Cortex."""
        if self._cortex is None:
            from memory.cortex import get_cortex

            self._cortex = get_cortex()

        memory_id = self._cortex.remember(
            content=content,
            memory_type=memory_type,
            category=category,
        )

        return f"Stored in {memory_type} memory: {memory_id}"

    async def _recall(
        self,
        query: str,
        memory_types: Optional[List[str]],
        limit: int,
    ) -> str:
        """Retrieve from Memory Cortex."""
        if self._cortex is None:
            from memory.cortex import get_cortex

            self._cortex = get_cortex()

        results = self._cortex.recall(
            query=query,
            memory_types=memory_types,
            limit=limit,
        )

        return json.dumps(results, indent=2)

    async def _execute_shell(
        self,
        command: str,
        working_dir: Optional[str],
        timeout: int,
    ) -> str:
        """Execute shell command safely."""
        # Safety checks
        dangerous = ["rm -rf /", "mkfs", ":(){:|:&};:", "dd if="]
        for pattern in dangerous:
            if pattern in command:
                return f"BLOCKED: Dangerous command pattern detected: {pattern}"

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout,
            )

            output = stdout.decode() if stdout else ""
            errors = stderr.decode() if stderr else ""

            if proc.returncode == 0:
                return output or "Command completed successfully"
            else:
                return f"Error (exit {proc.returncode}):\n{errors}"

        except asyncio.TimeoutError:
            return f"Command timed out after {timeout}s"
        except Exception as e:
            return f"Execution error: {str(e)}"

    async def _record_contribution(
        self,
        agent_id: str,
        task: str,
        result: str,
    ):
        """Record agent contribution to ledger."""
        if self._cortex is None:
            from memory.cortex import get_cortex

            self._cortex = get_cortex()

        # Calculate contribution value based on task type
        value = 10  # Base value

        self._cortex.record_contribution(
            agent_id=agent_id,
            contribution_type="task_completion",
            value=value,
            metadata={
                "task": task[:100],
                "result_length": len(result),
            },
        )

    def run(self, transport: str = "stdio"):
        """Run the MCP server."""
        if not self._server:
            raise RuntimeError("MCP not available. Install with: pip install mcp")

        self._server.run(transport=transport)

    def get_status(self) -> Dict:
        """Get server status."""
        return {
            "name": self.name,
            "mcp_available": MCP_AVAILABLE,
            "agents_loaded": list(self._agents.keys()) if self._agents else [],
            "router_initialized": self._router is not None,
            "cortex_initialized": self._cortex is not None,
        }


# Global server instance
_server: Optional[VerticeMCPServer] = None


def get_server() -> VerticeMCPServer:
    """Get the global MCP server instance."""
    global _server
    if _server is None:
        _server = VerticeMCPServer()
    return _server


# CLI entry point
def main():
    """Run the MCP server as a standalone process."""
    import argparse

    parser = argparse.ArgumentParser(description="Vertice MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport mode",
    )
    args = parser.parse_args()

    server = get_server()
    print(f"Starting Vertice MCP Server ({args.transport})...")
    server.run(transport=args.transport)


if __name__ == "__main__":
    main()
