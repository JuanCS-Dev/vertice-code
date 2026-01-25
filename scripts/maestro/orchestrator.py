"""Orchestrator - The Brain of Maestro."""
from datetime import datetime
from typing import Dict

from vertice_core.core.llm import LLMClient
from vertice_core.core.mcp_client import MCPClient
from vertice_core.agents.base import AgentTask, AgentResponse
from vertice_core.agents.planner import PlannerAgent
from vertice_core.agents.reviewer import ReviewerAgent
from vertice_core.agents.refactorer import RefactorerAgent
from vertice_core.agents.explorer import ExplorerAgent
from vertice_core.agents.executor import NextGenExecutorAgent, ExecutionMode, SecurityLevel
from vertice_core.agents.architect import ArchitectAgent
from vertice_core.agents.security import SecurityAgent
from vertice_core.agents.performance import PerformanceAgent
from vertice_core.agents.testing import TestRunnerAgent
from vertice_core.agents.documentation import DocumentationAgent
from vertice_core.agents.data_agent_production import create_data_agent
from vertice_core.agents.devops import create_devops_agent

from .routing import route_to_agent


class Orchestrator:
    """Routes tasks to appropriate v6.0 agents"""

    def __init__(self, llm_client: LLMClient, mcp_client: MCPClient, approval_callback=None):
        self.llm = llm_client
        self.mcp = mcp_client

        # Initialize REAL v6.0 Agents (order matters - Explorer first)
        explorer = ExplorerAgent(llm_client, mcp_client)

        self.agents = {
            "executor": NextGenExecutorAgent(
                llm_client=llm_client,
                mcp_client=mcp_client,
                execution_mode=ExecutionMode.LOCAL,  # Fast local execution
                security_level=SecurityLevel.PERMISSIVE,  # No approval required (per Architect request)
                approval_callback=None,  # Disabled: approval system too intrusive
                config={"timeout": 30.0, "max_retries": 3},
            ),
            "explorer": explorer,
            "planner": PlannerAgent(llm_client, mcp_client),
            "reviewer": ReviewerAgent(llm_client, mcp_client),
            "refactorer": RefactorerAgent(
                llm_client, mcp_client, explorer
            ),  # Pass explorer directly
            "architect": ArchitectAgent(llm_client, mcp_client),
            "security": SecurityAgent(llm_client, mcp_client),
            "performance": PerformanceAgent(llm_client, mcp_client),
            "testing": TestRunnerAgent(llm_client, mcp_client),
            "documentation": DocumentationAgent(llm_client, mcp_client),
            "data": create_data_agent(
                llm_client, mcp_client, enable_thinking=True
            ),  # DataAgent v1.0
            "devops": create_devops_agent(
                llm_client, mcp_client, auto_remediate=False, policy_mode="require_approval"
            ),  # DevOpsAgent v1.0
        }

    def route(self, prompt: str) -> str:
        """Delegate to routing module."""
        return route_to_agent(prompt)

    async def execute(self, prompt: str, context: Dict = None) -> AgentResponse:
        """Route and execute with real agents"""

        agent_name = self.route(prompt)
        agent = self.agents[agent_name]

        # Build AgentTask
        task = AgentTask(
            request=prompt,
            context=context or {},
            metadata={"interface": "maestro_v10", "timestamp": datetime.now().isoformat()},
        )

        # Execute REAL agent
        return await agent.execute(task)

    async def execute_streaming(self, prompt: str, context: Dict = None):
        """Route and execute with streaming support for 30 FPS.

        Yields updates from agent execution for real-time UI rendering.
        Only SimpleExecutorAgent currently supports streaming.
        """
        agent_name = self.route(prompt)
        agent = self.agents[agent_name]

        # Build AgentTask
        task = AgentTask(
            request=prompt,
            context=context or {},
            metadata={"interface": "maestro_v10", "timestamp": datetime.now().isoformat()},
        )

        # Check if agent supports streaming
        if hasattr(agent, "execute_streaming"):
            # Stream updates from agent
            async for update in agent.execute_streaming(task):
                yield update
        else:
            # Fallback: execute normally and yield final result
            result = await agent.execute(task)
            yield {"type": "result", "data": result}
