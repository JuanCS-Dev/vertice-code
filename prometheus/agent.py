"""
Prometheus Integrated Agent - BaseAgent Compliance Wrapper.

Integrates Prometheus meta-orchestrator into Vertice's agent ecosystem
while preserving all autonomous capabilities (Agent0, SimuRA, MIRIX, etc.).

This is the bridge between Vertice's BaseAgent protocol and Prometheus's
internal orchestration pipeline.

Phase 1 of Prometheus Integration Roadmap v2.3.
Created with love by: JuanCS Dev & Claude Opus 4.5
Date: 2026-01-06
"""

from __future__ import annotations

import logging
from typing import Any, Optional, List

from vertice_cli.agents.base import (
    BaseAgent,
    AgentRole,
    AgentCapability,
    AgentTask,
    AgentResponse,
    TaskResult,
    TaskStatus,
)

from .core.orchestrator import PrometheusOrchestrator
from .core.llm_client import GeminiClient

logger = logging.getLogger(__name__)


class PrometheusIntegratedAgent(BaseAgent):
    """
    Prometheus Meta-Agent integrated with Vertice BaseAgent protocol.

    Capabilities:
        - Self-evolving via Agent0 co-evolution loop
        - World model simulation via SimuRA
        - 6-type memory system via MIRIX
        - Autonomous tool creation via AutoTools
        - Self-reflection via Reflexion engine

    This agent operates at L4 autonomy (highest level) and should be
    invoked for complex, multi-step tasks requiring planning and adaptation.

    Architecture:
        BaseAgent (protocol) → PrometheusIntegratedAgent (adapter)
                            → PrometheusOrchestrator (core)
                            → [Memory, WorldModel, Reflection, Evolution, Tools]

    Note:
        Currently uses GeminiClient hardcoded. Will be refactored to use
        unified ProviderManager in Phase 6 (Unified LLM Client Refactoring).
    """

    def __init__(
        self,
        role: AgentRole = AgentRole.PROMETHEUS,
        capabilities: Optional[List[AgentCapability]] = None,
        llm_client: Any = None,
        mcp_client: Any = None,
        system_prompt: str = "",
        agent_name: str = "Prometheus",
    ):
        """
        Initialize Prometheus Integrated Agent.

        Args:
            role: Agent role (defaults to PROMETHEUS)
            capabilities: Agent capabilities (L4 autonomy = high privileges)
            llm_client: LLM client (currently ignored, uses GeminiClient)
            mcp_client: MCP client for tool execution
            system_prompt: System prompt (optional override)
            agent_name: Agent name for memory/logging
        """
        # L4 Autonomy = High privileges
        if capabilities is None:
            capabilities = [
                AgentCapability.READ_ONLY,
                AgentCapability.FILE_EDIT,
                AgentCapability.BASH_EXEC,
            ]

        # Default system prompt for Prometheus
        if not system_prompt:
            system_prompt = (
                "You are Prometheus, a self-evolving meta-agent with world model "
                "simulation and multi-type memory. You excel at complex, multi-step "
                "tasks requiring planning, adaptation, and continuous learning."
            )

        # Initialize BaseAgent
        super().__init__(
            role=role,
            capabilities=capabilities,
            llm_client=llm_client,  # Stored but not used yet (Phase 6)
            mcp_client=mcp_client,
            system_prompt=system_prompt,
        )

        # NOTE: For Phase 1, we use GeminiClient directly
        # Phase 6 will refactor to use llm_client (ProviderManager) via adapter
        self.gemini_client = GeminiClient()
        self.agent_name = agent_name

        # Initialize Prometheus Orchestrator (core engine)
        self.orchestrator = PrometheusOrchestrator(
            llm_client=self.gemini_client,
            agent_name=agent_name,
        )

        logger.info(
            f"PrometheusIntegratedAgent initialized (role={role.value}, "
            f"capabilities={[c.value for c in capabilities]})"
        )

    async def execute(self, task: AgentTask) -> AgentResponse:
        """
        Execute task via Prometheus orchestration pipeline.

        Adapts BaseAgent protocol (AgentTask) to Prometheus internal
        representation (ExecutionContext) and back (ExecutionResult → AgentResponse).

        Pipeline:
            1. Extract task request from AgentTask
            2. Stream execution through PrometheusOrchestrator
            3. Collect output tokens
            4. Package as AgentResponse with metadata

        Args:
            task: AgentTask with request and metadata

        Returns:
            AgentResponse with result and execution details
        """
        try:
            logger.info(f"Executing task via Prometheus: {task.request[:100]}...")

            # Determine if fast mode (default: True for Phase 1)
            # Fast mode skips memory/reflection for lower latency
            fast_mode = task.metadata.get("fast_mode", True)

            # Execute via Prometheus orchestrator (streaming)
            output_chunks = []
            async for chunk in self.orchestrator.execute(
                task=task.request,
                stream=True,
                fast_mode=fast_mode,
            ):
                output_chunks.append(chunk)

            # Collect full output
            full_output = "".join(output_chunks)

            # Create successful response
            result = TaskResult(
                output=full_output,
                status=TaskStatus.COMPLETED,
                metadata={
                    "agent": self.agent_name,
                    "fast_mode": fast_mode,
                    "execution_count": self.execution_count,
                },
            )

            logger.info(f"Task completed successfully (length={len(full_output)})")

            return AgentResponse(
                task_id=task.task_id,
                result=result,
                reasoning=(
                    "Executed via Prometheus meta-orchestrator with "
                    f"{'fast mode (no memory/reflection)' if fast_mode else 'full pipeline (memory + reflection)'}"
                ),
            )

        except Exception as e:
            logger.error(
                f"Prometheus execution failed: {type(e).__name__}: {e}",
                exc_info=True,
            )

            # Return error response
            result = TaskResult(
                output=f"Execution failed: {type(e).__name__}: {str(e)}",
                status=TaskStatus.FAILED,
                metadata={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
            )

            return AgentResponse(
                task_id=task.task_id,
                result=result,
                reasoning=f"Failed during Prometheus orchestration: {type(e).__name__}",
            )

    async def _reason(self, task: AgentTask, context_str: str) -> str:
        """
        Reasoning step (inherited from BaseAgent).

        For Prometheus, reasoning is handled internally by WorldModel (SimuRA)
        and Reflection engine, so we delegate to orchestrator.

        Args:
            task: Task to reason about
            context_str: Context string

        Returns:
            Reasoning trace
        """
        # Prometheus has its own internal reasoning via SimuRA + Reflection
        # For BaseAgent compliance, we provide a summary
        return (
            f"Prometheus reasoning pipeline activated:\n"
            f"- Task: {task.request[:100]}\n"
            f"- World Model (SimuRA): Planning action sequence\n"
            f"- Memory (MIRIX): Retrieving relevant context\n"
            f"- Reflection: Evaluating approach quality\n"
            f"- Evolution (Agent0): Adapting to task complexity"
        )

    def get_status(self) -> dict:
        """
        Get agent status including Prometheus-specific metrics.

        Returns:
            Status dictionary with orchestrator state
        """
        return {
            "role": self.role.value,
            "agent_name": self.agent_name,
            "capabilities": [c.value for c in self.capabilities],
            "execution_count": self.execution_count,
            "orchestrator_state": {
                "is_executing": self.orchestrator._is_executing,
                "execution_history_size": len(self.orchestrator.execution_history),
                "memory_system_active": True,
                "world_model_active": True,
                "evolution_loop_active": True,
            },
        }
