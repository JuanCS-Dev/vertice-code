"""
Tests for SemanticRouter - Sprint 2 Refactoring.

Tests cover:
    - Router initialization and configuration
    - Main routing logic with cache and fallback
    - Cache mixin functionality
    - Stats mixin functionality
    - Route management
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from vertice_core.agents.router.router import SemanticRouter
from vertice_core.agents.router.types import (
    AgentType,
    RouteDefinition,
    RoutingDecision,
    TaskComplexity,
)


class TestSemanticRouterInitialization:
    """Test SemanticRouter initialization and configuration."""

    def test_default_initialization(self) -> None:
        """Test router initialization with defaults."""
        router = SemanticRouter()

        assert router.routes is not None
        assert len(router.routes) > 0  # Should have default routes
        assert hasattr(router, "route")
        assert hasattr(router, "get_cached_decision")

    def test_custom_routes_initialization(self) -> None:
        """Test router with custom routes."""
        custom_routes = [
            RouteDefinition(
                agent_type=AgentType.ARCHITECT,
                name="test_route",
                description="Test routing",
                examples=["test query"],
            )
        ]

        router = SemanticRouter(routes=custom_routes)
        assert router.routes == custom_routes
        assert len(router.routes) == 1


class TestSemanticRouterRouting:
    """Test main routing functionality."""

    def test_route_method_exists(self) -> None:
        """Test that route method exists and is async."""
        router = SemanticRouter()
        assert hasattr(router, "route")
        assert asyncio.iscoroutinefunction(router.route)

    @pytest.mark.asyncio
    async def test_route_with_cache_hit(self) -> None:
        """Test routing with cache hit."""
        router = SemanticRouter()

        # Setup cache hit
        cached_decision = RoutingDecision(
            route_name="cached_route",
            agent_type=AgentType.ARCHITECT,
            confidence=0.95,
            reasoning="From cache",
        )
        router.cache_decision("test query", cached_decision)

        # Route should return cached decision
        result = await router.route("test query")

        assert result == cached_decision
        assert result.agent_type == AgentType.ARCHITECT
        assert result.confidence == 0.95


class TestSemanticRouterCache:
    """Test cache functionality inherited from RouterCacheMixin."""

    def test_cache_decision(self) -> None:
        """Test caching a decision."""
        router = SemanticRouter()

        decision = RoutingDecision(
            route_name="test_route",
            agent_type=AgentType.ARCHITECT,
            confidence=0.88,
            reasoning="Test reasoning",
        )

        router.cache_decision("test query", decision)

        # Should be able to retrieve
        cached = router.get_cached_decision("test query")
        assert cached == decision

    def test_cache_miss(self) -> None:
        """Test cache miss for unknown query."""
        router = SemanticRouter()

        cached = router.get_cached_decision("unknown query")
        assert cached is None

    def test_clear_cache(self) -> None:
        """Test clearing cache."""
        router = SemanticRouter()

        # Add to cache
        decision = RoutingDecision(
            route_name="test_route", agent_type=AgentType.PLANNER, confidence=0.8, reasoning="Test"
        )
        router.cache_decision("query1", decision)
        router.cache_decision("query2", decision)

        # Clear cache
        cleared_count = router.clear_cache()

        assert cleared_count == 2
        assert router.get_cached_decision("query1") is None


class TestSemanticRouterStats:
    """Test stats functionality inherited from RouterStatsMixin."""

    def test_record_route(self) -> None:
        """Test recording a routing decision."""
        router = SemanticRouter()

        decision = RoutingDecision(
            route_name="test_route",
            agent_type=AgentType.EXECUTOR,
            confidence=0.85,
            reasoning="Test",
        )

        router.record_route("test query", decision.confidence, 150.0)  # 150ms

        stats = router.get_stats()
        assert stats["total_routes"] == 1
        assert stats["fast_path"] == 1  # Fast path routing

    def test_record_error(self) -> None:
        """Test recording routing errors."""
        router = SemanticRouter()

        router.record_error()

        stats = router.get_stats()
        assert stats["errors"] == 1


class TestSemanticRouterRouteManagement:
    """Test route management functionality."""

    def test_add_route(self) -> None:
        """Test adding a custom route."""
        router = SemanticRouter()

        initial_count = len(router.routes)

        new_route = RouteDefinition(
            agent_type=AgentType.SECURITY,
            name="security_check",
            description="Security vulnerability checks",
            examples=["check for security issues", "audit security"],
        )

        router.add_route(new_route)

        assert len(router.routes) == initial_count + 1

    def test_get_default_routes(self) -> None:
        """Test that default routes are created."""
        router = SemanticRouter()

        routes = router._get_default_routes()

        assert isinstance(routes, list)
        assert len(routes) > 0


class TestSemanticRouterDecisionCreation:
    """Test decision creation and helper methods."""

    def test_default_decision(self) -> None:
        """Test creating default fallback decision."""
        router = SemanticRouter()

        decision = router._default_decision()

        assert decision.agent_type == AgentType.CHAT  # Default fallback
        assert decision.route_name == "chat"  # Default fallback agent

    def test_hash_based_embedding(self) -> None:
        """Test hash-based embedding fallback."""
        router = SemanticRouter()

        embedding = router._hash_based_embedding("test text")

        assert isinstance(embedding, list)
        assert len(embedding) > 0

        # Same text should produce same embedding
        embedding2 = router._hash_based_embedding("test text")
        assert embedding == embedding2


class TestSemanticRouterInitialization:
    """Test router initialization."""

    @pytest.mark.asyncio
    async def test_initialize_method(self) -> None:
        """Test router initialization."""
        router = SemanticRouter()

        # Should not raise any exceptions
        await router.initialize()

        # Routes should be initialized
        assert router.routes is not None
        assert len(router.routes) > 0
