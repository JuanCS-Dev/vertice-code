"""
Semantic Router - Core routing logic using embeddings + LLM fallback.
"""

import asyncio
import hashlib
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from .cache import RouterCacheMixin
from .similarity import SimilarityEngine
from .stats import RouterStatsMixin
from .types import AgentType, RouteDefinition, RoutingDecision, TaskComplexity

logger = logging.getLogger(__name__)


class SemanticRouter(RouterCacheMixin, RouterStatsMixin):
    """
    Intelligent request router using embeddings + LLM fallback.

    Strategy:
    1. Embed user request
    2. Compare against pre-computed route embeddings
    3. If confidence > threshold: return fast path result
    4. If confidence < threshold: use LLM for classification

    Usage:
        router = SemanticRouter()
        await router.initialize()  # Pre-compute embeddings
        decision = await router.route("implement user login")
    """

    # Confidence thresholds
    HIGH_CONFIDENCE = 0.85  # Fast path
    LOW_CONFIDENCE = 0.60  # Needs LLM fallback
    AMBIGUOUS_THRESHOLD = 0.10  # Gap between top 2 routes

    def __init__(
        self,
        routes: Optional[List[RouteDefinition]] = None,
        embed_func: Optional[Callable[[str], List[float]]] = None,
        llm_classify_func: Optional[Callable[[str, List[str]], str]] = None,
    ):
        """
        Initialize router.

        Args:
            routes: Custom route definitions (defaults to DEFAULT_ROUTES)
            embed_func: Function to generate embeddings
            llm_classify_func: Function for LLM-based classification fallback
        """
        RouterCacheMixin.__init__(self)
        RouterStatsMixin.__init__(self)

        # Load default routes if none provided
        self.routes = routes or self._get_default_routes()
        self._embed_func = embed_func
        self._llm_classify_func = llm_classify_func
        self._initialized = False

        # Route lookup
        self._route_map: Dict[str, RouteDefinition] = {r.name: r for r in self.routes}

        # Pre-computed embeddings
        self._route_embeddings: Dict[str, List[float]] = {}

    async def initialize(self) -> None:
        """Initialize router by pre-computing route embeddings."""
        if self._initialized:
            return

        logger.info(f"Initializing router with {len(self.routes)} routes")

        # Pre-compute embeddings for all routes
        for route in self.routes:
            embedding = await self._get_embedding(route.description)
            if embedding:
                self._route_embeddings[route.name] = embedding

        self._initialized = True
        logger.info("Router initialization complete")

    async def route(self, query: str, context: Optional[Dict[str, Any]] = None) -> RoutingDecision:
        """
        Route a user query to the appropriate agent.

        Args:
            query: User query string
            context: Optional context information

        Returns:
            Routing decision with confidence and reasoning
        """
        start_time = time.time()

        # Check cache first
        cached = self.get_cached_decision(query)
        if cached:
            self.record_route(cached.route_name, cached.confidence, 0, cache_hit=True)
            return cached

        try:
            # Get query embedding
            query_embedding = await self._get_embedding(query)
            if not query_embedding:
                return self._default_decision()

            # Find best matches
            similarities = {}
            for route_name, route_embedding in self._route_embeddings.items():
                similarity = SimilarityEngine.cosine_similarity(query_embedding, route_embedding)
                similarities[route_name] = similarity

            # Sort by similarity
            sorted_routes = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
            best_route, best_score = sorted_routes[0]

            # Check for ambiguous results
            if len(sorted_routes) > 1:
                second_best_score = sorted_routes[1][1]
                if abs(best_score - second_best_score) < self.AMBIGUOUS_THRESHOLD:
                    # Ambiguous, use LLM fallback
                    return await self._llm_fallback(query, sorted_routes[:3], start_time)

            # High confidence - return fast path result
            if best_score >= self.HIGH_CONFIDENCE:
                decision = self._create_decision(
                    best_route, best_score, sorted_routes[1:], "fast_path"
                )
                self.record_route(best_route, best_score, (time.time() - start_time) * 1000)
                self.cache_decision(query, decision)
                return decision

            # Low confidence - use LLM fallback
            if best_score < self.LOW_CONFIDENCE:
                return await self._llm_fallback(query, sorted_routes[:3], start_time)

            # Medium confidence - return with caution
            decision = self._create_decision(
                best_route, best_score, sorted_routes[1:], "medium_confidence"
            )
            self.record_route(best_route, best_score, (time.time() - start_time) * 1000)
            self.cache_decision(query, decision)
            return decision

        except Exception as e:
            logger.error(f"Routing error: {e}")
            self.record_error()
            return self._default_decision()

    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text using configured function."""
        if self._embed_func:
            try:
                return self._embed_func(text)
            except Exception as e:
                logger.warning(f"Embedding function failed: {e}")

        # Fallback to simple hash-based embedding (for testing)
        return self._hash_based_embedding(text)

    def _hash_based_embedding(self, text: str) -> List[float]:
        """Generate simple hash-based embedding for fallback."""
        # Create deterministic "embedding" based on text hash
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()

        # Convert to float list (not a real embedding, just for fallback)
        return [float(b) / 255.0 for b in hash_bytes[:32]]  # 32 dimensions

    def _create_decision(
        self,
        route_name: str,
        confidence: float,
        alternatives: List[tuple],
        reasoning: str,
    ) -> RoutingDecision:
        """Create a routing decision."""
        route_def = self._route_map.get(route_name)
        if not route_def:
            return self._default_decision()

        return RoutingDecision(
            route_name=route_name,
            agent_type=route_def.agent_type,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=[(alt[0], alt[1]) for alt in alternatives],
            complexity=route_def.complexity,
        )

    def _default_decision(self) -> RoutingDecision:
        """Return default routing decision (chat agent)."""
        return RoutingDecision(
            route_name="chat",
            agent_type=AgentType.CHAT,
            confidence=0.5,
            reasoning="Default fallback routing",
            complexity=TaskComplexity.SIMPLE,
        )

    async def _llm_fallback(
        self,
        query: str,
        candidates: List[tuple],
        start_time: float,
    ) -> RoutingDecision:
        """Use LLM for routing when embedding confidence is low."""
        if not self._llm_classify_func:
            # No LLM function, return best candidate
            best_route, best_score = candidates[0]
            decision = self._create_decision(
                best_route, best_score, candidates[1:], "llm_unavailable"
            )
            self.record_route(
                best_route, best_score, (time.time() - start_time) * 1000, fallback_used=True
            )
            return decision

        try:
            # Prepare options for LLM
            route_names = [route for route, _ in candidates]
            route_descriptions = []
            for route_name in route_names:
                route_def = self._route_map.get(route_name)
                if route_def:
                    route_descriptions.append(f"{route_name}: {route_def.description}")

            # Call LLM
            selected_route = self._llm_classify_func(query, route_descriptions)
            if asyncio.iscoroutine(selected_route):
                selected_route = await selected_route

            # Validate response
            if selected_route in route_names:
                confidence = 0.9  # High confidence from LLM
                decision = self._create_decision(selected_route, confidence, [], "llm_fallback")
                self.record_route(
                    selected_route,
                    confidence,
                    (time.time() - start_time) * 1000,
                    fallback_used=True,
                )
                return decision

        except Exception as e:
            logger.warning(f"LLM fallback failed: {e}")

        # LLM failed, return best embedding candidate
        best_route, best_score = candidates[0]
        decision = self._create_decision(best_route, best_score * 0.8, candidates[1:], "llm_failed")
        self.record_route(
            best_route, best_score * 0.8, (time.time() - start_time) * 1000, fallback_used=True
        )
        return decision

    def add_route(self, route: RouteDefinition) -> None:
        """Add a new route definition."""
        self.routes.append(route)
        self._route_map[route.name] = route

        # Pre-compute embedding if initialized
        if self._initialized:
            # Note: This would need async embedding in real implementation
            logger.warning("Adding routes after initialization requires re-initialization")

    def _get_default_routes(self) -> List[RouteDefinition]:
        """Get default routing definitions."""
        return [
            RouteDefinition(
                name="planner",
                agent_type=AgentType.PLANNER,
                description="Task planning, decomposition, and workflow orchestration",
                keywords=["plan", "schedule", "organize", "workflow", "steps"],
                complexity=TaskComplexity.COMPLEX,
            ),
            RouteDefinition(
                name="executor",
                agent_type=AgentType.EXECUTOR,
                description="Code implementation and execution of planned tasks",
                keywords=["implement", "code", "write", "execute", "run"],
                complexity=TaskComplexity.MODERATE,
            ),
            RouteDefinition(
                name="reviewer",
                agent_type=AgentType.REVIEWER,
                description="Code review, quality assurance, and improvement suggestions",
                keywords=["review", "check", "quality", "improve", "feedback"],
                complexity=TaskComplexity.MODERATE,
            ),
            RouteDefinition(
                name="architect",
                agent_type=AgentType.ARCHITECT,
                description="System design, architecture decisions, and technical planning",
                keywords=["design", "architecture", "structure", "system", "technical"],
                complexity=TaskComplexity.COMPLEX,
            ),
            RouteDefinition(
                name="chat",
                agent_type=AgentType.CHAT,
                description="General conversation and assistance",
                keywords=["help", "talk", "chat", "question", "explain"],
                complexity=TaskComplexity.SIMPLE,
            ),
        ]


__all__ = ["SemanticRouter"]
