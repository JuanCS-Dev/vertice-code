"""
Agency Coordinator - Unified Entry Point for VERTICE Orchestration.

This module provides a facade that coordinates between the three
existing orchestrators without modifying them:

1. OrchestratorAgent (agents/orchestrator/)
   - Bounded Autonomy (L0-L3)
   - Task decomposition and routing
   - Approval/notification callbacks

2. ActiveOrchestrator (vertice_core/agents/orchestrator.py)
   - State machine (11 states)
   - ExecutionPlan with retry logic
   - UnifiedContext management

3. DevSquad (vertice_cli/orchestration/squad.py)
   - 5-phase workflow (Architecture → Review)
   - Multi-agent coordination
   - Human approval gates

Design Principles:
    - Non-invasive: Does NOT modify existing orchestrators
    - Safe: Delegates to existing, tested code
    - Flexible: Chooses orchestrator based on task type
    - Observable: Logs all coordination decisions

Author: JuanCS Dev
Date: 2025-12-31
Soli Deo Gloria
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND TYPES
# =============================================================================


class OrchestratorType(Enum):
    """Type of orchestrator to use."""
    CORE = auto()      # OrchestratorAgent - for L0-L3 decisions
    STATE = auto()     # ActiveOrchestrator - for complex state workflows
    SQUAD = auto()     # DevSquad - for 5-phase dev tasks
    AUTO = auto()      # Let coordinator decide


class TaskCategory(Enum):
    """Category of task for routing."""
    SIMPLE_QUERY = "simple_query"           # L0: Just answer
    CODE_CHANGE = "code_change"             # L1: Execute + notify
    ARCHITECTURE = "architecture"            # L2: Requires approval
    PRODUCTION = "production"                # L3: Human only
    FULL_FEATURE = "full_feature"           # DevSquad 5-phase
    COMPLEX_WORKFLOW = "complex_workflow"    # ActiveOrchestrator


@dataclass
class CoordinationDecision:
    """Record of a coordination decision."""
    orchestrator: OrchestratorType
    category: TaskCategory
    confidence: float
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoordinationResult:
    """Result of coordinated execution."""
    success: bool
    orchestrator_used: OrchestratorType
    output: Any
    decisions: List[CoordinationDecision] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# AGENCY COORDINATOR
# =============================================================================


class AgencyCoordinator:
    """
    Unified coordinator for VERTICE orchestration.

    This is a facade that provides a single entry point for all
    orchestration needs, delegating to the appropriate orchestrator
    based on task type and complexity.

    Usage:
        coordinator = AgencyCoordinator()

        # Auto-select orchestrator
        async for chunk in coordinator.execute("Implement login feature"):
            print(chunk)

        # Force specific orchestrator
        async for chunk in coordinator.execute(
            "Review code changes",
            orchestrator=OrchestratorType.CORE
        ):
            print(chunk)

    Orchestrator Selection Logic:
        - Simple queries → OrchestratorAgent (L0)
        - Code changes → OrchestratorAgent (L1) or DevSquad
        - Architecture decisions → OrchestratorAgent (L2)
        - Production deploys → OrchestratorAgent (L3)
        - Full features → DevSquad (5-phase)
        - Complex workflows → ActiveOrchestrator (state machine)
    """

    # Keywords for task categorization
    CATEGORY_KEYWORDS = {
        TaskCategory.SIMPLE_QUERY: [
            "what is", "explain", "how does", "show me", "list",
            "describe", "tell me", "why", "when", "where",
        ],
        TaskCategory.CODE_CHANGE: [
            "fix", "update", "change", "modify", "refactor",
            "add", "remove", "rename", "move", "optimize",
        ],
        TaskCategory.ARCHITECTURE: [
            "design", "architect", "structure", "pattern",
            "migration", "rewrite", "redesign", "api change",
        ],
        TaskCategory.PRODUCTION: [
            "deploy", "production", "release", "publish",
            "database migration", "security", "credentials",
        ],
        TaskCategory.FULL_FEATURE: [
            "implement", "create feature", "build", "develop",
            "new feature", "full implementation", "end to end",
        ],
        TaskCategory.COMPLEX_WORKFLOW: [
            "workflow", "pipeline", "orchestrate", "coordinate",
            "multi-step", "complex task", "long running",
        ],
    }

    # Mapping from category to orchestrator
    CATEGORY_ORCHESTRATOR = {
        TaskCategory.SIMPLE_QUERY: OrchestratorType.CORE,
        TaskCategory.CODE_CHANGE: OrchestratorType.CORE,
        TaskCategory.ARCHITECTURE: OrchestratorType.CORE,
        TaskCategory.PRODUCTION: OrchestratorType.CORE,
        TaskCategory.FULL_FEATURE: OrchestratorType.SQUAD,
        TaskCategory.COMPLEX_WORKFLOW: OrchestratorType.STATE,
    }

    def __init__(
        self,
        vertice_client: Optional[Any] = None,
        mcp_client: Optional[Any] = None,
        approval_callback: Optional[Callable] = None,
        notify_callback: Optional[Callable] = None,
    ) -> None:
        """
        Initialize the coordinator.

        Args:
            vertice_client: VerticeClient (multi-provider LLM router) or
                           compatible LLM client. Supports: Groq, Cerebras,
                           Mistral, Vertex AI (Gemini), Azure OpenAI.
            mcp_client: MCP client for tool execution (optional)
            approval_callback: Callback for L2 approvals
            notify_callback: Callback for L1 notifications
        """
        self._vertice_client = vertice_client
        self._mcp_client = mcp_client
        self._approval_callback = approval_callback
        self._notify_callback = notify_callback

        # Lazy-loaded orchestrators
        self._core_orchestrator: Optional[Any] = None
        self._state_orchestrator: Optional[Any] = None
        self._squad_orchestrator: Optional[Any] = None

        # History
        self._decisions: List[CoordinationDecision] = []
        self._execution_count = 0

    # =========================================================================
    # ORCHESTRATOR LOADING (Lazy)
    # =========================================================================

    def _get_core_orchestrator(self) -> Optional[Any]:
        """Get or create OrchestratorAgent."""
        if self._core_orchestrator is not None:
            return self._core_orchestrator

        try:
            from agents.orchestrator import OrchestratorAgent
            self._core_orchestrator = OrchestratorAgent(
                approval_callback=self._approval_callback,
                notify_callback=self._notify_callback,
            )
            logger.debug("Loaded OrchestratorAgent")
            return self._core_orchestrator
        except ImportError as e:
            logger.warning(f"Could not load OrchestratorAgent: {e}")
            return None

    def _get_state_orchestrator(self) -> Optional[Any]:
        """Get or create ActiveOrchestrator."""
        if self._state_orchestrator is not None:
            return self._state_orchestrator

        try:
            from vertice_core.agents.orchestrator import ActiveOrchestrator
            from vertice_core.agents.context import UnifiedContext

            context = UnifiedContext()
            self._state_orchestrator = ActiveOrchestrator(context=context)
            logger.debug("Loaded ActiveOrchestrator")
            return self._state_orchestrator
        except ImportError as e:
            logger.warning(f"Could not load ActiveOrchestrator: {e}")
            return None

    def _get_squad_orchestrator(self) -> Optional[Any]:
        """Get or create DevSquad."""
        if self._squad_orchestrator is not None:
            return self._squad_orchestrator

        if self._vertice_client is None or self._mcp_client is None:
            logger.warning("DevSquad requires vertice_client and mcp_client")
            return None

        try:
            from vertice_cli.orchestration.squad import DevSquad
            self._squad_orchestrator = DevSquad(
                llm_client=self._vertice_client,  # VerticeClient is LLM-compatible
                mcp_client=self._mcp_client,
                require_human_approval=self._approval_callback is not None,
            )
            logger.debug("Loaded DevSquad")
            return self._squad_orchestrator
        except ImportError as e:
            logger.warning(f"Could not load DevSquad: {e}")
            return None

    # =========================================================================
    # TASK CATEGORIZATION
    # =========================================================================

    def categorize_task(self, request: str) -> TaskCategory:
        """
        Categorize task based on request content.

        Args:
            request: User request string

        Returns:
            TaskCategory for the request
        """
        request_lower = request.lower()

        # Check each category's keywords
        scores: Dict[TaskCategory, int] = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in request_lower)
            if score > 0:
                scores[category] = score

        if not scores:
            # Default to simple code change
            return TaskCategory.CODE_CHANGE

        # Return highest scoring category
        return max(scores, key=lambda c: scores[c])

    def select_orchestrator(
        self,
        request: str,
        category: Optional[TaskCategory] = None,
        force: Optional[OrchestratorType] = None,
    ) -> CoordinationDecision:
        """
        Select appropriate orchestrator for request.

        Args:
            request: User request
            category: Pre-computed category (optional)
            force: Force specific orchestrator (optional)

        Returns:
            CoordinationDecision with selected orchestrator
        """
        if force and force != OrchestratorType.AUTO:
            return CoordinationDecision(
                orchestrator=force,
                category=category or TaskCategory.CODE_CHANGE,
                confidence=1.0,
                reasoning="Forced by caller",
            )

        # Categorize if not provided
        if category is None:
            category = self.categorize_task(request)

        # Map to orchestrator
        orchestrator = self.CATEGORY_ORCHESTRATOR.get(
            category,
            OrchestratorType.CORE  # Default
        )

        # Check availability
        if orchestrator == OrchestratorType.SQUAD:
            if self._get_squad_orchestrator() is None:
                orchestrator = OrchestratorType.CORE
                logger.info("DevSquad unavailable, falling back to Core")

        if orchestrator == OrchestratorType.STATE:
            if self._get_state_orchestrator() is None:
                orchestrator = OrchestratorType.CORE
                logger.info("ActiveOrchestrator unavailable, falling back to Core")

        decision = CoordinationDecision(
            orchestrator=orchestrator,
            category=category,
            confidence=0.8,  # Could be improved with ML
            reasoning=f"Category '{category.value}' maps to {orchestrator.name}",
            metadata={"request_length": len(request)},
        )

        self._decisions.append(decision)
        return decision

    # =========================================================================
    # EXECUTION
    # =========================================================================

    async def execute(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
        orchestrator: OrchestratorType = OrchestratorType.AUTO,
    ) -> AsyncIterator[str]:
        """
        Execute request through appropriate orchestrator.

        Args:
            request: User request
            context: Optional context dict
            orchestrator: Force specific orchestrator or AUTO

        Yields:
            Response chunks as strings
        """
        self._execution_count += 1

        # Select orchestrator
        decision = self.select_orchestrator(request, force=orchestrator)

        yield f"[Coordinator] Task: {decision.category.value}\n"
        yield f"[Coordinator] Using: {decision.orchestrator.name}\n\n"

        try:
            if decision.orchestrator == OrchestratorType.CORE:
                async for chunk in self._execute_core(request, context):
                    yield chunk

            elif decision.orchestrator == OrchestratorType.STATE:
                async for chunk in self._execute_state(request, context):
                    yield chunk

            elif decision.orchestrator == OrchestratorType.SQUAD:
                async for chunk in self._execute_squad(request, context):
                    yield chunk

            else:
                yield f"[Coordinator] Unknown orchestrator: {decision.orchestrator}\n"

        except (AttributeError, RuntimeError, asyncio.CancelledError, ValueError, TypeError) as e:
            logger.error(f"Execution error: {e}")
            yield f"\n[Coordinator] Error: {e}\n"

            # Try fallback
            if decision.orchestrator != OrchestratorType.CORE:
                yield "[Coordinator] Falling back to Core orchestrator...\n\n"
                async for chunk in self._execute_core(request, context):
                    yield chunk

    async def _execute_core(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        """Execute via OrchestratorAgent."""
        orch = self._get_core_orchestrator()

        if orch is None:
            yield "[Core] OrchestratorAgent not available\n"
            yield f"[Fallback] Processing: {request[:100]}...\n"
            return

        try:
            async for chunk in orch.execute(request, stream=True):
                yield chunk
        except TypeError:
            # execute() may not support stream
            yield "[Core] Executing task...\n"
            tasks = await orch.plan(request)
            yield f"[Core] Created {len(tasks)} tasks\n"

            for task in tasks:
                can_proceed, approval = await orch.check_autonomy(task)

                if not can_proceed and approval:
                    yield f"[Core] Requires approval (L2): {approval.operation}\n"
                    yield f"[Core] Approval ID: {approval.id}\n"
                    continue

                agent_role = await orch.route(task)
                yield f"[Core] Routed to: {agent_role.value}\n"

                await orch.notify_completion(task, "completed")

            yield "[Core] All tasks processed\n"

    async def _execute_state(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        """Execute via ActiveOrchestrator."""
        orch = self._get_state_orchestrator()

        if orch is None:
            yield "[State] ActiveOrchestrator not available\n"
            # Fallback to core
            async for chunk in self._execute_core(request, context):
                yield chunk
            return

        try:
            async for chunk in orch.execute(request):
                yield chunk
        except (AttributeError, RuntimeError, asyncio.CancelledError, ValueError, TypeError) as e:
            yield f"[State] Error: {e}\n"

    async def _execute_squad(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        """Execute via DevSquad."""
        squad = self._get_squad_orchestrator()

        if squad is None:
            yield "[Squad] DevSquad not available (requires llm_client, mcp_client)\n"
            # Fallback to core
            async for chunk in self._execute_core(request, context):
                yield chunk
            return

        yield "[Squad] Starting 5-phase workflow...\n"

        try:
            result = await squad.execute_workflow(
                request,
                context=context,
                approval_callback=self._approval_callback,
            )

            # Stream phase results
            for phase_result in result.phases:
                status = "✓" if phase_result.success else "✗"
                yield f"[Squad] {status} {phase_result.phase.value}: "
                yield f"{phase_result.duration_seconds:.1f}s\n"

            yield f"\n[Squad] Status: {result.status.value}\n"
            yield f"[Squad] Duration: {result.total_duration_seconds:.1f}s\n"

            if result.metadata.get("error"):
                yield f"[Squad] Error: {result.metadata['error']}\n"

        except (AttributeError, RuntimeError, asyncio.CancelledError, ValueError, TypeError) as e:
            yield f"[Squad] Error: {e}\n"

    # =========================================================================
    # STATUS AND STATS
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """Get coordinator status."""
        return {
            "execution_count": self._execution_count,
            "decisions_made": len(self._decisions),
            "orchestrators": {
                "core": self._core_orchestrator is not None,
                "state": self._state_orchestrator is not None,
                "squad": self._squad_orchestrator is not None,
            },
            "has_callbacks": {
                "approval": self._approval_callback is not None,
                "notify": self._notify_callback is not None,
            },
        }

    def get_decisions(self) -> List[CoordinationDecision]:
        """Get history of coordination decisions."""
        return self._decisions.copy()

    def clear_history(self) -> None:
        """Clear decision history."""
        self._decisions.clear()

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================

    def set_callbacks(
        self,
        approval_callback: Optional[Callable] = None,
        notify_callback: Optional[Callable] = None,
    ) -> None:
        """Set or update callbacks."""
        if approval_callback:
            self._approval_callback = approval_callback
        if notify_callback:
            self._notify_callback = notify_callback

        # Update core orchestrator if loaded
        if self._core_orchestrator:
            self._core_orchestrator._approval_callback = self._approval_callback
            self._core_orchestrator._notify_callback = self._notify_callback

    def set_clients(
        self,
        vertice_client: Optional[Any] = None,
        mcp_client: Optional[Any] = None,
    ) -> None:
        """
        Set or update clients.

        Args:
            vertice_client: VerticeClient or compatible LLM client
            mcp_client: MCP client for tool execution
        """
        if vertice_client:
            self._vertice_client = vertice_client
        if mcp_client:
            self._mcp_client = mcp_client

        # Reset squad to pick up new clients
        self._squad_orchestrator = None


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================


def get_coordinator(**kwargs: Any) -> AgencyCoordinator:
    """
    Get a configured AgencyCoordinator.

    Convenience function for quick access.

    Usage:
        from vertice_agents import get_coordinator

        coordinator = get_coordinator(
            approval_callback=my_approval_handler
        )
    """
    return AgencyCoordinator(**kwargs)
