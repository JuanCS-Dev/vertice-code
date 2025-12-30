"""
Phase 7 Integration Tests - Resilience and Caching Mixin Integration.

Tests that all 6 agents correctly inherit ResilienceMixin and CachingMixin
and can use their methods.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock

import pytest

from agents.coder.agent import CoderAgent
from agents.reviewer.agent import ReviewerAgent
from agents.architect.agent import ArchitectAgent
from agents.researcher.agent import ResearcherAgent
from agents.devops.agent import DevOpsAgent
from agents.orchestrator.agent import OrchestratorAgent
from core.resilience import ResilienceMixin, TransientError
from core.caching import CachingMixin


# ============================================================================
# Test Agent Inheritance
# ============================================================================


class TestAgentInheritance:
    """Tests that all agents inherit resilience and caching mixins."""

    def test_coder_has_resilience_mixin(self) -> None:
        """CoderAgent inherits ResilienceMixin."""
        assert issubclass(CoderAgent, ResilienceMixin)

    def test_coder_has_caching_mixin(self) -> None:
        """CoderAgent inherits CachingMixin."""
        assert issubclass(CoderAgent, CachingMixin)

    def test_reviewer_has_resilience_mixin(self) -> None:
        """ReviewerAgent inherits ResilienceMixin."""
        assert issubclass(ReviewerAgent, ResilienceMixin)

    def test_reviewer_has_caching_mixin(self) -> None:
        """ReviewerAgent inherits CachingMixin."""
        assert issubclass(ReviewerAgent, CachingMixin)

    def test_architect_has_resilience_mixin(self) -> None:
        """ArchitectAgent inherits ResilienceMixin."""
        assert issubclass(ArchitectAgent, ResilienceMixin)

    def test_architect_has_caching_mixin(self) -> None:
        """ArchitectAgent inherits CachingMixin."""
        assert issubclass(ArchitectAgent, CachingMixin)

    def test_researcher_has_resilience_mixin(self) -> None:
        """ResearcherAgent inherits ResilienceMixin."""
        assert issubclass(ResearcherAgent, ResilienceMixin)

    def test_researcher_has_caching_mixin(self) -> None:
        """ResearcherAgent inherits CachingMixin."""
        assert issubclass(ResearcherAgent, CachingMixin)

    def test_devops_has_resilience_mixin(self) -> None:
        """DevOpsAgent inherits ResilienceMixin."""
        assert issubclass(DevOpsAgent, ResilienceMixin)

    def test_devops_has_caching_mixin(self) -> None:
        """DevOpsAgent inherits CachingMixin."""
        assert issubclass(DevOpsAgent, CachingMixin)

    def test_orchestrator_has_resilience_mixin(self) -> None:
        """OrchestratorAgent inherits ResilienceMixin."""
        assert issubclass(OrchestratorAgent, ResilienceMixin)

    def test_orchestrator_has_caching_mixin(self) -> None:
        """OrchestratorAgent inherits CachingMixin."""
        assert issubclass(OrchestratorAgent, CachingMixin)


# ============================================================================
# Test Resilience Methods Available
# ============================================================================


class TestResilienceMethods:
    """Tests that resilience methods are available on agents."""

    def test_coder_has_resilient_call(self) -> None:
        """CoderAgent has resilient_call method."""
        agent = CoderAgent()
        assert hasattr(agent, "resilient_call")
        assert callable(agent.resilient_call)

    def test_coder_has_get_resilience_stats(self) -> None:
        """CoderAgent has get_resilience_stats method."""
        agent = CoderAgent()
        assert hasattr(agent, "get_resilience_stats")

    def test_reviewer_has_resilient_call(self) -> None:
        """ReviewerAgent has resilient_call method."""
        agent = ReviewerAgent()
        assert hasattr(agent, "resilient_call")

    def test_architect_has_resilient_call(self) -> None:
        """ArchitectAgent has resilient_call method."""
        agent = ArchitectAgent()
        assert hasattr(agent, "resilient_call")

    def test_researcher_has_resilient_call(self) -> None:
        """ResearcherAgent has resilient_call method."""
        agent = ResearcherAgent()
        assert hasattr(agent, "resilient_call")

    def test_devops_has_resilient_call(self) -> None:
        """DevOpsAgent has resilient_call method."""
        agent = DevOpsAgent()
        assert hasattr(agent, "resilient_call")

    def test_orchestrator_has_resilient_call(self) -> None:
        """OrchestratorAgent has resilient_call method."""
        agent = OrchestratorAgent()
        assert hasattr(agent, "resilient_call")


# ============================================================================
# Test Caching Methods Available
# ============================================================================


class TestCachingMethods:
    """Tests that caching methods are available on agents."""

    def test_coder_has_cached_call(self) -> None:
        """CoderAgent has cached_call method."""
        agent = CoderAgent()
        assert hasattr(agent, "cached_call")
        assert callable(agent.cached_call)

    def test_coder_has_get_cache_stats(self) -> None:
        """CoderAgent has get_cache_stats method."""
        agent = CoderAgent()
        assert hasattr(agent, "get_cache_stats")

    def test_coder_has_invalidate_cache(self) -> None:
        """CoderAgent has invalidate_cache method."""
        agent = CoderAgent()
        assert hasattr(agent, "invalidate_cache")

    def test_reviewer_has_cached_call(self) -> None:
        """ReviewerAgent has cached_call method."""
        agent = ReviewerAgent()
        assert hasattr(agent, "cached_call")

    def test_architect_has_cached_call(self) -> None:
        """ArchitectAgent has cached_call method."""
        agent = ArchitectAgent()
        assert hasattr(agent, "cached_call")

    def test_researcher_has_cached_call(self) -> None:
        """ResearcherAgent has cached_call method."""
        agent = ResearcherAgent()
        assert hasattr(agent, "cached_call")

    def test_devops_has_cached_call(self) -> None:
        """DevOpsAgent has cached_call method."""
        agent = DevOpsAgent()
        assert hasattr(agent, "cached_call")

    def test_orchestrator_has_cached_call(self) -> None:
        """OrchestratorAgent has cached_call method."""
        agent = OrchestratorAgent()
        assert hasattr(agent, "cached_call")


# ============================================================================
# Test Resilient Call Execution
# ============================================================================


class TestResilientCallExecution:
    """Tests resilient_call execution behavior."""

    @pytest.mark.asyncio
    async def test_resilient_call_success(self) -> None:
        """Resilient call succeeds on first try."""
        agent = CoderAgent()

        async def success_func() -> str:
            return "success"

        result = await agent.resilient_call(success_func, provider="test")
        assert result == "success"

    @pytest.mark.asyncio
    async def test_resilient_call_retry_on_transient(self) -> None:
        """Resilient call retries on transient error."""
        agent = CoderAgent()
        attempts = 0

        async def flaky_func() -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise TransientError("Temporary failure")
            return "success"

        result = await agent.resilient_call(flaky_func, provider="test")
        assert result == "success"
        assert attempts == 2

    @pytest.mark.asyncio
    async def test_resilient_call_stats_tracked(self) -> None:
        """Resilient call tracks statistics."""
        agent = CoderAgent()

        async def success_func() -> str:
            return "ok"

        await agent.resilient_call(success_func, provider="test")
        stats = agent.get_resilience_stats()
        assert "total_calls" in stats
        assert stats["total_calls"] >= 1


# ============================================================================
# Test Cached Call Execution
# ============================================================================


class TestCachedCallExecution:
    """Tests cached_call execution behavior."""

    @pytest.mark.asyncio
    async def test_cached_call_caches_result(self) -> None:
        """Cached call caches result on first call."""
        agent = CoderAgent()
        call_count = 0

        async def expensive_func() -> str:
            nonlocal call_count
            call_count += 1
            return "result"

        # First call
        result1 = await agent.cached_call(expensive_func, cache_key="test_key")
        assert result1 == "result"
        assert call_count == 1

        # Second call - should use cache
        result2 = await agent.cached_call(expensive_func, cache_key="test_key")
        assert result2 == "result"
        assert call_count == 1  # Not called again

    @pytest.mark.asyncio
    async def test_cached_call_skip_cache(self) -> None:
        """Skip cache bypasses cache lookup."""
        agent = CoderAgent()
        call_count = 0

        async def func() -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{call_count}"

        await agent.cached_call(func, cache_key="key")
        result = await agent.cached_call(func, cache_key="key", skip_cache=True)
        assert call_count == 2
        assert result == "result_2"

    @pytest.mark.asyncio
    async def test_cached_call_stats_tracked(self) -> None:
        """Cached call tracks statistics."""
        agent = CoderAgent()

        async def func() -> str:
            return "ok"

        await agent.cached_call(func, cache_key="key")
        stats = agent.get_cache_stats()
        assert "total_calls" in stats

    @pytest.mark.asyncio
    async def test_invalidate_cache_clears_entry(self) -> None:
        """Invalidate cache clears specific entry."""
        agent = CoderAgent()
        call_count = 0

        async def func() -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{call_count}"

        await agent.cached_call(func, cache_key="key")
        await agent.invalidate_cache(key="key")

        # Should call function again after invalidation
        result = await agent.cached_call(func, cache_key="key")
        assert call_count == 2
        assert result == "result_2"


# ============================================================================
# Test Prometheus Metrics Generation
# ============================================================================


class TestPrometheusMetrics:
    """Tests Prometheus metrics generation."""

    def test_resilience_prometheus_metrics(self) -> None:
        """Generates Prometheus resilience metrics."""
        agent = CoderAgent()
        agent._init_resilience()

        metrics = agent.get_prometheus_resilience_metrics()
        assert "resilience_calls_total" in metrics

    def test_cache_prometheus_metrics(self) -> None:
        """Generates Prometheus cache metrics."""
        agent = CoderAgent()
        agent._init_caching()

        metrics = agent.get_prometheus_cache_metrics()
        assert "cache_calls_total" in metrics


# ============================================================================
# Test MRO (Method Resolution Order)
# ============================================================================


class TestMethodResolutionOrder:
    """Tests that MRO is correct for all agents."""

    def test_coder_mro(self) -> None:
        """CoderAgent MRO has ResilienceMixin before BaseAgent."""
        mro = CoderAgent.__mro__
        mro_names = [cls.__name__ for cls in mro]
        assert "ResilienceMixin" in mro_names
        assert "CachingMixin" in mro_names
        assert "BaseAgent" in mro_names
        # ResilienceMixin should come before BaseAgent
        assert mro_names.index("ResilienceMixin") < mro_names.index("BaseAgent")

    def test_all_agents_have_correct_mro(self) -> None:
        """All agents have correct MRO."""
        agents = [
            CoderAgent,
            ReviewerAgent,
            ArchitectAgent,
            ResearcherAgent,
            DevOpsAgent,
            OrchestratorAgent,
        ]

        for agent_class in agents:
            mro_names = [cls.__name__ for cls in agent_class.__mro__]
            assert "ResilienceMixin" in mro_names, f"{agent_class.__name__} missing ResilienceMixin"
            assert "CachingMixin" in mro_names, f"{agent_class.__name__} missing CachingMixin"
