"""
Governance Pipeline
===================

Orchestrator-Worker pattern for multi-agent governance with parallel execution.

Architecture: User Request -> Maestro -> [Justiça + Sofia] PARALLEL -> Worker
"""

import asyncio
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from vertice_cli.agents.base import AgentTask, AgentResponse, BaseAgent
from vertice_cli.agents.justica_agent import JusticaIntegratedAgent
from vertice_cli.agents.sofia_agent import SofiaIntegratedAgent
from vertice_cli.core.observability import get_tracer, trace_operation
from vertice_cli.core.agent_identity import enforce_permission, AgentPermission

logger = logging.getLogger(__name__)
tracer = get_tracer()


def _detect_circular_references(obj: Any, visited: Optional[set] = None, max_depth: int = 100) -> bool:
    """Detect circular references to prevent infinite loops."""
    if visited is None:
        visited = set()

    if max_depth <= 0:
        logger.warning("Max depth reached in circular reference detection")
        return True

    # Get object ID
    obj_id = id(obj)

    # Check if we've seen this object before
    if obj_id in visited:
        return True

    # Mark as visited
    visited.add(obj_id)

    # Check nested structures
    if isinstance(obj, dict):
        for key, value in obj.items():
            if _detect_circular_references(value, visited.copy(), max_depth - 1):
                return True
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            if _detect_circular_references(item, visited.copy(), max_depth - 1):
                return True

    return False


class GovernancePipeline:
    """Governance pipeline using Orchestrator-Worker pattern.

    Runs Justiça (governance) and Sofia (counsel) checks in parallel.
    Features: Context isolation, parallel execution, fail-safe mode.
    """

    def __init__(
        self,
        justica: JusticaIntegratedAgent,
        sofia: SofiaIntegratedAgent,
        enable_governance: bool = True,
        enable_counsel: bool = True,
        enable_observability: bool = True,
        fail_safe: bool = True
    ):
        """Initialize governance pipeline with Justiça and Sofia agents."""
        if justica is None:
            raise ValueError("justica cannot be None")
        if sofia is None:
            raise ValueError("sofia cannot be None")

        # Type validation (duck typing - check for required methods)
        if not hasattr(justica, 'evaluate_action') and not hasattr(justica, 'execute'):
            raise TypeError(
                f"justica must have 'evaluate_action' or 'execute' method, "
                f"got {type(justica).__name__}"
            )

        if not hasattr(sofia, 'provide_counsel') and not hasattr(sofia, 'execute'):
            raise TypeError(
                f"sofia must have 'provide_counsel' or 'execute' method, "
                f"got {type(sofia).__name__}"
            )

        if not isinstance(enable_governance, bool):
            raise TypeError(f"enable_governance must be bool, got {type(enable_governance).__name__}")
        if not isinstance(enable_counsel, bool):
            raise TypeError(f"enable_counsel must be bool, got {type(enable_counsel).__name__}")
        if not isinstance(enable_observability, bool):
            raise TypeError(f"enable_observability must be bool, got {type(enable_observability).__name__}")
        if not isinstance(fail_safe, bool):
            raise TypeError(f"fail_safe must be bool, got {type(fail_safe).__name__}")

        self.justica = justica
        self.sofia = sofia
        self.enable_governance = enable_governance
        self.enable_counsel = enable_counsel
        self.enable_observability = enable_observability
        self.fail_safe = fail_safe

        logger.info("✓ Governance Pipeline initialized")
        logger.info(f"  - Governance (Justiça): {enable_governance}")
        logger.info(f"  - Counsel (Sofia): {enable_counsel}")
        logger.info(f"  - Observability: {enable_observability}")
        logger.info(f"  - Fail-safe mode: {fail_safe}")

    async def pre_execution_check(
        self,
        task: AgentTask,
        agent_id: str,
        risk_level: str = "MEDIUM"
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Execute governance checks BEFORE agent action (parallel).

        Args:
            task: Task to be executed
            agent_id: Agent requesting execution
            risk_level: LOW, MEDIUM, HIGH, or CRITICAL

        Returns:
            Tuple of (approved, reason, traces)
        """
        if task is None:
            raise ValueError("task cannot be None")
        if not isinstance(task, AgentTask):
            raise TypeError(f"task must be AgentTask, got {type(task).__name__}")

        if agent_id is None:
            raise ValueError("agent_id cannot be None")
        if not isinstance(agent_id, str):
            raise TypeError(f"agent_id must be str, got {type(agent_id).__name__}")
        if not agent_id.strip():
            raise ValueError("agent_id cannot be empty")

        if risk_level is None:
            raise ValueError("risk_level cannot be None")
        if not isinstance(risk_level, str):
            raise TypeError(f"risk_level must be str, got {type(risk_level).__name__}")

        valid_risk_levels = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        if risk_level not in valid_risk_levels:
            raise ValueError(f"risk_level must be one of {valid_risk_levels}, got '{risk_level}'")

        if _detect_circular_references(task.context):
            raise ValueError("Circular reference detected in task.context - potential infinite loop")

        correlation_id = str(uuid.uuid4())

        with trace_operation(
            "governance_pipeline.pre_execution_check",
            {
                "correlation_id": correlation_id,
                "agent_id": agent_id,
                "risk_level": risk_level
            }
        ) as span:

            traces = {
                "correlation_id": correlation_id,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "agent_id": agent_id,
                "risk_level": risk_level,
                "governance_check": None,
                "counsel_check": None,
                "parallel_execution": True
            }

            try:
                # PARALLEL EXECUTION (Anthropic pattern)
                # Both checks run simultaneously with isolated contexts
                tasks_to_run = []

                if self.enable_governance:
                    tasks_to_run.append(self._run_governance_check(task, agent_id, correlation_id))

                if self.enable_counsel:
                    tasks_to_run.append(self._run_counsel_check(task, agent_id, risk_level, correlation_id))

                # Execute in parallel
                if tasks_to_run:
                    results = await asyncio.gather(*tasks_to_run, return_exceptions=True)

                    # Process governance result
                    if self.enable_governance:
                        gov_result = results[0]
                        if isinstance(gov_result, Exception):
                            if self.fail_safe:
                                traces["governance_check"] = {"error": str(gov_result), "blocked": True}
                                return False, f"Governance check failed: {str(gov_result)}", traces
                        else:
                            traces["governance_check"] = gov_result
                            if not gov_result["approved"]:
                                return False, gov_result["reason"], traces

                    # Process counsel result
                    if self.enable_counsel and len(results) > 1:
                        counsel_result = results[1] if len(results) > 1 else results[0]
                        if isinstance(counsel_result, Exception):
                            logger.warning(f"Counsel check failed: {counsel_result}")
                            # Counsel failures don't block (advisory only)
                        else:
                            traces["counsel_check"] = counsel_result

                traces["completed_at"] = datetime.now(timezone.utc).isoformat()
                traces["approved"] = True

                return True, None, traces

            except Exception as e:
                logger.exception(f"[{correlation_id}] Pipeline error: {e}")
                span.record_exception(e)

                # FAIL-SAFE: Block on unexpected error
                if self.fail_safe:
                    return False, f"Pipeline error (fail-safe): {str(e)}", traces

                # If not fail-safe, allow but log
                logger.error("Pipeline error but fail-safe disabled - allowing execution")
                return True, None, traces

    async def _run_governance_check(
        self,
        task: AgentTask,
        agent_id: str,
        correlation_id: str
    ) -> Dict[str, Any]:
        """
        Run Justiça governance check (isolated context).

        This runs in PARALLEL with counsel check.
        """
        with trace_operation(
            "governance.justica_check",
            {"agent": "justica", "correlation_id": correlation_id}
        ) as span:

            # Enforce permission (IAM pattern)
            try:
                enforce_permission("governance", AgentPermission.EVALUATE_GOVERNANCE)
            except PermissionError as e:
                logger.error(f"Permission denied: {e}")
                return {
                    "agent": "justica",
                    "approved": False,
                    "reason": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

            # Evaluate action
            verdict = await self.justica.evaluate_action(
                agent_id=agent_id,
                action_type="agent_task",  # Fixed: was action_description (AIR GAP!)
                content=task.request,
                context={
                    **task.context,
                    "correlation_id": correlation_id
                }
            )

            result = {
                "agent": "justica",
                "approved": verdict.approved,  # Fixed: was verdict.success (AIR GAP!)
                "reason": verdict.reasoning if not verdict.approved else None,
                "trust_score": getattr(verdict, "trust_score", 0.0),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            if not verdict.approved:
                span.set_attribute("blocked", True)

            return result

    async def _run_counsel_check(
        self,
        task: AgentTask,
        agent_id: str,
        risk_level: str,
        correlation_id: str
    ) -> Dict[str, Any]:
        """
        Run Sofia counsel check (isolated context).

        This runs in PARALLEL with governance check.
        Only triggers for HIGH/CRITICAL risk or detected dilemmas.
        """
        with trace_operation(
            "governance.sofia_check",
            {"agent": "sofia", "correlation_id": correlation_id}
        ) as span:

            # Enforce permission (IAM pattern)
            try:
                enforce_permission("counselor", AgentPermission.PROVIDE_COUNSEL)
            except PermissionError as e:
                logger.error(f"Permission denied: {e}")
                return {
                    "agent": "sofia",
                    "triggered": False,
                    "reason": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

            # Check if counsel should trigger
            should_counsel, reason = self.sofia.should_trigger_counsel(task.request)

            result = {
                "agent": "sofia",
                "triggered": False,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Only provide counsel for HIGH/CRITICAL risk OR detected dilemmas
            if should_counsel and risk_level in ["HIGH", "CRITICAL"]:
                counsel = await self.sofia.pre_execution_counsel(
                    action_description=task.request,
                    risk_level=risk_level,
                    agent_id=agent_id,
                    context={
                        **task.context,
                        "correlation_id": correlation_id
                    }
                )

                result["triggered"] = True
                result["counsel_type"] = counsel.counsel_type
                result["confidence"] = counsel.confidence
                result["requires_professional"] = counsel.requires_professional
                result["counsel_preview"] = counsel.counsel[:200]  # First 200 chars

                span.set_attribute("triggered", True)
                span.set_attribute("requires_professional", counsel.requires_professional)

                # ESCALATE if professional help required
                if counsel.requires_professional:
                    logger.warning(f"[{correlation_id}] Professional referral required")
                    await self._escalate_to_professional(
                        correlation_id=correlation_id,
                        agent_id=agent_id,
                        counsel=counsel,
                        task_context=task.context
                    )

            return result

    async def _escalate_to_professional(
        self,
        correlation_id: str,
        agent_id: str,
        counsel: Any,
        task_context: Dict[str, Any]
    ) -> None:
        """Escalate to professional human review (non-blocking)."""
        escalation_record = {
            "correlation_id": correlation_id,
            "agent_id": agent_id,
            "escalation_type": "professional_referral",
            "counsel_type": getattr(counsel, "counsel_type", "unknown"),
            "confidence": getattr(counsel, "confidence", 0.0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context_summary": str(task_context)[:500]  # Truncate for logging
        }

        logger.warning(
            f"[{correlation_id}] ESCALATION: Professional referral triggered. "
            f"Agent: {agent_id}, Type: {escalation_record['counsel_type']}"
        )

        # Record escalation for audit trail
        with trace_operation(
            "governance.escalation",
            {"correlation_id": correlation_id, "type": "professional_referral"}
        ) as span:
            span.set_attribute("escalation.agent_id", agent_id)
            span.set_attribute("escalation.requires_professional", True)

    async def execute_with_governance(
        self,
        agent: BaseAgent,
        task: AgentTask,
        risk_level: str = "MEDIUM"
    ) -> AgentResponse:
        """Execute agent with governance pipeline.

        Args:
            agent: Agent to execute
            task: Task to execute
            risk_level: Risk level (default: MEDIUM)

        Returns:
            AgentResponse with governance metadata
        """
        correlation_id = str(uuid.uuid4())

        with trace_operation(
            "execute_with_governance",
            {
                "correlation_id": correlation_id,
                "agent_id": agent.role.value,
                "risk_level": risk_level
            }
        ) as span:

            # PHASE 1: Pre-execution checks (PARALLEL)
            approved, reason, traces = await self.pre_execution_check(
                task=task,
                agent_id=agent.role.value,
                risk_level=risk_level
            )

            if not approved:
                logger.warning(f"[{correlation_id}] Action blocked: {reason}")
                span.set_attribute("blocked", True)

                return AgentResponse(
                    success=False,
                    reasoning="Governance pipeline blocked action",
                    error=reason,
                    data={
                        "governance_traces": traces,
                        "blocked_by": "governance_pipeline",
                        "correlation_id": correlation_id
                    }
                )

            # PHASE 2: Execute agent (context isolated)
            try:
                with trace_operation(f"agent.{agent.role.value}.execute"):
                    response = await agent.execute(task)

                # Add governance metadata to response
                if response.data is None:
                    response.data = {}
                response.data["governance_traces"] = traces
                response.data["correlation_id"] = correlation_id

                # PHASE 3: Post-execution metrics (background task, non-blocking)
                asyncio.create_task(
                    self._update_metrics_async(
                        agent_id=agent.role.value,
                        success=response.success,
                        correlation_id=correlation_id
                    )
                )

                return response

            except Exception as e:
                logger.exception(f"[{correlation_id}] Agent execution failed: {e}")
                span.record_exception(e)

                return AgentResponse(
                    success=False,
                    reasoning=f"Agent execution failed: {str(e)}",
                    error=str(e),
                    data={
                        "correlation_id": correlation_id,
                        "governance_traces": traces
                    }
                )

    async def _update_metrics_async(
        self,
        agent_id: str,
        success: bool,
        correlation_id: str
    ) -> None:
        """Update Justiça trust metrics in background (non-blocking)."""
        try:
            with trace_operation(
                "governance.metrics_update",
                {"correlation_id": correlation_id, "agent_id": agent_id}
            ) as span:
                span.set_attribute("metrics.success", success)

                if success:
                    logger.debug(f"[{correlation_id}] Recording success for {agent_id}")
                    # Record successful execution in Justiça metrics
                    if hasattr(self.justica, 'record_execution_success'):
                        await self.justica.record_execution_success(agent_id, correlation_id)
                else:
                    logger.debug(f"[{correlation_id}] Recording failure for {agent_id}")
                    # Record failed execution (may affect trust score)
                    if hasattr(self.justica, 'record_execution_failure'):
                        await self.justica.record_execution_failure(agent_id, correlation_id)

                # Log current trust score for observability
                current_trust = self.justica.get_trust_score(agent_id)
                span.set_attribute("metrics.trust_score", current_trust)
                logger.debug(f"[{correlation_id}] Agent {agent_id} trust score: {current_trust:.2f}")

        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
