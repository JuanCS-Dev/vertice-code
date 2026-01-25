"""
Agentic RAG System

Implements adaptive retrieval with multi-agent collaboration.

Pattern (arXiv:2501.09136):
1. Classify query complexity
2. Select retrieval strategy
3. Plan multi-hop retrieval (if complex)
4. Execute with specialized agents
5. Evaluate sufficiency
6. Generate or iterate

Reference:
- Agentic RAG Survey (arXiv:2501.09136)
- MA-RAG: Multi-Agent RAG (arXiv:2505.20096)
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Dict, List
import logging

from .types import (
    AgenticRAGResult,
    CodebaseAgent,
    DocumentationAgent,
    QueryComplexity,
    ResearchResult,
    RetrievalAgent,
    RetrievalPlan,
    RetrievalStep,
    RetrievalStrategy,
    SufficiencyEvaluation,
    WebSearchAgent,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class AgenticRAGMixin:
    """
    Mixin providing Agentic RAG capabilities.

    Add to ResearcherAgent via multiple inheritance.
    """

    _retrieval_agents: Dict[str, RetrievalAgent]

    def _init_retrieval_agents(self) -> None:
        """Initialize specialized retrieval agents."""
        self._retrieval_agents = {
            "docs": DocumentationAgent(),
            "web": WebSearchAgent(),
            "code": CodebaseAgent(),
        }

    async def _generate_answer_llm(
        self,
        query: str,
        results: List[ResearchResult],
    ) -> str:
        """Generate final answer from retrieved results using LLM (Claude 4.5 optimized)."""
        if not results:
            return f"Unable to find information about: {query}"

        # Import router and complexity
        from vertice_core.providers.vertice_router import get_router, TaskComplexity

        router = get_router()

        # Format context for Claude 4.5 Prompt Caching
        # Placing large context at the beginning of the prompt
        context_parts = []
        for i, res in enumerate(results):
            context_parts.append(f"Source {i+1} ({res.title}):\n{res.content or 'No content'}\n")

        context_str = "\n---\n".join(context_parts)

        system_prompt = "You are an expert researcher. Synthesize the following search results into a clear, concise, and accurate answer."

        user_prompt = f"""CONTEXT FOR RESEARCH:
{context_str}

USER QUERY: {query}

Synthesize the context above to answer the query.
Use markdown. Cite sources by their source number [1], [2], etc.
If the context doesn't contain the answer, say so.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            # Use TaskComplexity.COMPLEX to route to Claude 4.5
            answer = await router.generate(
                messages, complexity=TaskComplexity.COMPLEX, max_tokens=4096
            )
            return answer
        except Exception as e:
            logger.error(f"LLM Synthesis failed: {e}. Falling back to basic synthesis.")
            return self._generate_answer_basic(query, results)

    def _generate_answer_basic(
        self,
        query: str,
        results: List[ResearchResult],
    ) -> str:
        """Fallback basic answer generation."""
        answer_parts = [f"Research findings for: {query}\n"]
        for i, result in enumerate(results[:5], 1):
            answer_parts.append(f"\n{i}. {result.title}")
            if result.content:
                answer_parts.append(f"   {result.content[:200]}...")
            if result.url:
                answer_parts.append(f"   Source: {result.url}")
        return "\n".join(answer_parts)

    async def agentic_research(
        self,
        query: str,
        max_iterations: int = 3,
        confidence_threshold: float = 0.7,
    ) -> AgenticRAGResult:
        """
        Perform Agentic RAG research.
        """
        # ... (rest of the method remains similar until answer generation)
        if not hasattr(self, "_retrieval_agents"):
            self._init_retrieval_agents()

        reasoning_trace: List[str] = []
        retrieval_steps: List[RetrievalStep] = []
        all_results: List[ResearchResult] = []

        complexity = self._classify_complexity(query)
        reasoning_trace.append(f"[Classify] Query complexity: {complexity.value}")

        strategy = self._select_strategy(complexity)
        reasoning_trace.append(f"[Strategy] Selected: {strategy.value}")

        if strategy == RetrievalStrategy.DIRECT_ANSWER:
            answer = f"Based on knowledge: {query}"
            return AgenticRAGResult(
                query=query,
                complexity=complexity,
                strategy_used=strategy,
                retrieval_steps=[],
                final_answer=answer,
                confidence=0.9,
                sources=[],
                reasoning_trace=reasoning_trace,
                iterations=0,
            )

        if strategy == RetrievalStrategy.MULTI_HOP:
            plan = self._plan_retrieval(query)
            reasoning_trace.append(f"[Plan] Sub-queries: {plan.sub_queries}")
            sub_queries = plan.sub_queries
        else:
            sub_queries = [query]

        iteration = 0
        confidence = 0.0

        while iteration < max_iterations and confidence < confidence_threshold:
            iteration += 1
            reasoning_trace.append(f"[Iteration {iteration}] Starting retrieval")

            for sub_query in sub_queries:
                agents_to_use = self._route_query(sub_query)

                for agent_name in agents_to_use:
                    agent = self._retrieval_agents.get(agent_name)
                    if agent:
                        results = await agent.retrieve(sub_query)
                        all_results.extend(results)

                        step = RetrievalStep(
                            query=sub_query,
                            source=agent_name,
                            results=results,
                            relevance_assessment=self._assess_relevance(results, sub_query),
                            needs_more=len(results) == 0,
                        )
                        retrieval_steps.append(step)
                        reasoning_trace.append(f"[Retrieve] {agent_name}: {len(results)} results")

            evaluation = self._evaluate_sufficiency(query, all_results)
            confidence = evaluation.confidence
            reasoning_trace.append(
                f"[Evaluate] Sufficient: {evaluation.sufficient}, Confidence: {confidence:.2f}"
            )

            if evaluation.sufficient:
                break

            if evaluation.recommendation == "refine_query":
                sub_queries = [self._refine_query(query, evaluation.missing_aspects)]
                reasoning_trace.append(f"[Refine] New query: {sub_queries[0]}")

        # Use the new LLM-based synthesis (Claude 4.5 optimized)
        answer = await self._generate_answer_llm(query, all_results)
        sources = list(set(r.url for r in all_results if r.url))

        return AgenticRAGResult(
            query=query,
            complexity=complexity,
            strategy_used=strategy,
            retrieval_steps=retrieval_steps,
            final_answer=answer,
            confidence=confidence,
            sources=sources,
            reasoning_trace=reasoning_trace,
            iterations=iteration,
        )
        """Classify query complexity for adaptive retrieval."""
        query_lower = query.lower()

        simple_patterns = [
            r"^what is\b",
            r"^define\b",
            r"^who is\b",
            r"^when (was|did)\b",
        ]
        for pattern in simple_patterns:
            if re.match(pattern, query_lower):
                return QueryComplexity.SIMPLE

        complex_patterns = [
            r"\bcompare\b",
            r"\bvs\.?\b",
            r"\banalyz",
            r"\bhow (does|do|can|should).+and\b",
            r"\brelationship between\b",
            r"\bstep.+by.+step\b",
        ]
        for pattern in complex_patterns:
            if re.search(pattern, query_lower):
                return QueryComplexity.COMPLEX

        words = query.split()
        if len(words) > 15:
            return QueryComplexity.COMPLEX
        elif len(words) < 5:
            return QueryComplexity.SIMPLE

        return QueryComplexity.MODERATE

    def _select_strategy(self, complexity: QueryComplexity) -> RetrievalStrategy:
        """Select retrieval strategy based on complexity."""
        strategy_map = {
            QueryComplexity.SIMPLE: RetrievalStrategy.SINGLE_RETRIEVAL,
            QueryComplexity.MODERATE: RetrievalStrategy.SINGLE_RETRIEVAL,
            QueryComplexity.COMPLEX: RetrievalStrategy.MULTI_HOP,
        }
        return strategy_map.get(complexity, RetrievalStrategy.SINGLE_RETRIEVAL)

    def _plan_retrieval(self, query: str) -> RetrievalPlan:
        """Plan multi-hop retrieval by decomposing query."""
        sub_queries = []

        if " and " in query.lower():
            parts = query.lower().split(" and ")
            sub_queries.extend([p.strip() for p in parts if len(p.strip()) > 3])

        if " vs " in query.lower() or " versus " in query.lower():
            parts = re.split(r"\s+vs\.?\s+|\s+versus\s+", query, flags=re.IGNORECASE)
            for part in parts:
                if len(part.strip()) > 3:
                    sub_queries.append(f"What is {part.strip()}?")

        if not sub_queries:
            sub_queries = [query]

        sources = ["docs", "web"]
        if any(word in query.lower() for word in ["code", "function", "class", "method"]):
            sources.append("code")

        return RetrievalPlan(
            original_query=query,
            sub_queries=sub_queries,
            sources_to_check=sources,
            estimated_hops=len(sub_queries),
            reasoning=f"Decomposed into {len(sub_queries)} sub-queries",
        )

    def _route_query(self, query: str) -> List[str]:
        """Route query to appropriate retrieval agents."""
        agents = []
        query_lower = query.lower()

        doc_keywords = ["api", "function", "method", "class", "library", "module", "docs"]
        if any(kw in query_lower for kw in doc_keywords):
            agents.append("docs")

        web_keywords = ["latest", "news", "article", "blog", "tutorial", "example"]
        if any(kw in query_lower for kw in web_keywords):
            agents.append("web")

        code_keywords = ["implement", "code", "source", "file", "codebase"]
        if any(kw in query_lower for kw in code_keywords):
            agents.append("code")

        if not agents:
            agents = ["docs", "web"]

        return agents

    def _assess_relevance(
        self,
        results: List[ResearchResult],
        query: str,
    ) -> str:
        """Assess relevance of retrieved results."""
        if not results:
            return "No results found"

        high_relevance = sum(1 for r in results if r.relevance_score > 0.7)
        if high_relevance >= len(results) * 0.5:
            return "High relevance"
        elif high_relevance > 0:
            return "Mixed relevance"
        else:
            return "Low relevance"

    def _evaluate_sufficiency(
        self,
        query: str,
        results: List[ResearchResult],
    ) -> SufficiencyEvaluation:
        """Evaluate if we have sufficient information."""
        if not results:
            return SufficiencyEvaluation(
                sufficient=False,
                confidence=0.0,
                missing_aspects=["No information retrieved"],
                recommendation="retrieve_more",
            )

        avg_relevance = sum(r.relevance_score for r in results) / len(results)
        coverage = min(1.0, len(results) / 5)
        confidence = avg_relevance * 0.6 + coverage * 0.4

        missing = []
        if confidence < 0.5:
            missing.append("Low relevance scores")
        if len(results) < 2:
            missing.append("Insufficient sources")

        sufficient = confidence >= 0.7 and not missing

        if not sufficient:
            recommendation = "retrieve_more" if confidence < 0.3 else "refine_query"
        else:
            recommendation = "generate"

        return SufficiencyEvaluation(
            sufficient=sufficient,
            confidence=confidence,
            missing_aspects=missing,
            recommendation=recommendation,
        )

    def _refine_query(self, original: str, missing: List[str]) -> str:
        """Refine query based on missing aspects."""
        refined = original
        if "specific" in " ".join(missing).lower():
            refined = f"detailed {original}"
        return refined

    def _generate_answer(
        self,
        query: str,
        results: List[ResearchResult],
    ) -> str:
        """Generate final answer from retrieved results."""
        if not results:
            return f"Unable to find information about: {query}"

        answer_parts = [f"Research findings for: {query}\n"]

        for i, result in enumerate(results[:5], 1):
            answer_parts.append(f"\n{i}. {result.title}")
            if result.content:
                answer_parts.append(f"   {result.content[:200]}...")
            if result.url:
                answer_parts.append(f"   Source: {result.url}")

        return "\n".join(answer_parts)

    async def quick_lookup(self, query: str) -> AgenticRAGResult:
        """Quick single-hop lookup for simple queries."""
        return await self.agentic_research(
            query,
            max_iterations=1,
            confidence_threshold=0.5,
        )
