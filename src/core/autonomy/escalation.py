"""
Escalation Manager

Manages human-in-the-loop escalation workflow.

References:
- arXiv:2307.15042 (Staged Autonomy)
- Constitutional AI (Anthropic, 2022)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .types import (
    AutonomyDecision,
    EscalationRequest,
    EscalationReason,
    AutonomyConfig,
)

logger = logging.getLogger(__name__)


class EscalationManager:
    """
    Manages escalation requests to human overseers.

    Implements:
    - Escalation queue with priority
    - Timeout handling
    - Response routing
    - Learning from escalation outcomes
    """

    def __init__(
        self,
        config: Optional[AutonomyConfig] = None,
        on_escalation: Optional[Callable[[EscalationRequest], None]] = None,
    ):
        """
        Initialize escalation manager.

        Args:
            config: Autonomy configuration
            on_escalation: Callback when escalation is created
        """
        self._config = config or AutonomyConfig()
        self._on_escalation = on_escalation

        # Pending escalations by ID
        self._pending: Dict[str, EscalationRequest] = {}

        # Escalation history
        self._history: List[EscalationRequest] = []

        # Response futures for async waiting
        self._response_futures: Dict[str, asyncio.Future] = {}

    def create_escalation(
        self,
        decision: AutonomyDecision,
        reason: EscalationReason,
        options: Optional[List[str]] = None,
        recommended: Optional[str] = None,
    ) -> EscalationRequest:
        """
        Create an escalation request.

        Args:
            decision: The decision requiring escalation
            reason: Reason for escalation
            options: Available options for human
            recommended: Recommended option

        Returns:
            EscalationRequest
        """
        # Check max pending
        if len(self._pending) >= self._config.max_pending_escalations:
            oldest_id = next(iter(self._pending))
            self._timeout_escalation(oldest_id)

        # Determine severity
        severity = self._determine_severity(decision, reason)

        # Generate default options if not provided
        if options is None:
            options = ["approve", "deny", "modify"]

        request = EscalationRequest(
            action=decision.action,
            context=decision.context,
            original_decision=decision,
            reason=reason,
            severity=severity,
            timeout_seconds=self._config.escalation_timeout_seconds,
            options=options,
            recommended_option=recommended,
        )

        self._pending[request.id] = request

        logger.info(
            f"[Escalation] Created: id={request.id}, reason={reason.value}, "
            f"severity={severity}, options={options}"
        )

        # Notify callback if registered
        if self._on_escalation:
            self._on_escalation(request)

        return request

    async def wait_for_response(
        self,
        request_id: str,
        timeout: Optional[int] = None,
    ) -> Optional[str]:
        """
        Wait for human response to an escalation.

        Args:
            request_id: Escalation request ID
            timeout: Optional timeout override

        Returns:
            Human response or None if timeout
        """
        if request_id not in self._pending:
            return None

        request = self._pending[request_id]
        effective_timeout = timeout or request.timeout_seconds

        # Create future for response
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        self._response_futures[request_id] = future

        try:
            response = await asyncio.wait_for(future, timeout=effective_timeout)
            return response
        except asyncio.TimeoutError:
            self._timeout_escalation(request_id)
            return None
        finally:
            self._response_futures.pop(request_id, None)

    def respond(
        self,
        request_id: str,
        response: str,
    ) -> bool:
        """
        Submit human response to an escalation.

        Args:
            request_id: Escalation request ID
            response: Human's response

        Returns:
            True if response was accepted
        """
        if request_id not in self._pending:
            logger.warning(f"[Escalation] Response for unknown request: {request_id}")
            return False

        request = self._pending[request_id]

        # Validate response against options
        if request.options and response not in request.options:
            logger.warning(
                f"[Escalation] Invalid response '{response}', "
                f"expected one of {request.options}"
            )
            # Allow anyway but log warning

        # Update request
        request.human_response = response
        request.response_timestamp = datetime.now().isoformat()
        request.resolved = True

        # Move to history
        del self._pending[request_id]
        self._history.append(request)

        # Resolve any waiting future
        if request_id in self._response_futures:
            future = self._response_futures[request_id]
            if not future.done():
                future.set_result(response)

        logger.info(
            f"[Escalation] Resolved: id={request_id}, response={response}"
        )

        return True

    def get_pending(self) -> List[EscalationRequest]:
        """Get all pending escalation requests."""
        return list(self._pending.values())

    def get_pending_by_severity(self, severity: str) -> List[EscalationRequest]:
        """Get pending requests filtered by severity."""
        return [r for r in self._pending.values() if r.severity == severity]

    def get_request(self, request_id: str) -> Optional[EscalationRequest]:
        """Get a specific escalation request."""
        return self._pending.get(request_id) or next(
            (r for r in self._history if r.id == request_id), None
        )

    def cancel(self, request_id: str) -> bool:
        """
        Cancel a pending escalation.

        Args:
            request_id: Escalation request ID

        Returns:
            True if cancelled
        """
        if request_id not in self._pending:
            return False

        request = self._pending[request_id]
        request.resolved = True
        request.human_response = "cancelled"

        del self._pending[request_id]
        self._history.append(request)

        # Cancel any waiting future
        if request_id in self._response_futures:
            future = self._response_futures[request_id]
            if not future.done():
                future.cancel()

        logger.info(f"[Escalation] Cancelled: id={request_id}")
        return True

    def _timeout_escalation(self, request_id: str) -> None:
        """Handle escalation timeout."""
        if request_id not in self._pending:
            return

        request = self._pending[request_id]
        request.resolved = True

        if self._config.auto_deny_on_timeout:
            request.human_response = "denied_timeout"
        else:
            request.human_response = "timeout"

        del self._pending[request_id]
        self._history.append(request)

        # Cancel any waiting future
        if request_id in self._response_futures:
            future = self._response_futures[request_id]
            if not future.done():
                future.set_result(None)

        logger.warning(f"[Escalation] Timeout: id={request_id}")

    def _determine_severity(
        self,
        decision: AutonomyDecision,
        reason: EscalationReason,
    ) -> str:
        """Determine severity level for escalation."""
        # Critical: safety concerns or policy violations
        if reason in [EscalationReason.SAFETY_CONCERN, EscalationReason.POLICY_VIOLATION]:
            return "critical"

        # High: high risk actions
        if decision.risk_level >= 0.8 or reason == EscalationReason.HIGH_RISK:
            return "high"

        # Medium: low confidence or ambiguous input
        if reason in [EscalationReason.LOW_CONFIDENCE, EscalationReason.AMBIGUOUS_INPUT]:
            return "medium"

        # Low: user preference or novel situations
        return "low"

    def get_stats(self) -> Dict[str, Any]:
        """Get escalation statistics."""
        total = len(self._history)
        if total == 0:
            return {
                "total_escalations": 0,
                "pending_count": len(self._pending),
            }

        approved = sum(1 for r in self._history if r.human_response == "approve")
        denied = sum(1 for r in self._history if r.human_response == "deny")
        timeout = sum(1 for r in self._history if "timeout" in (r.human_response or ""))

        by_reason = {}
        for r in self._history:
            reason = r.reason.value
            by_reason[reason] = by_reason.get(reason, 0) + 1

        by_severity = {}
        for r in self._history:
            by_severity[r.severity] = by_severity.get(r.severity, 0) + 1

        return {
            "total_escalations": total,
            "pending_count": len(self._pending),
            "approved_count": approved,
            "denied_count": denied,
            "timeout_count": timeout,
            "approval_rate": approved / total if total > 0 else 0.0,
            "by_reason": by_reason,
            "by_severity": by_severity,
        }

    def clear_history(self) -> None:
        """Clear escalation history."""
        self._history.clear()
