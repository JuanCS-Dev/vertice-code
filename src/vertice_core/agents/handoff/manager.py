"""Handoff Manager implementation."""

from __future__ import annotations
import asyncio
import logging
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Set
from ..context import DecisionType, UnifiedContext
from ..router import AgentType
from .types import (
    HandoffStatus,
    HandoffReason,
    HandoffRequest,
    HandoffResult,
    AgentCapability,
    EscalationChain,
)
from .config import DEFAULT_CAPABILITIES, DEFAULT_ESCALATION_CHAINS
from .selection import AgentSelector

logger = logging.getLogger(__name__)


class HandoffManager:
    """Manages agent handoffs and transfers."""

    def __init__(
        self,
        context: UnifiedContext,
        capabilities: Optional[Dict[AgentType, AgentCapability]] = None,
        escalation_chains: Optional[List[EscalationChain]] = None,
    ):
        self.context = context
        self.capabilities = capabilities or DEFAULT_CAPABILITIES.copy()
        self.escalation_chains = escalation_chains or DEFAULT_ESCALATION_CHAINS.copy()
        self.selector = AgentSelector(self.capabilities, self.escalation_chains)
        self._handoff_history: List[HandoffResult] = []
        self._pending_handoffs: List[HandoffRequest] = []
        self._pre_handoff: Optional[Callable[[HandoffRequest], bool]] = None
        self._post_handoff: Optional[Callable[[HandoffResult], None]] = None

    def create_handoff(
        self,
        to_agent: Optional[AgentType] = None,
        reason: HandoffReason = HandoffReason.TASK_COMPLETION,
        message: str = "",
        required_capabilities: Optional[Set[str]] = None,
        context_updates: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> HandoffRequest:
        from_agent = AgentType(self.context.current_agent or "chat")
        request = HandoffRequest(
            from_agent=from_agent,
            to_agent=to_agent,
            reason=reason,
            message=message,
            required_capabilities=required_capabilities or set(),
            context_updates=context_updates or {},
            **kwargs,
        )
        logger.debug(f"Created handoff request: {from_agent.value} → {to_agent}")
        return request

    def create_swarm_handoff(
        self,
        agent_type: AgentType,
        context_updates: Optional[Dict[str, Any]] = None,
    ) -> HandoffRequest:
        return self.create_handoff(
            to_agent=agent_type,
            reason=HandoffReason.TASK_COMPLETION,
            context_updates=context_updates,
        )

    def select_agent(self, *args, **kwargs):
        return self.selector.select_agent(*args, **kwargs)

    def get_escalation_target(self, *args, **kwargs):
        return self.selector.get_escalation_target(*args, **kwargs)

    async def execute_handoff(self, request: HandoffRequest) -> HandoffResult:
        start_time = time.time()
        request.status = HandoffStatus.IN_PROGRESS
        try:
            if self._pre_handoff and not self._pre_handoff(request):
                request.status = HandoffStatus.REJECTED
                return HandoffResult(
                    request_id=request.request_id,
                    success=False,
                    from_agent=request.from_agent,
                    to_agent=request.from_agent,
                    error="Handoff rejected by pre-handoff hook",
                )
            target_agent = request.to_agent
            if target_agent is None:
                if request.required_capabilities:
                    target_agent = self.select_agent(request.required_capabilities)
                elif request.reason == HandoffReason.ESCALATION:
                    target_agent = self.get_escalation_target(request.from_agent)
            if target_agent is None:
                request.status = HandoffStatus.FAILED
                return HandoffResult(
                    request_id=request.request_id,
                    success=False,
                    from_agent=request.from_agent,
                    to_agent=request.from_agent,
                    error="No suitable agent found for handoff",
                )
            request.actual_to_agent = target_agent
            if request.context_updates:
                self.context.update(request.context_updates)
            self.context.record_decision(
                f"Handoff: {request.from_agent.value} → {target_agent.value}",
                DecisionType.HANDOFF,
                1.0,  # confidence
                f"Reason: {request.reason.value}",
                agent_id=request.from_agent.value,
            )
            self.context.current_agent = target_agent.value
            request.status = HandoffStatus.COMPLETED
            request.completed_at = time.time()
            duration_ms = (time.time() - start_time) * 1000
            result = HandoffResult(
                request_id=request.request_id,
                success=True,
                from_agent=request.from_agent,
                to_agent=target_agent,
                duration_ms=duration_ms,
                message=f"Handoff complete: {request.from_agent.value} → {target_agent.value}",
            )
            self._handoff_history.append(result)
            if self._post_handoff:
                self._post_handoff(result)
            logger.info(f"Handoff completed: {request.from_agent.value} → {target_agent.value}")
            return result
        except Exception as e:
            request.status = HandoffStatus.FAILED
            request.error = str(e)
            return HandoffResult(
                request_id=request.request_id,
                success=False,
                from_agent=request.from_agent,
                to_agent=request.to_agent or request.from_agent,
                error=str(e),
            )

    async def execute_parallel_handoffs(
        self, requests: List[HandoffRequest]
    ) -> List[HandoffResult]:
        tasks = [self.execute_handoff(req) for req in requests]
        return await asyncio.gather(*tasks)

    async def escalate(self, reason: str = "", chain_name: Optional[str] = None) -> HandoffResult:
        current = AgentType(self.context.current_agent or "chat")
        target = self.get_escalation_target(current, chain_name)
        if not target:
            return HandoffResult(
                request_id=str(uuid.uuid4())[:8],
                success=False,
                from_agent=current,
                to_agent=current,
                error="No escalation target available",
            )
        request = self.create_handoff(
            to_agent=target, reason=HandoffReason.ESCALATION, message=reason
        )
        return await self.execute_handoff(request)

    async def delegate_to(
        self,
        agent_type: AgentType,
        task: str = "",
        context_updates: Optional[Dict[str, Any]] = None,
    ) -> HandoffResult:
        request = self.create_handoff(
            to_agent=agent_type,
            reason=HandoffReason.SPECIALIZATION,
            message=task,
            context_updates=context_updates,
        )
        return await self.execute_handoff(request)

    async def return_to_caller(self, result: str = "") -> HandoffResult:
        if self._handoff_history:
            last = self._handoff_history[-1]
            target = last.from_agent
        else:
            target = AgentType.CHAT
        request = self.create_handoff(
            to_agent=target, reason=HandoffReason.TASK_COMPLETION, message=result
        )
        return await self.execute_handoff(request)

    def get_history(self) -> List[HandoffResult]:
        return self._handoff_history.copy()

    def get_current_agent(self) -> AgentType:
        return AgentType(self.context.current_agent or "chat")

    def get_handoff_chain(self) -> List[AgentType]:
        chain: List[AgentType] = []
        for result in self._handoff_history:
            if result.success:
                if not chain:
                    chain.append(result.from_agent)
                chain.append(result.to_agent)
        return chain

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._handoff_history)
        successful = sum(1 for h in self._handoff_history if h.success)
        return {
            "total_handoffs": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": f"{successful / max(total, 1) * 100:.1f}%",
            "current_agent": self.get_current_agent().value,
            "chain_length": len(self.get_handoff_chain()),
        }

    def set_pre_handoff(self, callback: Callable[[HandoffRequest], bool]) -> None:
        self._pre_handoff = callback

    def set_post_handoff(self, callback: Callable[[HandoffResult], None]) -> None:
        self._post_handoff = callback
