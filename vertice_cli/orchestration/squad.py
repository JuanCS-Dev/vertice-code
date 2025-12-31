"""
DevSquad: Multi-Agent Orchestration System.

This module coordinates the 5 specialist agents (Architect, Explorer, Planner,
Refactorer, Reviewer) to handle complex software development tasks through
agentic thinking and federation of specialists.

Architecture:
    DevSquad (orchestrator)
        ├── Phase 1: Architecture (Architect)
        ├── Phase 2: Exploration (Explorer)
        ├── Phase 3: Planning (Planner)
        ├── [GOVERNANCE GATE] ← JUSTIÇA + SOFIA (parallel)
        ├── Phase 4: Execution (Refactorer)
        └── Phase 5: Review (Reviewer)

Philosophy (Boris Cherny):
    "The best architecture is the one where each component does ONE thing well."

Sprint 5: Pipeline Blindado
    - Checkpoints at each phase via DevSquadStateMachine
    - Rollback capability on failure
    - Input validation at entry
    - Governance gate (JUSTIÇA + SOFIA) before execution
"""

import logging
import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from ..agents.architect import ArchitectAgent
from ..agents.base import AgentResponse, AgentTask
from ..agents.explorer import ExplorerAgent
from ..agents.planner import PlannerAgent
from ..agents.refactorer import RefactorerAgent
from ..agents.reviewer import ReviewerAgent
from .state_machine import DevSquadStateMachine, Phase, PhaseCheckpoint

logger = logging.getLogger(__name__)


class WorkflowPhase(str, Enum):
    """5-phase workflow stages."""
    ARCHITECTURE = "architecture"
    EXPLORATION = "exploration"
    PLANNING = "planning"
    EXECUTION = "execution"
    REVIEW = "review"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PhaseResult(BaseModel):
    """Result of a single workflow phase.
    
    Attributes:
        phase: Workflow phase identifier
        success: Whether phase succeeded
        agent_response: Underlying agent execution response
        started_at: Phase start timestamp
        completed_at: Phase completion timestamp
        duration_seconds: Execution duration
    """
    phase: WorkflowPhase
    success: bool
    agent_response: AgentResponse
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class WorkflowResult(BaseModel):
    """Complete workflow execution result.
    
    Attributes:
        workflow_id: Unique workflow identifier
        request: Original user request
        status: Overall workflow status
        phases: Results from each phase
        artifacts: Generated artifacts (files, reports, etc.)
        total_duration_seconds: Total execution time
        metadata: Arbitrary metadata
    """
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request: str
    status: WorkflowStatus
    phases: List[PhaseResult] = Field(default_factory=list)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    total_duration_seconds: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DevSquad:
    """Multi-agent orchestration system with Pipeline Blindado.

    Coordinates 5 specialist agents to handle complex development tasks:
        1. Architect: Technical feasibility analysis
        2. Explorer: Intelligent context gathering
        3. Planner: Atomic execution plan generation
        4. Refactorer: Code execution with self-correction
        5. Reviewer: Quality validation and approval

    Pipeline Blindado Features (Sprint 5):
        - Checkpoints at each phase for rollback
        - Input validation at entry
        - Governance gate (JUSTIÇA + SOFIA) before execution
        - Automatic rollback on failure

    Workflow:
        User Request
            → [VALIDATION] (input sanitization)
            → Architect (approve/veto) [checkpoint]
            → Explorer (gather context) [checkpoint]
            → Planner (generate plan) [checkpoint]
            → [HUMAN GATE] (approval required)
            → [GOVERNANCE GATE] (JUSTIÇA + SOFIA parallel)
            → Refactorer (execute plan) [checkpoint + transactional]
            → Reviewer (validate quality) [checkpoint]
            → Done / Rollback on failure
    """

    # Input validation patterns
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf\s+/",           # Destructive commands
        r"sudo\s+rm",              # Sudo destructive
        r">\s*/dev/",              # Write to devices
        r"mkfs\.",                 # Format filesystem
        r"dd\s+if=",               # Direct disk write
        r":(){:|:&};:",            # Fork bomb
    ]

    def __init__(
        self,
        llm_client: Any,
        mcp_client: Any,
        require_human_approval: bool = True,
        governance_pipeline: Optional[Any] = None,
        enable_checkpoints: bool = True,
    ):
        """Initialize DevSquad orchestrator with Pipeline Blindado.

        Args:
            llm_client: LLM provider client (Gemini, Claude, etc.)
            mcp_client: MCP client for tool execution
            require_human_approval: Whether to require human approval before execution
            governance_pipeline: Optional GovernancePipeline for JUSTIÇA/SOFIA gates
            enable_checkpoints: Enable phase checkpoints for rollback (default: True)
        """
        self.llm_client = llm_client
        self.mcp_client = mcp_client
        self.require_human_approval = require_human_approval
        self.governance_pipeline = governance_pipeline
        self.enable_checkpoints = enable_checkpoints

        # Initialize specialist agents
        self.architect = ArchitectAgent(llm_client, mcp_client)
        self.explorer = ExplorerAgent(llm_client, mcp_client)
        self.planner = PlannerAgent(llm_client, mcp_client)
        self.refactorer = RefactorerAgent(llm_client, mcp_client)
        self.reviewer = ReviewerAgent(llm_client, mcp_client)

        # State machine for checkpoints (lazy initialized per workflow)
        self._state_machine: Optional[DevSquadStateMachine] = None

    def _validate_input(self, request: str) -> Tuple[bool, Optional[str]]:
        """
        Validate input request for dangerous patterns.

        Pipeline Blindado - Layer 1: Input Validation

        Args:
            request: User request string

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not request or not request.strip():
            return False, "Empty request not allowed"

        if len(request) > 50000:  # 50KB limit
            return False, "Request too large (max 50KB)"

        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, request, re.IGNORECASE):
                logger.warning(f"Dangerous pattern detected: {pattern}")
                return False, f"Request contains potentially dangerous command pattern"

        return True, None

    def _init_state_machine(self, workflow_id: str) -> DevSquadStateMachine:
        """Initialize state machine for a workflow."""
        sm = DevSquadStateMachine(workflow_id=workflow_id)
        sm.start()
        return sm

    def _save_checkpoint(
        self,
        phase: WorkflowPhase,
        context: Dict[str, Any],
        outputs: Dict[str, Any]
    ) -> None:
        """Save checkpoint for current phase."""
        if not self.enable_checkpoints or self._state_machine is None:
            return

        # Map WorkflowPhase to state_machine Phase
        phase_map = {
            WorkflowPhase.ARCHITECTURE: Phase.ARCHITECT,
            WorkflowPhase.EXPLORATION: Phase.EXPLORER,
            WorkflowPhase.PLANNING: Phase.PLANNER,
            WorkflowPhase.EXECUTION: Phase.EXECUTOR,
            WorkflowPhase.REVIEW: Phase.REVIEWER,
        }

        sm_phase = phase_map.get(phase)
        if sm_phase:
            self._state_machine._create_checkpoint(sm_phase, context, outputs)
            logger.debug(f"Checkpoint saved for phase: {phase.value}")

    async def _run_governance_check(
        self,
        plan: Dict[str, Any],
        session_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Run governance check (JUSTIÇA + SOFIA) before execution.

        Pipeline Blindado - Layer 2: Governance Gate

        Args:
            plan: Execution plan from Planner
            session_id: Current session ID

        Returns:
            Tuple of (approved, rejection_reason)
        """
        if self.governance_pipeline is None:
            logger.debug("No governance pipeline configured, skipping check")
            return True, None

        try:
            # Create task for governance check
            task = AgentTask(
                request=f"Execute plan with {len(plan.get('steps', []))} steps",
                context={"plan": plan},
                session_id=session_id,
            )

            # Run JUSTIÇA + SOFIA in parallel
            approved, reason, traces = await self.governance_pipeline.pre_execution_check(
                task=task,
                agent_id="refactorer",
                risk_level="HIGH"  # Code execution is always HIGH risk
            )

            if not approved:
                logger.warning(f"Governance check failed: {reason}")
            else:
                logger.info("Governance check passed")

            return approved, reason

        except Exception as e:
            logger.error(f"Governance check error: {e}")
            # Fail-safe: block on error
            return False, f"Governance check failed: {str(e)}"

    def get_rollback_checkpoint(self, phase: WorkflowPhase) -> Optional[PhaseCheckpoint]:
        """
        Get checkpoint for a specific phase (for rollback).

        Args:
            phase: Phase to get checkpoint for

        Returns:
            PhaseCheckpoint if available, None otherwise
        """
        if self._state_machine is None:
            return None

        phase_map = {
            WorkflowPhase.ARCHITECTURE: Phase.ARCHITECT,
            WorkflowPhase.EXPLORATION: Phase.EXPLORER,
            WorkflowPhase.PLANNING: Phase.PLANNER,
            WorkflowPhase.EXECUTION: Phase.EXECUTOR,
            WorkflowPhase.REVIEW: Phase.REVIEWER,
        }

        sm_phase = phase_map.get(phase)
        if sm_phase:
            return self._state_machine.get_checkpoint(sm_phase)
        return None

    async def execute_workflow(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
        approval_callback: Optional[Any] = None,
    ) -> WorkflowResult:
        """Execute complete 5-phase workflow with Pipeline Blindado.

        Pipeline Blindado Features:
            - Input validation at entry
            - Checkpoints at each phase
            - Governance gate before execution
            - Automatic failure tracking for rollback

        Args:
            request: User request description
            context: Optional context dictionary
            approval_callback: Optional callback for human approval
                              (must return bool or raise exception to cancel)

        Returns:
            WorkflowResult with phase results and artifacts
        """
        workflow_id = str(uuid.uuid4())
        session_id = f"squad_{workflow_id[:8]}"
        workflow_start = datetime.now()

        result = WorkflowResult(
            workflow_id=workflow_id,
            request=request,
            status=WorkflowStatus.IN_PROGRESS,
        )

        # =====================================================================
        # BLINDAGEM LAYER 1: Input Validation
        # =====================================================================
        is_valid, validation_error = self._validate_input(request)
        if not is_valid:
            result.status = WorkflowStatus.FAILED
            result.metadata["validation_error"] = validation_error
            logger.warning(f"Input validation failed: {validation_error}")
            return self._finalize_workflow(result, workflow_start)

        # =====================================================================
        # BLINDAGEM: Initialize State Machine for Checkpoints
        # =====================================================================
        if self.enable_checkpoints:
            self._state_machine = self._init_state_machine(workflow_id)
            result.metadata["checkpoints_enabled"] = True

        try:
            # Phase 1: Architecture Analysis
            arch_result = await self._phase_architecture(
                request, context or {}, session_id
            )
            result.phases.append(arch_result)

            # Save checkpoint
            self._save_checkpoint(
                WorkflowPhase.ARCHITECTURE,
                context or {},
                arch_result.agent_response.data
            )

            if arch_result.success == False:
                result.status = WorkflowStatus.FAILED
                result.metadata["failed_phase"] = "architecture"
                return self._finalize_workflow(result, workflow_start)

            # Check if architect vetoed
            arch_output = arch_result.agent_response.data
            decision = str(arch_output.get("decision", "")).upper()

            if decision not in ["APPROVED", "APPROVE"]:
                result.status = WorkflowStatus.FAILED
                result.metadata["veto_reason"] = arch_output.get("reasoning", "Unknown")
                result.metadata["failed_phase"] = "architecture"
                return self._finalize_workflow(result, workflow_start)

            # Phase 2: Context Exploration
            explore_result = await self._phase_exploration(
                request, arch_output, session_id
            )
            result.phases.append(explore_result)

            # Save checkpoint
            self._save_checkpoint(
                WorkflowPhase.EXPLORATION,
                {"architecture": arch_output},
                explore_result.agent_response.data
            )

            if explore_result.success == False:
                result.status = WorkflowStatus.FAILED
                result.metadata["failed_phase"] = "exploration"
                return self._finalize_workflow(result, workflow_start)

            # Phase 3: Execution Planning
            plan_result = await self._phase_planning(
                request, explore_result.agent_response.data, session_id
            )
            result.phases.append(plan_result)

            # Save checkpoint
            self._save_checkpoint(
                WorkflowPhase.PLANNING,
                {"exploration": explore_result.agent_response.data},
                plan_result.agent_response.data
            )

            if plan_result.success == False:
                result.status = WorkflowStatus.FAILED
                result.metadata["failed_phase"] = "planning"
                return self._finalize_workflow(result, workflow_start)

            # Human Gate: Approval Required
            if self.require_human_approval:
                result.status = WorkflowStatus.AWAITING_APPROVAL

                if approval_callback:
                    plan_output = plan_result.agent_response.data
                    approved = await self._request_approval(
                        approval_callback, plan_output.get("plan", {})
                    )

                    if not approved:
                        result.status = WorkflowStatus.CANCELLED
                        result.metadata["cancellation_reason"] = "User rejected plan"
                        return self._finalize_workflow(result, workflow_start)
                else:
                    # No callback provided, pause here
                    result.metadata["awaiting_manual_approval"] = True
                    return self._finalize_workflow(result, workflow_start)

            result.status = WorkflowStatus.IN_PROGRESS

            # =================================================================
            # BLINDAGEM LAYER 2: Governance Gate (JUSTIÇA + SOFIA)
            # =================================================================
            plan_output = plan_result.agent_response.data
            plan = plan_output.get("plan", {})

            gov_approved, gov_reason = await self._run_governance_check(plan, session_id)

            if not gov_approved:
                result.status = WorkflowStatus.FAILED
                result.metadata["governance_blocked"] = True
                result.metadata["governance_reason"] = gov_reason
                result.metadata["failed_phase"] = "governance_gate"
                logger.warning(f"Governance gate blocked execution: {gov_reason}")
                return self._finalize_workflow(result, workflow_start)

            result.metadata["governance_passed"] = True

            # Phase 4: Code Execution (with transactional support via RefactorerAgent)
            exec_result = await self._phase_execution(
                plan_result.agent_response.data, session_id
            )
            result.phases.append(exec_result)

            # Save checkpoint
            self._save_checkpoint(
                WorkflowPhase.EXECUTION,
                {"plan": plan},
                exec_result.agent_response.data
            )

            if exec_result.success == False:
                result.status = WorkflowStatus.FAILED
                result.metadata["failed_phase"] = "execution"
                # Note: RefactorerAgent handles its own rollback via TransactionalSession
                return self._finalize_workflow(result, workflow_start)

            # Phase 5: Quality Review
            review_result = await self._phase_review(
                exec_result.agent_response.data, session_id
            )
            result.phases.append(review_result)

            # Save checkpoint
            self._save_checkpoint(
                WorkflowPhase.REVIEW,
                {"execution": exec_result.agent_response.data},
                review_result.agent_response.data
            )

            if review_result.success == False:
                result.status = WorkflowStatus.FAILED
                result.metadata["failed_phase"] = "review"
                return self._finalize_workflow(result, workflow_start)

            # Check if reviewer approved
            review_output = review_result.agent_response.data
            if not review_output.get("report", {}).get("approved", False):
                result.status = WorkflowStatus.FAILED
                result.metadata["review_failed"] = True
                result.metadata["grade"] = review_output.get("report", {}).get("grade", "F")
                result.metadata["failed_phase"] = "review"
            else:
                result.status = WorkflowStatus.COMPLETED
                result.artifacts = self._collect_artifacts(result.phases)

            return self._finalize_workflow(result, workflow_start)

        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.metadata["error"] = str(e)
            result.metadata["failed_phase"] = "unknown"
            logger.exception(f"Workflow failed with exception: {e}")
            return self._finalize_workflow(result, workflow_start)

    async def _phase_architecture(
        self, request: str, context: Dict[str, Any], session_id: str
    ) -> PhaseResult:
        """Phase 1: Architecture analysis with Architect agent."""
        phase_start = datetime.now()

        task = AgentTask(
            request=request,
            context=context,
            session_id=session_id,
        )

        agent_response = await self.architect.execute(task)
        phase_end = datetime.now()

        return PhaseResult(
            phase=WorkflowPhase.ARCHITECTURE,
            success=agent_response.success,
            agent_response=agent_response,
            started_at=phase_start,
            completed_at=phase_end,
            duration_seconds=(phase_end - phase_start).total_seconds(),
        )

    async def _phase_exploration(
        self, request: str, arch_output: Dict[str, Any], session_id: str
    ) -> PhaseResult:
        """Phase 2: Context exploration with Explorer agent."""
        phase_start = datetime.now()

        # Pass architecture plan to explorer
        context = {
            "architecture": arch_output.get("architecture", {}),
            "project_type": arch_output.get("project_type"),
        }

        task = AgentTask(
            request=request,
            context=context,
            session_id=session_id,
        )

        agent_response = await self.explorer.execute(task)
        phase_end = datetime.now()

        return PhaseResult(
            phase=WorkflowPhase.EXPLORATION,
            success=agent_response.success,
            agent_response=agent_response,
            started_at=phase_start,
            completed_at=phase_end,
            duration_seconds=(phase_end - phase_start).total_seconds(),
        )

    async def _phase_planning(
        self, request: str, explore_output: Dict[str, Any], session_id: str
    ) -> PhaseResult:
        """Phase 3: Execution planning with Planner agent."""
        phase_start = datetime.now()

        # Pass explored context to planner
        context = {
            "context_map": explore_output.get("context", {}),
            "relevant_files": explore_output.get("files", []),
        }

        task = AgentTask(
            request=request,
            context=context,
            session_id=session_id,
        )

        agent_response = await self.planner.execute(task)
        phase_end = datetime.now()

        return PhaseResult(
            phase=WorkflowPhase.PLANNING,
            success=agent_response.success,
            agent_response=agent_response,
            started_at=phase_start,
            completed_at=phase_end,
            duration_seconds=(phase_end - phase_start).total_seconds(),
        )

    async def _phase_execution(
        self, plan_output: Dict[str, Any], session_id: str
    ) -> PhaseResult:
        """Phase 4: Code execution with Refactorer agent."""
        phase_start = datetime.now()

        # Extract execution plan
        plan = plan_output.get("plan", {})

        task = AgentTask(
            request="Execute the planned changes",
            context={"plan": plan},
            session_id=session_id,
        )

        agent_response = await self.refactorer.execute(task)
        phase_end = datetime.now()

        return PhaseResult(
            phase=WorkflowPhase.EXECUTION,
            success=agent_response.success,
            agent_response=agent_response,
            started_at=phase_start,
            completed_at=phase_end,
            duration_seconds=(phase_end - phase_start).total_seconds(),
        )

    async def _phase_review(
        self, exec_output: Dict[str, Any], session_id: str
    ) -> PhaseResult:
        """Phase 5: Quality review with Reviewer agent."""
        phase_start = datetime.now()

        # Extract changed files from execution
        changed_files = exec_output.get("modified_files", [])

        task = AgentTask(
            request="Review code changes for quality",
            context={"files": changed_files},
            session_id=session_id,
        )

        agent_response = await self.reviewer.execute(task)
        phase_end = datetime.now()

        return PhaseResult(
            phase=WorkflowPhase.REVIEW,
            success=agent_response.success,
            agent_response=agent_response,
            started_at=phase_start,
            completed_at=phase_end,
            duration_seconds=(phase_end - phase_start).total_seconds(),
        )

    async def _request_approval(
        self, callback: Any, plan: Dict[str, Any]
    ) -> bool:
        """Request human approval for execution plan.
        
        Args:
            callback: Approval callback function or coroutine
            plan: Execution plan dictionary
        
        Returns:
            True if approved, False if rejected
        """
        try:
            if callable(callback):
                result = callback(plan)
                if hasattr(result, '__await__'):
                    result = await result
                return bool(result)
            return False
        except Exception:
            return False  # Reject on error

    def _collect_artifacts(self, phases: List[PhaseResult]) -> Dict[str, Any]:
        """Collect artifacts from all phases.
        
        Args:
            phases: List of phase results
        
        Returns:
            Dictionary of artifacts by phase
        """
        artifacts = {}

        for phase_result in phases:
            phase_name = phase_result.phase.value
            artifacts[phase_name] = phase_result.agent_response.data

        return artifacts

    def _finalize_workflow(
        self, result: WorkflowResult, start_time: datetime
    ) -> WorkflowResult:
        """Finalize workflow result with timing.
        
        Args:
            result: Workflow result to finalize
            start_time: Workflow start timestamp
        
        Returns:
            Finalized workflow result
        """
        end_time = datetime.now()
        result.total_duration_seconds = (end_time - start_time).total_seconds()
        return result

    def get_phase_summary(self, workflow_result: WorkflowResult) -> str:
        """Generate human-readable phase summary.
        
        Args:
            workflow_result: Completed workflow result
        
        Returns:
            Formatted summary string
        """
        lines = [
            f"Workflow {workflow_result.workflow_id[:8]}",
            f"Status: {workflow_result.status.value}",
            f"Duration: {workflow_result.total_duration_seconds:.1f}s",
            "",
            "Phases:",
        ]

        for phase_result in workflow_result.phases:
            status_icon = "✅" if phase_result.success == True else "❌"
            lines.append(
                f"  {status_icon} {phase_result.phase.value.capitalize()}: "
                f"{phase_result.duration_seconds:.1f}s"
            )

        if workflow_result.status == WorkflowStatus.COMPLETED:
            lines.append("")
            lines.append("Artifacts: " + ", ".join(workflow_result.artifacts.keys()))

        return "\n".join(lines)
