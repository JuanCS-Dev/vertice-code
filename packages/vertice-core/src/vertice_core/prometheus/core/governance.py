"""
Prometheus Governance Bridge.

Connects Prometheus to SOFIA (Ethical Counselor) and JUSTICA (Constitutional Governance).
Ensures L4 autonomous actions are aligned with Vértice principles.

Capabilities:
- SofiaReview: Deliberation on ethical dimensions and risk.
- JusticaVerdict: Constitutional alignment check.
- VetoPower: Ability to halt high-risk actions.

Phase 5 of Prometheus Integration Roadmap v2.7.
Created with love by: JuanCS Dev & Claude Opus 4.5
Date: 2026-01-06
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from vertice_core.agents.justica_agent import JusticaIntegratedAgent
from vertice_governance.justica import EnforcementMode
from vertice_governance.sofia.agent.core import SofiaAgent

logger = logging.getLogger(__name__)


@dataclass
class GovernanceVerdict:
    """Verdict from the governance system."""

    approved: bool
    reasoning: str
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    governor: str  # JUSTICA or SOFIA
    suggestions: Optional[str] = None


class PrometheusGovernanceBridge:
    """
    Bridge for SOFIA and JUSTICA governance.

    Implements the 'Guardian Agent' pattern from CODE_CONSTITUTION.
    """

    def __init__(self, llm_client: Any, mcp_client: Any):
        # Initialize JUSTICA (Normative mode for balanced enforcement)
        self.justica = JusticaIntegratedAgent(
            llm_client=llm_client,
            mcp_client=mcp_client,
            enforcement_mode=EnforcementMode.NORMATIVE,
            verbose_ui=True,
        )

        # Initialize SOFIA (Wise Counselor)
        self.sofia = SofiaAgent()
        self.sofia.start()

    async def review_task(self, task: str, context: Dict[str, Any]) -> GovernanceVerdict:
        """
        Perform a pre-execution review of a task.

        Evaluates constitutional alignment and ethical risk.
        """
        logger.info(f"[Governance] Reviewing task: {task[:50]}...")

        # 1. First, consult SOFIA for deliberation if task looks complex/risky
        sofia_counsel = self.sofia.respond(task, context=context)

        if sofia_counsel.confidence < 0.4:
            return GovernanceVerdict(
                approved=False,
                reasoning=f"SOFIA expressed high uncertainty: {sofia_counsel.response}",
                risk_level="HIGH",
                governor="SOFIA",
                suggestions="Clarify user intent or seek human approval.",
            )

        # 2. Then, get a verdict from JUSTICA
        # We adapt the task into a format JUSTICA understands
        verdict = await self.justica.evaluate_action(
            agent_id="prometheus", action_type="autonomous_execution", content=task, context=context
        )

        return GovernanceVerdict(
            approved=verdict.approved,
            reasoning=verdict.reasoning,
            risk_level="HIGH" if not verdict.approved else "LOW",
            governor="JUSTICA",
        )

    def get_governance_status(self) -> Dict[str, Any]:
        """Get status of governance systems."""
        return {
            "justica_active": True,
            "sofia_active": True,
            "sofia_state": self.sofia.state.name,
            "metrics": self.justica.get_all_metrics(),
        }
