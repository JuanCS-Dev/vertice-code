"""
Orchestrator Integration - Central coordination via OrchestratorAgent.

Enables Three Loops pattern for human-AI collaboration in TUI.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .manager import AgentManager
    from .core_adapter import CoreAgentAdapter


# =============================================================================
# ORCHESTRATION CONTEXT
# =============================================================================


@dataclass
class OrchestrationContext:
    """
    Context for orchestrated execution.

    Attributes:
        request_id: Unique request identifier
        autonomy_level: L0-L3 autonomy level
        approval_pending: Waiting for human approval
        sub_tasks: Decomposed sub-tasks
        executed_tasks: Already executed tasks
        history: Execution history for context
    """

    request_id: str = ""
    autonomy_level: str = "L1"
    approval_pending: bool = False
    sub_tasks: List[Dict[str, Any]] = field(default_factory=list)
    executed_tasks: List[str] = field(default_factory=list)
    history: List[str] = field(default_factory=list)


# =============================================================================
# ORCHESTRATOR INTEGRATION
# =============================================================================


class OrchestratorIntegration:
    """
    Integrates OrchestratorAgent with TUI for coordinated execution.

    Uses the core OrchestratorAgent (from agents/orchestrator/) as the
    central coordinator, enabling:
    - Task decomposition and routing
    - BoundedAutonomyMixin for approval workflows
    - Three Loops collaboration pattern

    Example:
        integration = OrchestratorIntegration(agent_manager)
        async for chunk in integration.execute_orchestrated("Build auth"):
            print(chunk, end='')
    """

    def __init__(self, agent_manager: "AgentManager") -> None:
        """
        Initialize orchestrator integration.

        Args:
            agent_manager: The TUI AgentManager instance
        """
        self.agent_manager = agent_manager
        self._orchestrator: Optional["CoreAgentAdapter"] = None
        self._context = OrchestrationContext()
        self._approval_queue: List[Dict[str, Any]] = []

    async def _get_orchestrator(self) -> Optional["CoreAgentAdapter"]:
        """
        Get or load the OrchestratorAgent (wrapped in CoreAgentAdapter).

        Returns:
            CoreAgentAdapter wrapping OrchestratorAgent, or None if unavailable
        """
        if self._orchestrator is not None:
            return self._orchestrator

        # Try to get from agent manager (will be wrapped by CoreAgentAdapter)
        orchestrator = await self.agent_manager.get_agent("orchestrator_core")
        if orchestrator is not None:
            self._orchestrator = orchestrator
            return self._orchestrator

        return None

    async def execute_orchestrated(
        self, request: str, context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """
        Execute request through the orchestrator.

        Falls back to direct routing if orchestrator unavailable.

        Args:
            request: User request to execute
            context: Optional context dict

        Yields:
            Response chunks as strings
        """
        orchestrator = await self._get_orchestrator()

        if orchestrator is None:
            # Fallback: direct routing without orchestration
            yield "[Fallback: Orchestrator unavailable, using direct routing]\n\n"
            async for chunk in self.agent_manager.invoke("planner", request, context):
                yield chunk
            return

        # Use orchestrator for coordinated execution
        yield f"[Orchestrator] Analyzing request...\n"

        try:
            # Execute through CoreAgentAdapter's streaming interface
            async for chunk in orchestrator.execute_streaming(request, context):
                yield chunk

                # Track execution for context
                self._context.history.append(chunk)

        except Exception as e:
            yield f"\n[Orchestrator] Error: {e}\n"
            yield "[Fallback] Routing to planner...\n\n"
            async for chunk in self.agent_manager.invoke("planner", request, context):
                yield chunk

    async def request_approval(self, operation: str, details: Dict[str, Any]) -> AsyncIterator[str]:
        """
        Request human approval for L2 operations.

        Args:
            operation: Operation requiring approval
            details: Operation details

        Yields:
            Approval request message
        """
        approval_id = f"approval-{len(self._approval_queue)}"
        self._approval_queue.append(
            {"id": approval_id, "operation": operation, "details": details, "status": "pending"}
        )

        yield f"\n**Approval Required** (L2)\n"
        yield f"Operation: {operation}\n"
        if details.get("reason"):
            yield f"Reason: {details['reason']}\n"
        yield f"\nUse `/approve {approval_id}` or `/reject {approval_id}`\n"

    def approve(self, approval_id: str, approved_by: str = "user") -> bool:
        """
        Approve a pending operation.

        Args:
            approval_id: The approval request ID
            approved_by: Who approved

        Returns:
            True if approved successfully
        """
        for item in self._approval_queue:
            if item["id"] == approval_id and item["status"] == "pending":
                item["status"] = "approved"
                item["approved_by"] = approved_by
                return True
        return False

    def reject(self, approval_id: str, rejected_by: str = "user") -> bool:
        """
        Reject a pending operation.

        Args:
            approval_id: The approval request ID
            rejected_by: Who rejected

        Returns:
            True if rejected successfully
        """
        for item in self._approval_queue:
            if item["id"] == approval_id and item["status"] == "pending":
                item["status"] = "rejected"
                item["rejected_by"] = rejected_by
                return True
        return False

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """
        Get all pending approval requests.

        Returns:
            List of pending approval dicts
        """
        return [a for a in self._approval_queue if a["status"] == "pending"]

    def get_status(self) -> Dict[str, Any]:
        """
        Get orchestrator integration status.

        Returns:
            Status dict with orchestrator and approval info
        """
        return {
            "orchestrator_available": self._orchestrator is not None,
            "autonomy_level": self._context.autonomy_level,
            "pending_approvals": len(self.get_pending_approvals()),
            "executed_tasks": len(self._context.executed_tasks),
            "history_entries": len(self._context.history),
        }

    def set_autonomy_level(self, level: str) -> bool:
        """
        Set the autonomy level for orchestration.

        Args:
            level: L0, L1, L2, or L3

        Returns:
            True if valid level set
        """
        valid_levels = {"L0", "L1", "L2", "L3"}
        if level.upper() in valid_levels:
            self._context.autonomy_level = level.upper()
            return True
        return False

    def clear_history(self) -> None:
        """Clear execution history."""
        self._context.history.clear()
        self._context.executed_tasks.clear()
        self._approval_queue.clear()
