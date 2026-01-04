"""
DevSquad - Multi-Agent Orchestration System.

Coordinates 5 specialist agents for complex software development tasks.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ...agents.architect import ArchitectAgent
from ...agents.base import AgentTask, AgentResponse
from ...agents.explorer import ExplorerAgent
from ...agents.planner import PlannerAgent
from ...agents.refactorer import RefactorerAgent
from ...agents.reviewer import ReviewerAgent
from ..state_machine import DevSquadStateMachine, Phase, PhaseCheckpoint
from .phases import (
    phase_architecture,
    phase_exploration,
    phase_planning,
    phase_execution,
    phase_review,
)
from .types import (
    PhaseResult,
    WorkflowPhase,
    WorkflowResult,
    WorkflowStatus,
)
from .validation import validate_input

logger = logging.getLogger(__name__)


class DevSquad:
    """Multi-agent orchestration system with Pipeline Blindado.

    Coordinates 5 specialist agents to handle complex development tasks:
        1. Architect: Technical feasibility analysis
        2. Explorer: Intelligent context gathering
        3. Planner: Atomic execution plan generation
        4. Refactorer: Code execution with self-correction
        5. Reviewer: Quality validation and approval
    """

    def __init__(
        self,
        llm_client: Any,
        mcp_client: Any,
        require_human_approval: bool = True,
        governance_pipeline: Optional[Any] = None,
        enable_checkpoints: bool = True,
    ):
        """Initialize DevSquad orchestrator."""
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

        self._state_machine: Optional[DevSquadStateMachine] = None

    def _init_state_machine(self, workflow_id: str) -> DevSquadStateMachine:
        """Initialize state machine for a workflow."""
        sm = DevSquadStateMachine(workflow_id=workflow_id)
        sm.start()
        return sm

    def _save_checkpoint(
        self, phase: WorkflowPhase, context: Dict[str, Any], outputs: Dict[str, Any]
    ) -> None:
        """Save checkpoint for current phase."""
        if not self.enable_checkpoints or self._state_machine is None:
            return

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
        self, plan: Dict[str, Any], session_id: str
    ) -> Tuple[bool, Optional[str]]:
        """Run governance check (JUSTIÇA + SOFIA) before execution."""
        if self.governance_pipeline is None:
            logger.debug("No governance pipeline configured, skipping check")
            return True, None

        try:
            task = AgentTask(
                request=f"Execute plan with {len(plan.get('steps', []))} steps",
                context={"plan": plan},
                session_id=session_id,
            )

            approved, reason, traces = await self.governance_pipeline.pre_execution_check(
                task=task, agent_id="refactorer", risk_level="HIGH"
            )

            if not approved:
                logger.warning(f"Governance check failed: {reason}")
            else:
                logger.info("Governance check passed")

            return approved, reason

        except Exception as e:
            logger.error(f"Governance check error: {e}")
            return False, f"Governance check failed: {str(e)}"

    def get_rollback_checkpoint(self, phase: WorkflowPhase) -> Optional[PhaseCheckpoint]:
        """Get checkpoint for a specific phase (for rollback)."""
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
        """Execute complete 5-phase workflow with Pipeline Blindado."""
        workflow_id = str(uuid.uuid4())
        session_id = f"squad_{workflow_id[:8]}"
        workflow_start = datetime.now()

        result = WorkflowResult(
            workflow_id=workflow_id,
            request=request,
            status=WorkflowStatus.IN_PROGRESS,
        )

        # BLINDAGEM LAYER 1: Input Validation
        is_valid, validation_error = validate_input(request)
        if not is_valid:
            result.status = WorkflowStatus.FAILED
            result.metadata["validation_error"] = validation_error
            logger.warning(f"Input validation failed: {validation_error}")
            return self._finalize_workflow(result, workflow_start)

        # Initialize State Machine
        if self.enable_checkpoints:
            self._state_machine = self._init_state_machine(workflow_id)
            result.metadata["checkpoints_enabled"] = True

        try:
            # Phase 1: Architecture
            arch_result = await phase_architecture(
                self.architect, request, context or {}, session_id
            )
            result.phases.append(arch_result)
            self._save_checkpoint(
                WorkflowPhase.ARCHITECTURE, context or {}, arch_result.agent_response.data
            )

            if not arch_result.success:
                result.status = WorkflowStatus.FAILED
                result.metadata["failed_phase"] = "architecture"
                return self._finalize_workflow(result, workflow_start)

            arch_output = arch_result.agent_response.data
            decision = str(arch_output.get("decision", "")).upper()
            if decision not in ["APPROVED", "APPROVE"]:
                result.status = WorkflowStatus.FAILED
                result.metadata["veto_reason"] = arch_output.get("reasoning", "Unknown")
                result.metadata["failed_phase"] = "architecture"
                return self._finalize_workflow(result, workflow_start)

            # Phase 2: Exploration
            explore_result = await phase_exploration(
                self.explorer, request, arch_output, session_id
            )
            result.phases.append(explore_result)
            self._save_checkpoint(
                WorkflowPhase.EXPLORATION,
                {"architecture": arch_output},
                explore_result.agent_response.data,
            )

            if not explore_result.success:
                result.status = WorkflowStatus.FAILED
                result.metadata["failed_phase"] = "exploration"
                return self._finalize_workflow(result, workflow_start)

            # Phase 3: Planning
            plan_result = await phase_planning(
                self.planner, request, explore_result.agent_response.data, session_id
            )
            result.phases.append(plan_result)
            self._save_checkpoint(
                WorkflowPhase.PLANNING,
                {"exploration": explore_result.agent_response.data},
                plan_result.agent_response.data,
            )

            if not plan_result.success:
                result.status = WorkflowStatus.FAILED
                result.metadata["failed_phase"] = "planning"
                return self._finalize_workflow(result, workflow_start)

            # Human Gate
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
                    result.metadata["awaiting_manual_approval"] = True
                    return self._finalize_workflow(result, workflow_start)

            result.status = WorkflowStatus.IN_PROGRESS

            # BLINDAGEM LAYER 2: Governance Gate
            plan_output = plan_result.agent_response.data
            plan = plan_output.get("plan", {})
            gov_approved, gov_reason = await self._run_governance_check(plan, session_id)

            if not gov_approved:
                result.status = WorkflowStatus.FAILED
                result.metadata["governance_blocked"] = True
                result.metadata["governance_reason"] = gov_reason
                result.metadata["failed_phase"] = "governance_gate"
                return self._finalize_workflow(result, workflow_start)

            result.metadata["governance_passed"] = True

            # Phase 4: Execution
            exec_result = await phase_execution(
                self.refactorer, plan_result.agent_response.data, session_id
            )
            result.phases.append(exec_result)
            self._save_checkpoint(
                WorkflowPhase.EXECUTION, {"plan": plan}, exec_result.agent_response.data
            )

            if not exec_result.success:
                result.status = WorkflowStatus.FAILED
                result.metadata["failed_phase"] = "execution"
                return self._finalize_workflow(result, workflow_start)

            # Phase 5: Review
            review_result = await phase_review(
                self.reviewer, exec_result.agent_response.data, session_id
            )
            result.phases.append(review_result)
            self._save_checkpoint(
                WorkflowPhase.REVIEW,
                {"execution": exec_result.agent_response.data},
                review_result.agent_response.data,
            )

            if not review_result.success:
                result.status = WorkflowStatus.FAILED
                result.metadata["failed_phase"] = "review"
                return self._finalize_workflow(result, workflow_start)

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

    async def _request_approval(self, callback: Any, plan: Dict[str, Any]) -> bool:
        """Request human approval for execution plan."""
        try:
            if callable(callback):
                result = callback(plan)
                if hasattr(result, "__await__"):
                    result = await result
                return bool(result)
            return False
        except (TypeError, ValueError, RuntimeError):
            return False

    def _collect_artifacts(self, phases: List[PhaseResult]) -> Dict[str, Any]:
        """Collect artifacts from all phases."""
        artifacts = {}
        for phase_result in phases:
            phase_name = phase_result.phase.value
            artifacts[phase_name] = phase_result.agent_response.data
        return artifacts

    def _finalize_workflow(self, result: WorkflowResult, start_time: datetime) -> WorkflowResult:
        """Finalize workflow result with timing."""
        end_time = datetime.now()
        result.total_duration_seconds = (end_time - start_time).total_seconds()
        return result

    def get_phase_summary(self, workflow_result: WorkflowResult) -> str:
        """Generate human-readable phase summary."""
        lines = [
            f"Workflow {workflow_result.workflow_id[:8]}",
            f"Status: {workflow_result.status.value}",
            f"Duration: {workflow_result.total_duration_seconds:.1f}s",
            "",
            "Phases:",
        ]

        for phase_result in workflow_result.phases:
            status_icon = "+" if phase_result.success else "x"
            lines.append(
                f"  [{status_icon}] {phase_result.phase.value.capitalize()}: "
                f"{phase_result.duration_seconds:.1f}s"
            )

        if workflow_result.status == WorkflowStatus.COMPLETED:
            lines.append("")
            lines.append("Artifacts: " + ", ".join(workflow_result.artifacts.keys()))

        return "\n".join(lines)


__all__ = ["DevSquad"]
