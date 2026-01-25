"""
Agentic RAG V2 - Simplified with Direct Tools

Uses tools directly instead of sub-agents, following Google ADK 2026 pattern.
Same output format as V1 for backward compatibility.

Changes from V1:
- No sub-agent classes (DocumentationAgent, WebSearchAgent, CodebaseAgent)
- Direct tool calls (WebSearchTool, grep, file read)
- Simpler code, fewer abstractions

Reference:
- Google ADK 2026: "Use tools, not sub-agents for simple retrieval"
- Agentic RAG Survey (arXiv:2501.09136)
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List
import logging

from .types import (
    AgenticRAGResult,
    QueryComplexity,
    ResearchResult,
    RetrievalPlan,
    RetrievalStep,
    RetrievalStrategy,
    SufficiencyEvaluation,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class AgenticRAGV2Mixin:
    """
    Simplified Agentic RAG using tools directly.
    
    V2 eliminates sub-agent classes in favor of direct tool calls.
    This reduces abstraction layers and improves maintainability.
    """

    async def agentic_research(
        self,
        query: str,
        max_iterations: int = 3,
        confidence_threshold: float = 0.7,
    ) -> AgenticRAGResult:
        """
        Perform Agentic RAG research using direct tools.
        """
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
                tools_to_use = self._route_query(sub_query)

                for tool_name in tools_to_use:
                    # Direct tool calls instead of sub-agents
                    results = await self._call_tool(tool_name, sub_query)
                    all_results.extend(results)

                    step = RetrievalStep(
                        query=sub_query,
                        source=tool_name,
                        results=results,
                        relevance_assessment=self._assess_relevance(results, sub_query),
                        needs_more=len(results) == 0,
                    )
                    retrieval_steps.append(step)
                    reasoning_trace.append(f"[Tool:{tool_name}] {len(results)} results")

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

        # Generate answer
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

    async def _call_tool(self, tool_name: str, query: str) -> List[ResearchResult]:
        """
        Call retrieval tool directly.
        
        This replaces sub-agent classes with direct tool calls.
        """
        if tool_name == "docs":
            return await self._tool_search_docs(query)
        elif tool_name == "web":
            return await self._tool_search_web(query)
        elif tool_name == "code":
            return await self._tool_search_code(query)
        else:
            logger.warning(f"Unknown tool: {tool_name}")
            return []

    async def _tool_search_docs(self, query: str, limit: int = 5) -> List[ResearchResult]:
        """Search local documentation (direct tool)."""
        results: List[ResearchResult] = []
        cwd = Path.cwd()
        
        doc_paths = [
            cwd / "docs",
            cwd / "README.md",
            cwd / "CONTRIBUTING.md",
        ]
        
        query_lower = query.lower()
        
        for doc_path in doc_paths:
            if not doc_path.exists():
                continue
                
            try:
                if doc_path.is_file():
                    content = doc_path.read_text(encoding="utf-8", errors="ignore")
                    if any(term in content.lower() for term in query_lower.split()):
                        results.append(
                            ResearchResult(
                                source=str(doc_path.relative_to(cwd)),
                                title=doc_path.name,
                                content=content[:500],
                                relevance_score=0.7,
                                metadata={"type": "local_doc", "tool": "docs_v2"},
                            )
                        )
                elif doc_path.is_dir():
                    for md_file in doc_path.glob("**/*.md"):
                        try:
                            content = md_file.read_text(encoding="utf-8", errors="ignore")
                            if any(term in content.lower() for term in query_lower.split()):
                                relevant_lines = [
                                    line.strip()
                                    for line in content.split("\n")
                                    if any(term in line.lower() for term in query_lower.split())
                                ][:5]
                                
                                results.append(
                                    ResearchResult(
                                        source=str(md_file.relative_to(cwd)),
                                        title=md_file.name,
                                        content="\n".join(relevant_lines) or content[:500],
                                        relevance_score=0.7,
                                        metadata={"type": "local_doc", "tool": "docs_v2"},
                                    )
                                )
                        except (IOError, UnicodeDecodeError):
                            continue
            except (IOError, PermissionError):
                continue
                
        return results[:limit]

    async def _tool_search_web(self, query: str, limit: int = 5) -> List[ResearchResult]:
        """Search web using WebSearchTool directly."""
        results: List[ResearchResult] = []
        
        try:
            from vertice_core.tools.web_search import WebSearchTool
            
            web_tool = WebSearchTool()
            search_result = await web_tool._execute_validated(
                query=query,
                max_results=limit,
                time_range=None,
            )
            
            if search_result.success and search_result.data:
                for item in search_result.data:
                    results.append(
                        ResearchResult(
                            source=item.get("source", "web"),
                            title=item.get("title", "Untitled"),
                            content=item.get("snippet", ""),
                            url=item.get("url"),
                            relevance_score=0.8,
                            metadata={"tool": "web_v2", "engine": "duckduckgo"},
                        )
                    )
            else:
                logger.warning(f"Web search failed: {search_result.error}")
                
        except Exception as e:
            logger.error(f"Web search tool error: {e}")
            
        return results[:limit]

    async def _tool_search_code(self, query: str, limit: int = 5) -> List[ResearchResult]:
        """Search codebase using grep directly."""
        results: List[ResearchResult] = []
        cwd = Path.cwd()
        
        try:
            proc = subprocess.run(
                ["grep", "-r", "-l", "-i", query, ".", "--include=*.py"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=cwd,
            )
            
            files = [f for f in proc.stdout.strip().split("\n") if f][:limit]
            
            for file_path in files:
                try:
                    full_path = cwd / file_path
                    content = full_path.read_text(encoding="utf-8", errors="ignore")
                    
                    lines = content.split("\n")
                    matching = [
                        f"L{i + 1}: {line.strip()}"
                        for i, line in enumerate(lines)
                        if query.lower() in line.lower()
                    ][:5]
                    
                    results.append(
                        ResearchResult(
                            source=file_path,
                            title=Path(file_path).name,
                            content="\n".join(matching),
                            relevance_score=0.9,
                            metadata={"type": "codebase", "tool": "code_v2"},
                        )
                    )
                except (IOError, UnicodeDecodeError):
                    continue
                    
        except subprocess.TimeoutExpired:
            logger.warning("Code search timed out")
        except FileNotFoundError:
            logger.warning("grep not available")
            
        return results[:limit]

    async def _generate_answer_llm(
        self,
        query: str,
        results: List[ResearchResult],
    ) -> str:
        """Generate final answer using LLM."""
        if not results:
            return f"Unable to find information about: {query}"

        try:
            from vertice_core.providers.vertice_router import get_router, TaskComplexity

            router = get_router()

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

            answer = await router.generate(
                messages, complexity=TaskComplexity.COMPLEX, max_tokens=4096
            )
            return answer
            
        except Exception as e:
            logger.error(f"LLM Synthesis failed: {e}")
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

    def _classify_complexity(self, query: str) -> QueryComplexity:
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
        """Route query to appropriate tools."""
        tools = []
        query_lower = query.lower()

        doc_keywords = ["api", "function", "method", "class", "library", "module", "docs"]
        if any(kw in query_lower for kw in doc_keywords):
            tools.append("docs")

        web_keywords = ["latest", "news", "article", "blog", "tutorial", "example"]
        if any(kw in query_lower for kw in web_keywords):
            tools.append("web")

        code_keywords = ["implement", "code", "source", "file", "codebase"]
        if any(kw in query_lower for kw in code_keywords):
            tools.append("code")

        if not tools:
            tools = ["docs", "web"]

        return tools

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

    async def quick_lookup(self, query: str) -> AgenticRAGResult:
        """Quick single-hop lookup for simple queries."""
        return await self.agentic_research(
            query,
            max_iterations=1,
            confidence_threshold=0.5,
        )
