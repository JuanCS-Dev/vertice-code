"""
Bounded Autonomy System

Implements the Three Loops pattern for human-AI collaboration.

Autonomy Levels:
- L0: Autonomous - execute without human approval
- L1: Notify - execute and notify human afterward
- L2: Approve - propose and wait for human approval
- L3: Human Only - human executes, agent advises

Reference:
- https://www.infoq.com/articles/architects-ai-era/
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional, Any, Tuple
import logging

from .types import (
    ApprovalRequest,
    AutonomyLevel,
    Task,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BoundedAutonomyMixin:
    """
    Mixin providing Bounded Autonomy capabilities.

    Add to OrchestratorAgent via multiple inheritance.
    """

    pending_approvals: Dict[str, ApprovalRequest]
    _approval_callback: Optional[Any]
    _notify_callback: Optional[Any]

    # Bounded Autonomy Rules - Maps operations to autonomy levels
    AUTONOMY_RULES: Dict[str, AutonomyLevel] = {
        # L0 - Full autonomy (safe, reversible operations)
        "format_code": AutonomyLevel.L0_AUTONOMOUS,
        "lint_check": AutonomyLevel.L0_AUTONOMOUS,
        "run_tests": AutonomyLevel.L0_AUTONOMOUS,
        "generate_docs": AutonomyLevel.L0_AUTONOMOUS,
        "search_codebase": AutonomyLevel.L0_AUTONOMOUS,
        "read_file": AutonomyLevel.L0_AUTONOMOUS,
        # L1 - Execute + notify (low-risk modifications)
        "write_file": AutonomyLevel.L1_NOTIFY,
        "create_file": AutonomyLevel.L1_NOTIFY,
        "refactor_code": AutonomyLevel.L1_NOTIFY,
        "add_dependency": AutonomyLevel.L1_NOTIFY,
        "git_commit": AutonomyLevel.L1_NOTIFY,
        # L2 - Requires approval (significant changes)
        "delete_file": AutonomyLevel.L2_APPROVE,
        "architecture_change": AutonomyLevel.L2_APPROVE,
        "api_change": AutonomyLevel.L2_APPROVE,
        "security_config": AutonomyLevel.L2_APPROVE,
        "git_push": AutonomyLevel.L2_APPROVE,
        "database_migration": AutonomyLevel.L2_APPROVE,
        # L3 - Human only (critical operations)
        "deploy_production": AutonomyLevel.L3_HUMAN_ONLY,
        "delete_database": AutonomyLevel.L3_HUMAN_ONLY,
        "financial_transaction": AutonomyLevel.L3_HUMAN_ONLY,
        "external_api_key": AutonomyLevel.L3_HUMAN_ONLY,
        "user_data_access": AutonomyLevel.L3_HUMAN_ONLY,
    }

    def get_autonomy_level(self, operation: str) -> AutonomyLevel:
        """
        Get the autonomy level for an operation.

        Args:
            operation: The operation to check (e.g., "write_file").

        Returns:
            AutonomyLevel for the operation (defaults to L1).
        """
        return self.AUTONOMY_RULES.get(operation, AutonomyLevel.L1_NOTIFY)

    def classify_operation(self, task_description: str) -> str:
        """
        Classify a task description into an operation type.

        Args:
            task_description: Description of the task.

        Returns:
            Operation type string for autonomy lookup.
        """
        desc_lower = task_description.lower()

        # L3 operations (most restrictive first)
        if any(k in desc_lower for k in ["deploy prod", "deploy to prod", "production"]):
            return "deploy_production"
        if "api key" in desc_lower or "secret" in desc_lower:
            return "external_api_key"

        # L2 operations
        if "delete" in desc_lower and "file" in desc_lower:
            return "delete_file"
        if any(k in desc_lower for k in ["architecture", "design system"]):
            return "architecture_change"
        if "push" in desc_lower and "git" in desc_lower:
            return "git_push"
        if "migration" in desc_lower:
            return "database_migration"

        # L1 operations
        if any(k in desc_lower for k in ["write", "create", "add"]):
            return "write_file"
        if "refactor" in desc_lower:
            return "refactor_code"
        if "commit" in desc_lower:
            return "git_commit"

        # L0 operations
        if any(k in desc_lower for k in ["format", "lint", "test", "search", "read"]):
            return "format_code"

        return "write_file"  # Default to L1

    async def check_autonomy(
        self,
        task: Task,
        operation: Optional[str] = None,
    ) -> Tuple[bool, Optional[ApprovalRequest]]:
        """
        Check if task can proceed based on autonomy level.

        Args:
            task: The task to check.
            operation: Optional explicit operation type.

        Returns:
            Tuple of (can_proceed, approval_request_if_needed).
        """
        op = operation or self.classify_operation(task.description)
        level = self.get_autonomy_level(op)
        task.autonomy_level = level

        if level == AutonomyLevel.L0_AUTONOMOUS:
            return True, None

        elif level == AutonomyLevel.L1_NOTIFY:
            return True, None

        elif level == AutonomyLevel.L2_APPROVE:
            approval = ApprovalRequest(
                id=str(uuid.uuid4()),
                task_id=task.id,
                operation=op,
                description=task.description,
                autonomy_level=level,
                proposed_action=f"Execute: {task.description}",
                risk_assessment=self._assess_risk(task, op),
            )
            task.approval_request = approval
            self.pending_approvals[approval.id] = approval

            if self._approval_callback:
                approved = self._approval_callback(approval)
                if approved:
                    approval.approved = True
                    approval.approved_at = datetime.now().isoformat()
                    return True, approval
                else:
                    approval.approved = False
                    return False, approval

            return False, approval

        else:  # L3_HUMAN_ONLY
            approval = ApprovalRequest(
                id=str(uuid.uuid4()),
                task_id=task.id,
                operation=op,
                description=task.description,
                autonomy_level=level,
                proposed_action=f"HUMAN MUST EXECUTE: {task.description}",
                risk_assessment="CRITICAL: This operation requires human execution.",
            )
            task.approval_request = approval
            self.pending_approvals[approval.id] = approval
            return False, approval

    def _assess_risk(self, task: Task, operation: str) -> str:
        """Generate risk assessment for approval request."""
        risk_levels = {
            "delete_file": "MEDIUM: File deletion is irreversible without backup.",
            "architecture_change": "HIGH: Affects system structure and dependencies.",
            "api_change": "HIGH: May break existing integrations.",
            "security_config": "HIGH: Security misconfiguration risk.",
            "git_push": "MEDIUM: Changes will be visible to team.",
            "database_migration": "HIGH: Data integrity risk.",
            "deploy_production": "CRITICAL: Affects live users.",
            "delete_database": "CRITICAL: Irreversible data loss.",
        }
        return risk_levels.get(operation, "MEDIUM: Review before proceeding.")

    async def notify_completion(
        self,
        task: Task,
        result: str,
    ) -> None:
        """Notify human of task completion (for L1 operations)."""
        if task.autonomy_level == AutonomyLevel.L1_NOTIFY:
            if self._notify_callback:
                self._notify_callback(
                    "task_completed",
                    {
                        "task_id": task.id,
                        "description": task.description,
                        "result": result,
                        "autonomy_level": task.autonomy_level.value,
                    },
                )

            logger.info(f"[L1 Notify] Task {task.id} completed: {result[:100]}...")

    def approve(self, approval_id: str, approved_by: str = "human") -> bool:
        """Approve a pending approval request."""
        if approval_id not in self.pending_approvals:
            return False

        approval = self.pending_approvals[approval_id]
        approval.approved = True
        approval.approved_by = approved_by
        approval.approved_at = datetime.now().isoformat()

        logger.info(f"Approved: {approval.operation} by {approved_by}")
        return True

    def reject(self, approval_id: str, rejected_by: str = "human") -> bool:
        """Reject a pending approval request."""
        if approval_id not in self.pending_approvals:
            return False

        approval = self.pending_approvals[approval_id]
        approval.approved = False
        approval.approved_by = rejected_by
        approval.approved_at = datetime.now().isoformat()

        logger.info(f"Rejected: {approval.operation} by {rejected_by}")
        return True

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approval requests."""
        return [a.to_dict() for a in self.pending_approvals.values() if a.approved is None]
