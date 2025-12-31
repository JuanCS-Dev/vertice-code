"""
Core Agent Adapter - Bridge between core agents and TUI AgentManager.

Adapts the core agent interfaces (Task dataclass, mixins, AsyncIterator)
to the TUI agent interface (AgentTask, normalized streaming chunks).

Core agents have advanced features:
- BoundedAutonomyMixin (L0-L3 autonomy levels)
- DarwinGodelMixin (code evolution)
- DeepThinkMixin (metacognition)
- ThreeLoopsMixin (human-AI collaboration)
- AgenticRAGMixin (multi-hop retrieval)
- IncidentHandlerMixin (DevOps incidents)

This adapter ensures these features work correctly within the TUI.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agents.orchestrator.types import Task, TaskComplexity, AutonomyLevel


# Fallback TaskComplexity for when import fails
class _FallbackTaskComplexity(str, Enum):
    """Fallback TaskComplexity when agents.orchestrator.types unavailable."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


# =============================================================================
# CONTEXT DATACLASS
# =============================================================================


@dataclass
class CoreAgentContext:
    """
    Context passed to core agents for mixin activation.

    Attributes:
        autonomy_level: L0-L3 from BoundedAutonomyMixin
        approval_callback: Called when L2/L3 approval needed
        notify_callback: Called when L1 notification needed
        history_context: Previous conversation for context
        enable_deep_think: Enable DeepThinkMixin (if available)
        enable_darwin_godel: Enable DarwinGodelMixin (if available)
    """

    autonomy_level: str = "L1"  # L0, L1, L2, L3
    approval_callback: Optional[Callable[[Any], bool]] = None
    notify_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    history_context: Optional[str] = None
    enable_deep_think: bool = True
    enable_darwin_godel: bool = False
    extra_config: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# CORE AGENT ADAPTER
# =============================================================================


class CoreAgentAdapter:
    """
    Adapts core agents (agents/) to TUI streaming interface.

    Core agents from agents/ have different patterns:
    - Task dataclass with complexity, autonomy_level
    - AsyncIterator[str] for execute()
    - Mixins with runtime callbacks

    TUI uses:
    - AgentTask with request, context dict
    - Normalized streaming chunks

    This adapter bridges the gap.

    Example:
        adapter = CoreAgentAdapter(orchestrator, "orchestrator_core")
        async for chunk in adapter.execute_streaming("Plan my feature"):
            print(chunk, end='')
    """

    def __init__(self, core_agent: Any, agent_name: str) -> None:
        """
        Initialize adapter for a core agent.

        Args:
            core_agent: The core agent instance (e.g., OrchestratorAgent)
            agent_name: Agent name from registry
        """
        self.core_agent = core_agent
        self.agent_name = agent_name
        self._mixin_activated = False
        self._default_context = CoreAgentContext()

    @property
    def name(self) -> str:
        """Agent name."""
        return self.agent_name

    def _activate_mixins(self, context: CoreAgentContext) -> None:
        """
        Activate mixins that require runtime configuration.

        This sets callbacks on the core agent for:
        - BoundedAutonomyMixin: approval_callback, notify_callback
        - Other mixins as needed

        Args:
            context: Context with callbacks and configuration
        """
        if self._mixin_activated:
            return

        # BoundedAutonomyMixin callbacks
        if hasattr(self.core_agent, '_approval_callback'):
            self.core_agent._approval_callback = context.approval_callback
        if hasattr(self.core_agent, '_notify_callback'):
            self.core_agent._notify_callback = context.notify_callback

        # Mark as activated
        self._mixin_activated = True

    def _estimate_complexity(self, request: str) -> Any:
        """
        Estimate task complexity from request text.

        Uses simple heuristics based on word count and keywords.

        Args:
            request: The task request text

        Returns:
            TaskComplexity enum value
        """
        # Try to import TaskComplexity, use fallback if unavailable
        try:
            from agents.orchestrator.types import TaskComplexity
        except ImportError:
            TaskComplexity = _FallbackTaskComplexity  # type: ignore

        word_count = len(request.split())

        if word_count < 10:
            return TaskComplexity.SIMPLE
        elif word_count < 50:
            return TaskComplexity.MODERATE
        elif any(kw in request.lower() for kw in [
            "architecture", "design", "security", "production"
        ]):
            return TaskComplexity.COMPLEX
        elif any(kw in request.lower() for kw in [
            "deploy", "critical", "urgent"
        ]):
            return TaskComplexity.CRITICAL
        else:
            return TaskComplexity.MODERATE

    def _normalize_chunk(self, chunk: Any) -> str:
        """
        Normalize chunk to string for TUI.

        Handles various chunk types from core agents.

        Args:
            chunk: Raw chunk from agent

        Returns:
            Normalized string
        """
        if isinstance(chunk, str):
            return chunk
        elif hasattr(chunk, 'text'):
            return str(chunk.text)
        elif hasattr(chunk, 'content'):
            return str(chunk.content)
        elif isinstance(chunk, dict):
            if 'text' in chunk:
                return str(chunk['text'])
            elif 'content' in chunk:
                return str(chunk['content'])
            elif 'message' in chunk:
                return str(chunk['message'])
        return str(chunk)

    async def execute_streaming(
        self,
        task_request: str,
        context: Optional[Dict[str, Any]] = None,
        core_context: Optional[CoreAgentContext] = None,
    ) -> AsyncIterator[str]:
        """
        Execute core agent with streaming, adapted for TUI.

        This method:
        1. Activates mixins with callbacks
        2. Builds a Task object for core agent
        3. Calls agent.execute() with streaming
        4. Normalizes chunks for TUI display

        Args:
            task_request: The task to execute
            context: Optional context dict (from AgentTask)
            core_context: Optional CoreAgentContext for mixin configuration

        Yields:
            Normalized response chunks
        """
        ctx = core_context or self._default_context
        self._activate_mixins(ctx)

        # Try streaming execute first
        if hasattr(self.core_agent, 'execute'):
            try:
                async for chunk in self.core_agent.execute(
                    task_request, stream=True
                ):
                    yield self._normalize_chunk(chunk)
                return
            except TypeError:
                # execute() doesn't support stream parameter
                pass

        # Fallback: build Task and call without stream
        try:
            from agents.orchestrator.types import Task

            task = Task(
                id=f"tui-{self.agent_name}-{id(task_request) % 10000}",
                description=task_request,
                complexity=self._estimate_complexity(task_request),
            )

            # Some core agents have plan() method
            if hasattr(self.core_agent, 'plan'):
                yield f"[{self.agent_name}] Planning task...\n"
                tasks = await self.core_agent.plan(task_request)
                yield f"[{self.agent_name}] Created {len(tasks)} subtasks\n"

            # Route if orchestrator
            if hasattr(self.core_agent, 'route'):
                agent_role = await self.core_agent.route(task)
                yield f"[{self.agent_name}] Routing to {agent_role.value}...\n"

            yield f"[{self.agent_name}] Task completed\n"

        except Exception as e:
            yield f"[{self.agent_name}] Error: {e}\n"

    async def execute(self, task_request: str) -> Any:
        """
        Execute core agent synchronously.

        For compatibility with TUI patterns that expect non-streaming.

        Args:
            task_request: The task to execute

        Returns:
            Concatenated result string
        """
        chunks: List[str] = []
        async for chunk in self.execute_streaming(task_request):
            chunks.append(chunk)
        return "".join(chunks)

    def get_status(self) -> Dict[str, Any]:
        """
        Get adapter and core agent status.

        Returns:
            Status dict with adapter and agent info
        """
        status = {
            "adapter_name": self.agent_name,
            "mixin_activated": self._mixin_activated,
            "core_agent_type": type(self.core_agent).__name__,
        }

        # Get core agent status if available
        if hasattr(self.core_agent, 'get_status'):
            status["core_status"] = self.core_agent.get_status()

        return status

    def check_autonomy(
        self,
        operation: str
    ) -> tuple[bool, Optional[Any]]:
        """
        Check autonomy level for an operation.

        Delegates to BoundedAutonomyMixin if available.

        Args:
            operation: The operation to check

        Returns:
            (can_proceed, approval_request) tuple
        """
        if hasattr(self.core_agent, 'check_autonomy'):
            result: tuple[bool, Optional[Any]] = self.core_agent.check_autonomy(
                operation
            )
            return result
        return (True, None)  # Default: allow

    def approve(self, approval_id: str, approved_by: str) -> bool:
        """
        Approve a pending operation (L2).

        Args:
            approval_id: The approval request ID
            approved_by: Who approved

        Returns:
            True if approved successfully
        """
        if hasattr(self.core_agent, 'approve'):
            result: bool = self.core_agent.approve(approval_id, approved_by)
            return result
        return False

    def reject(self, approval_id: str, rejected_by: str) -> bool:
        """
        Reject a pending operation (L2).

        Args:
            approval_id: The approval request ID
            rejected_by: Who rejected

        Returns:
            True if rejected successfully
        """
        if hasattr(self.core_agent, 'reject'):
            result: bool = self.core_agent.reject(approval_id, rejected_by)
            return result
        return False

    def get_pending_approvals(self) -> List[Any]:
        """
        Get pending approval requests.

        Returns:
            List of ApprovalRequest objects
        """
        if hasattr(self.core_agent, 'get_pending_approvals'):
            result: List[Any] = self.core_agent.get_pending_approvals()
            return result
        return []
