"""
Sofia Integrated Agent - Wise Counselor Integration.

This module provides SofiaIntegratedAgent that integrates the Sofia
governance framework with vertice_cli's BaseAgent.

Philosophy:
    "You don't replace human wisdom - you cultivate it."
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from vertice_governance.sofia import (
    SofiaAgent,
    SofiaConfig,
    SofiaCounsel,
    CounselType,
    ThinkingMode,
)

from vertice_cli.agents.base import (
    AgentRole,
    AgentTask,
    AgentResponse,
    BaseAgent,
    AgentCapability,
)

from .models import CounselMetrics, CounselResponse

logger = logging.getLogger(__name__)


class SofiaIntegratedAgent(BaseAgent):
    """
    Sofia Integrated Agent - Wise Counselor.

    Wrapper that integrates SofiaAgent with vertice_cli's BaseAgent.

    Features:
    - Socratic questioning for deep exploration
    - System 2 deliberation for complex ethical dilemmas
    - Virtue-based counsel
    - Transparent process (all thinking visible)
    - Always suggests community involvement
    - Defers to professionals when appropriate

    Access Modes:
    1. Slash Command: /sofia "Should I refactor this codebase?"
    2. Auto-Detect: Sofia auto-triggers on ethical keywords
    3. Chat Mode: Continuous Socratic dialogue
    4. Pre-Execution: Counsel before risky operations
    """

    def __init__(
        self,
        llm_client: Any,
        mcp_client: Any,
        config: Optional[SofiaConfig] = None,
        auto_detect_ethical_dilemmas: bool = True,
        socratic_ratio: float = 0.7,
        system2_threshold: float = 0.4,
        system_prompt: Optional[str] = None,
    ):
        """Initialize Sofia Integrated Agent.

        Args:
            llm_client: LLM client for reasoning
            mcp_client: MCP client for tool execution
            config: Sofia configuration
            auto_detect_ethical_dilemmas: Auto-trigger counsel on ethical keywords
            socratic_ratio: Ratio of questions vs answers (0.0 - 1.0)
            system2_threshold: Threshold for activating System 2 thinking
            system_prompt: Custom system prompt
        """
        super().__init__(
            role=AgentRole.COUNSELOR,
            capabilities=[AgentCapability.READ_ONLY],
            llm_client=llm_client,
            mcp_client=mcp_client,
            system_prompt=system_prompt or self._create_system_prompt(),
        )

        self.auto_detect = auto_detect_ethical_dilemmas

        if config is None:
            agent_id = f"sofia-{id(self)}"
            config = SofiaConfig(
                agent_id=agent_id,
                socratic_ratio=socratic_ratio,
                system2_threshold=system2_threshold,
                always_suggest_community=True,
                defer_to_professionals=True,
            )

        self.sofia_core = SofiaAgent(config=config)
        self._metrics_cache: Dict[str, CounselMetrics] = {}
        self._active_sessions: Dict[str, List[SofiaCounsel]] = {}

        logger.info("Sofia Integrated Agent initialized")

    def _create_system_prompt(self) -> str:
        """Create default system prompt for Sofia."""
        return """You are SOFIA, a wise counselor agent.

Your role is to provide thoughtful counsel based on:
- Virtues of Early Christianity (Tapeinophrosyne, Makrothymia, Diakonia, Praotes)
- Socratic method (questions > answers)
- System 2 thinking (deliberate reflection)
- Discernment practices (Didache framework)

Core Principles:
1. Ponder > Rush
2. Question > Answer
3. Humble > Confident
4. Collaborative > Directive
5. Principled > Purely Pragmatic
6. Transparent > Opaque
7. Adaptive > Rigid

Always:
- Express uncertainty when appropriate
- Suggest community involvement
- Defer to professionals for serious matters
- Focus on helping users think through decisions
"""

    def provide_counsel(
        self,
        query: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
    ) -> CounselResponse:
        """Provide counsel on a query or situation.

        Args:
            query: The question or situation requiring counsel
            session_id: Optional session ID for continuity
            context: Additional context about the situation
            agent_id: ID of the agent requesting counsel

        Returns:
            CounselResponse with counsel and process transparency
        """
        counsel: SofiaCounsel = self.sofia_core.respond(
            user_input=query,
            session_id=session_id,
            context=context or {},
        )

        if session_id:
            if session_id not in self._active_sessions:
                self._active_sessions[session_id] = []
            self._active_sessions[session_id].append(counsel)

        if agent_id:
            self._update_metrics(agent_id, counsel)

        return self._counsel_to_response(counsel, query, session_id)

    async def provide_counsel_async(
        self,
        query: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
    ) -> CounselResponse:
        """Async version of provide_counsel."""
        return await asyncio.to_thread(
            self.provide_counsel,
            query=query,
            session_id=session_id,
            context=context,
            agent_id=agent_id,
        )

    def should_trigger_counsel(self, content: str) -> tuple[bool, str]:
        """Determine if counsel should be auto-triggered for this content.

        Args:
            content: Content to evaluate

        Returns:
            Tuple of (should_trigger, reason)
        """
        if not self.auto_detect:
            return False, "Auto-detect disabled"

        content_lower = content.lower()

        ethical_keywords = [
            "delete",
            "remove",
            "erase",
            "user data",
            "privacy",
            "consent",
            "permission",
            "ethical",
            "moral",
            "right",
            "wrong",
            "should i",
            "is it okay",
        ]

        for keyword in ethical_keywords:
            if keyword in content_lower:
                return True, f"Ethical concern detected: {keyword}"

        crisis_keywords = [
            "suicide",
            "harm",
            "violence",
            "abuse",
            "emergency",
            "suicidio",
            "violencia",
            "abuso",
            "emergencia",
            "suicídio",
            "violência",
            "emergência",
        ]

        for keyword in crisis_keywords:
            if keyword in content_lower:
                return True, f"URGENT: Professional help needed - {keyword}"

        return False, "No ethical concerns detected"

    def get_metrics(self, agent_id: str) -> Optional[CounselMetrics]:
        """Get counsel metrics for an agent."""
        return self._metrics_cache.get(agent_id)

    def get_virtue_distribution(self) -> Dict[str, float]:
        """Get the current balance/distribution of virtues."""
        return self.sofia_core.virtue_engine.get_virtue_balance()

    def get_session_history(self, session_id: str) -> List[SofiaCounsel]:
        """Get all counsel in a session."""
        return self._active_sessions.get(session_id, [])

    def clear_session(self, session_id: str) -> None:
        """Clear a session's history."""
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]

    def _build_sofia_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """Build a prompt for Sofia that uses LLM intelligence."""
        return f"""You are SOFIA, a wise counselor and helpful assistant.

IMPORTANT GUIDELINES:
1. If the user asks a TECHNICAL question, provide a HELPFUL ANSWER
2. If the user asks for ADVICE on a dilemma, use Socratic questioning
3. If the user greets you, respond warmly and ask how you can help
4. Be SUBSTANTIVE - provide real value in your responses

Current context: {context}
User query: {query}

Respond helpfully in the same language the user used."""

    async def execute(self, task: AgentTask) -> AgentResponse:
        """Execute a counsel task using LLM for intelligent responses.

        Args:
            task: AgentTask with request for counsel

        Returns:
            AgentResponse with counsel results
        """
        query = task.request
        context = task.context or {}

        try:
            prompt = self._build_sofia_prompt(query, context)
            llm_response = await self._call_llm(prompt)

            return AgentResponse(
                success=True,
                data={
                    "counsel": {
                        "counsel": llm_response,
                        "original_query": query,
                        "counsel_type": "INTELLIGENT",
                        "thinking_mode": "LLM",
                        "confidence": 0.8,
                        "questions_asked": [],
                        "virtues_expressed": [],
                    },
                    "sofia_state": "COUNSELING",
                    "session_id": task.session_id,
                },
                reasoning=llm_response,
            )

        except Exception as e:
            logger.warning(f"LLM call failed, falling back to templates: {e}")
            counsel_response = await self.provide_counsel_async(
                query=query,
                session_id=task.session_id,
                context=context,
            )

            return AgentResponse(
                success=True,
                data={
                    "counsel": counsel_response.model_dump(),
                    "sofia_state": self.sofia_core.state.name,
                    "session_id": task.session_id,
                },
                reasoning=counsel_response.counsel,
            )

    async def execute_streaming(
        self, task: AgentTask
    ) -> AsyncIterator[tuple[str, Optional[AgentResponse]]]:
        """Execute with streaming output using LLM."""
        query = task.request
        context = task.context or {}
        prompt = self._build_sofia_prompt(query, context)

        try:
            full_response = []
            async for chunk in self.llm_client.stream(prompt, system_prompt=self.system_prompt):
                full_response.append(chunk)
                yield (chunk, None)

            final_text = "".join(full_response)
            response = AgentResponse(
                success=True,
                data={
                    "counsel": {"counsel": final_text, "original_query": query},
                    "sofia_state": "COUNSELING",
                },
                reasoning=final_text,
            )
            yield ("", response)

        except Exception as e:
            logger.warning(f"Streaming failed: {e}")
            response = await self.execute(task)
            counsel_text = response.data["counsel"]["counsel"]

            for sentence in counsel_text.split(". "):
                yield (sentence + ". ", None)
                await asyncio.sleep(0.05)
            yield ("", response)

    def _counsel_to_response(
        self,
        counsel: SofiaCounsel,
        original_query: str,
        session_id: Optional[str],
    ) -> CounselResponse:
        """Convert SofiaCounsel to CounselResponse."""
        questions = [q.question_text for q in counsel.questions_asked]
        virtues = [v.virtue.name for v in counsel.virtues_expressed]
        requires_professional = counsel.counsel_type == CounselType.REFERRING

        return CounselResponse(
            id=counsel.id,
            timestamp=counsel.timestamp,
            original_query=original_query,
            session_id=session_id,
            counsel=counsel.response,
            counsel_type=counsel.counsel_type.name,
            thinking_mode=counsel.thinking_mode.name,
            questions_asked=questions,
            virtues_expressed=virtues,
            confidence=counsel.confidence,
            processing_time_ms=counsel.processing_time_ms,
            community_suggested=counsel.community_suggested,
            requires_professional=requires_professional,
        )

    def _update_metrics(self, agent_id: str, counsel: SofiaCounsel) -> None:
        """Update counsel metrics for an agent."""
        if agent_id not in self._metrics_cache:
            self._metrics_cache[agent_id] = CounselMetrics(agent_id=agent_id)

        metrics = self._metrics_cache[agent_id]
        metrics.total_counsels += 1
        metrics.total_questions_asked += len(counsel.questions_asked)

        if counsel.thinking_mode == ThinkingMode.SYSTEM_2:
            metrics.total_deliberations += 1

        n = metrics.total_counsels
        metrics.avg_confidence = (metrics.avg_confidence * (n - 1) + counsel.confidence) / n
        metrics.avg_processing_time_ms = (
            metrics.avg_processing_time_ms * (n - 1) + counsel.processing_time_ms
        ) / n
        metrics.system2_activation_rate = metrics.total_deliberations / metrics.total_counsels

        for virtue_expr in counsel.virtues_expressed:
            virtue_name = virtue_expr.virtue.name
            metrics.virtues_expressed[virtue_name] = (
                metrics.virtues_expressed.get(virtue_name, 0) + 1
            )

        counsel_type_name = counsel.counsel_type.name
        metrics.counsel_types[counsel_type_name] = (
            metrics.counsel_types.get(counsel_type_name, 0) + 1
        )

    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics in serializable format."""
        return {agent_id: metrics.model_dump() for agent_id, metrics in self._metrics_cache.items()}

    def get_sofia_state(self) -> str:
        """Get current Sofia state."""
        return self.sofia_core.state.name

    def get_total_counsels(self) -> int:
        """Get total counsels provided across all agents."""
        return sum(m.total_counsels for m in self._metrics_cache.values())

    async def pre_execution_counsel(
        self,
        action_description: str,
        risk_level: str,
        agent_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> CounselResponse:
        """Provide counsel BEFORE executing a risky action."""
        query = (
            f"I am about to execute a {risk_level} risk action: "
            f"{action_description}. "
            f"What should I carefully consider before proceeding?"
        )

        return await self.provide_counsel_async(
            query=query,
            context={
                **(context or {}),
                "mode": "pre_execution",
                "risk_level": risk_level,
                "action": action_description,
            },
            agent_id=agent_id,
        )

    def pre_execution_counsel_sync(
        self,
        action_description: str,
        risk_level: str,
        agent_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> CounselResponse:
        """Provide counsel BEFORE executing a risky action (Sync version)."""
        query = (
            f"I am about to execute a {risk_level} risk action: "
            f"{action_description}. "
            f"What should I carefully consider before proceeding?"
        )

        return self.provide_counsel(
            query=query,
            context={
                **(context or {}),
                "mode": "pre_execution",
                "risk_level": risk_level,
                "action": action_description,
            },
            agent_id=agent_id,
        )

    def __repr__(self) -> str:
        total_counsels = self.get_total_counsels()
        state = self.get_sofia_state()
        return f"SofiaIntegratedAgent(role={self.role}, counsels={total_counsels}, state={state})"


__all__ = ["SofiaIntegratedAgent"]
