"""
AI Audit Service - ISO 42001 Compliance
Comprehensive logging of AI interactions for safety and compliance
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from .database import get_db_session
from .guardrails import get_ai_safety_guardrails, SafetyResult, SafetyViolation

logger = logging.getLogger(__name__)


@dataclass
class AIAuditEntry:
    """Audit entry for AI interactions."""

    workspace_id: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    session_id: Optional[str] = None

    # Interaction data
    input_prompt: str
    output_generated: Optional[str] = None
    model_used: str = ""
    latency_ms: Optional[int] = None
    token_count: Optional[int] = None
    cost_cents: Optional[float] = None

    # Safety results
    input_safety: Optional[SafetyResult] = None
    output_safety: Optional[SafetyResult] = None

    # Metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    context: Dict[str, Any] = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}


class AIAuditService:
    """
    Service for comprehensive AI interaction auditing.
    Implements ISO 42001 requirements for AI safety logging.
    """

    def __init__(self):
        self.guardrails = get_ai_safety_guardrails()

    async def audit_ai_interaction(self, entry: AIAuditEntry, persist_to_db: bool = True) -> str:
        """
        Audit a complete AI interaction with safety checks.

        Args:
            entry: The audit entry to process
            persist_to_db: Whether to persist to database

        Returns:
            Audit log ID
        """
        start_time = time.time()

        # Perform safety checks if not already done
        if entry.input_safety is None:
            entry.input_safety, _ = await self.guardrails.check_interaction(
                entry.input_prompt, None, {"workspace_id": entry.workspace_id}
            )

        if entry.output_generated and entry.output_safety is None:
            _, entry.output_safety = await self.guardrails.check_interaction(
                entry.input_prompt, entry.output_generated, {"workspace_id": entry.workspace_id}
            )

        # Calculate audit metrics
        processing_time = int((time.time() - start_time) * 1000)
        if entry.latency_ms is None:
            entry.latency_ms = processing_time

        audit_id = await self._persist_audit_entry(entry) if persist_to_db else "dry-run"

        # Log safety violations
        await self._log_safety_violations(entry)

        logger.info(
            f"AI interaction audited: workspace={entry.workspace_id}, "
            f"model={entry.model_used}, safe={self._is_interaction_safe(entry)}"
        )

        return audit_id

    async def audit_prompt_only(
        self,
        workspace_id: str,
        input_prompt: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Quick audit for input prompt only (before AI processing).
        """
        entry = AIAuditEntry(
            workspace_id=workspace_id,
            user_id=user_id,
            session_id=session_id,
            input_prompt=input_prompt,
            context=context or {},
        )

        return await self.audit_ai_interaction(entry, persist_to_db=True)

    async def audit_full_interaction(
        self,
        workspace_id: str,
        input_prompt: str,
        output_generated: str,
        model_used: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        latency_ms: Optional[int] = None,
        token_count: Optional[int] = None,
        cost_cents: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Full audit for complete AI interaction.
        """
        entry = AIAuditEntry(
            workspace_id=workspace_id,
            user_id=user_id,
            agent_id=agent_id,
            session_id=session_id,
            input_prompt=input_prompt,
            output_generated=output_generated,
            model_used=model_used,
            latency_ms=latency_ms,
            token_count=token_count,
            cost_cents=cost_cents,
            context=context or {},
        )

        return await self.audit_ai_interaction(entry, persist_to_db=True)

    async def _persist_audit_entry(self, entry: AIAuditEntry) -> str:
        """Persist audit entry to database."""
        from sqlalchemy import text

        # Prepare safety flags
        safety_flags = {}
        if entry.input_safety:
            safety_flags.update(
                {
                    "input_violations": [v.value for v in entry.input_safety.violations],
                    "input_severity": entry.input_safety.severity.value,
                    "input_confidence": entry.input_safety.confidence_score,
                }
            )
        if entry.output_safety:
            safety_flags.update(
                {
                    "output_violations": [v.value for v in entry.output_safety.violations],
                    "output_severity": entry.output_safety.severity.value,
                    "output_confidence": entry.output_safety.confidence_score,
                }
            )

        # Calculate bias score (simplified - would use ML model in production)
        bias_score = self._calculate_bias_score(entry)

        # Insert into database
        query = text(
            """
            INSERT INTO audit_log (
                workspace_id, event_type, actor_type, actor_id, actor_ip,
                ai_interaction, input_prompt, output_generated, model_used,
                latency_ms, token_count, cost_cents, safety_flags, bias_score,
                metadata, created_at
            ) VALUES (
                :workspace_id, :event_type, :actor_type, :actor_id, :actor_ip,
                :ai_interaction, :input_prompt, :output_generated, :model_used,
                :latency_ms, :token_count, :cost_cents, :safety_flags, :bias_score,
                :metadata, NOW()
            )
            RETURNING id
        """
        )

        async with get_db_session() as session:
            result = await session.execute(
                query,
                {
                    "workspace_id": entry.workspace_id,
                    "event_type": "ai_interaction_complete",
                    "actor_type": "agent" if entry.agent_id else "user",
                    "actor_id": entry.agent_id or entry.user_id,
                    "actor_ip": entry.ip_address,
                    "ai_interaction": True,
                    "input_prompt": entry.input_prompt,
                    "output_generated": entry.output_generated,
                    "model_used": entry.model_used,
                    "latency_ms": entry.latency_ms,
                    "token_count": entry.token_count,
                    "cost_cents": entry.cost_cents,
                    "safety_flags": safety_flags,
                    "bias_score": bias_score,
                    "metadata": {
                        "session_id": entry.session_id,
                        "user_agent": entry.user_agent,
                        "context": entry.context,
                    },
                },
            )

            audit_id = str((await result.fetchone())[0])
            await session.commit()

            return audit_id

    def _calculate_bias_score(self, entry: AIAuditEntry) -> Optional[float]:
        """Calculate bias score for the interaction (simplified implementation)."""
        if not entry.output_generated:
            return None

        # Simple heuristic - in production would use ML model
        bias_indicators = [
            "gender",
            "race",
            "ethnicity",
            "religion",
            "sexual orientation",
            "disability",
            "age",
            "nationality",
        ]

        text_lower = entry.output_generated.lower()
        bias_count = sum(1 for indicator in bias_indicators if indicator in text_lower)

        # Normalize to 0.0-1.0 scale (higher = more biased)
        if bias_count > 5:
            return 1.0
        elif bias_count > 2:
            return 0.7
        elif bias_count > 0:
            return 0.4
        else:
            return 0.1

    def _is_interaction_safe(self, entry: AIAuditEntry) -> bool:
        """Check if the interaction passed safety checks."""
        input_safe = entry.input_safety.is_safe if entry.input_safety else True
        output_safe = entry.output_safety.is_safe if entry.output_safety else True
        return input_safe and output_safe

    async def _log_safety_violations(self, entry: AIAuditEntry) -> None:
        """Log safety violations at appropriate levels."""
        if entry.input_safety and not entry.input_safety.is_safe:
            logger.warning(
                f"Input safety violation: {entry.input_safety.violations} "
                f"for workspace {entry.workspace_id}"
            )

        if entry.output_safety and not entry.output_safety.is_safe:
            severity = entry.output_safety.severity
            if severity.value == "critical":
                logger.error(
                    f"Critical output safety violation: {entry.output_safety.violations} "
                    f"for workspace {entry.workspace_id}"
                )
            else:
                logger.warning(
                    f"Output safety violation: {entry.output_safety.violations} "
                    f"for workspace {entry.workspace_id}"
                )

    async def get_audit_summary(self, workspace_id: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get audit summary for safety monitoring.
        """
        from sqlalchemy import text

        query = text(
            """
            SELECT
                COUNT(*) as total_interactions,
                COUNT(CASE WHEN safety_flags->>'input_violations' IS NOT NULL THEN 1 END) as input_violations,
                COUNT(CASE WHEN safety_flags->>'output_violations' IS NOT NULL THEN 1 END) as output_violations,
                AVG(latency_ms) as avg_latency,
                SUM(cost_cents) as total_cost,
                AVG(bias_score) as avg_bias_score
            FROM audit_log
            WHERE workspace_id = :workspace_id
            AND ai_interaction = true
            AND created_at > NOW() - INTERVAL ':hours hours'
        """
        )

        async with get_db_session() as session:
            result = await session.execute(query, {"workspace_id": workspace_id, "hours": hours})

            row = await result.fetchone()
            return dict(row) if row else {}


# Global instance
_audit_service: Optional[AIAuditService] = None


def get_ai_audit_service() -> AIAuditService:
    """Get global AI audit service instance."""
    global _audit_service
    if _audit_service is None:
        _audit_service = AIAuditService()
    return _audit_service
