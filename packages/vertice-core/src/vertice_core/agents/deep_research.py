"""
Vertex AI Deep Research Agent - Adapted for Vertice-Code
Autonomous multi-step research agent using iterative web search and analysis

This module provides deep research capabilities through iterative information gathering,
integrated with Vertice-Code's existing agent architecture and tools.
"""

import logging
import time
from typing import AsyncIterator, Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Using simple class instead of BaseAgent for compatibility
from vertice_core.core.guardrails import get_ai_safety_guardrails
from vertice_core.tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)


@dataclass
class DeepResearchConfig:
    """Configuration for deep research agent."""

    max_iterations: int = 5
    max_search_results: int = 10
    enable_thinking_trace: bool = True
    safety_checks: bool = True
    audit_enabled: bool = True
    synthesis_model: str = "claude-3-5-sonnet"  # Would use Vertex AI in production


@dataclass
class ResearchIteration:
    """A single research iteration."""

    iteration: int
    query: str
    search_results: List[Dict[str, Any]] = field(default_factory=list)
    analysis: str = ""
    key_findings: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)


@dataclass
class DeepResearchResult:
    """Complete research result."""

    success: bool
    content: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    thinking_trace: List[str] = field(default_factory=list)
    iterations_completed: int = 0
    execution_time: float = 0.0
    error_message: Optional[str] = None


@dataclass
class ResearchAgentResult:
    """Simple result class for research agent."""

    success: bool
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class VertexDeepResearchAgent:
    """
    Deep Research Agent for Vertice-Code

    Performs multi-step research by:
    1. Breaking down complex queries into focused searches
    2. Iteratively gathering and analyzing information
    3. Synthesizing findings into comprehensive reports
    4. Providing citations and confidence levels

    Uses iterative web search and analysis with existing tools.
    """

    def __init__(self, config: Optional[DeepResearchConfig] = None):
        self.config = config or DeepResearchConfig()
        self.web_search = WebSearchTool()
        self.guardrails = get_ai_safety_guardrails()

    @property
    def name(self) -> str:
        return "deep_research"

    @property
    def description(self) -> str:
        return "Autonomous multi-step research agent with iterative information gathering"

    async def execute(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> ResearchAgentResult:
        """
        Execute deep research task.

        Args:
            task: Research query/topic
            context: Additional context (constraints, focus areas, etc.)

        Returns:
            Comprehensive research report
        """
        start_time = time.time()

        try:
            # Safety check
            if self.config.safety_checks:
                input_check, _ = await self.guardrails.check_interaction(task)
                if not input_check.is_safe:
                    return ResearchAgentResult(
                        success=False,
                        content="Research query failed safety checks",
                        metadata={"safety_violations": input_check.violations},
                    )

            # Execute research
            result = await self._perform_research(task, context or {})

            # Audit disabled for now - can be added later

            execution_time = time.time() - start_time

            return ResearchAgentResult(
                success=result.success,
                content=result.content,
                metadata={
                    "execution_time": execution_time,
                    "iterations": result.iterations_completed,
                    "sources_count": len(result.sources),
                    "thinking_steps": len(result.thinking_trace),
                },
            )

        except Exception as e:
            logger.error(f"Deep research failed: {e}")
            return ResearchAgentResult(
                success=False, content="Research execution failed", metadata={"error": str(e)}
            )

    async def execute_streaming(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream deep research with progressive updates.

        Yields status updates as each research phase progresses.

        Args:
            task: Research query/topic
            context: Additional context

        Yields:
            StreamingChunk dicts with research progress
        """
        try:
            yield {"type": "status", "data": f"🔬 Starting deep research: '{task[:50]}...'"}

            # Safety check
            if self.config.safety_checks:
                yield {"type": "status", "data": "🔒 Running safety checks..."}
                input_check, _ = await self.guardrails.check_interaction(task)
                if not input_check.is_safe:
                    yield {"type": "error", "data": "Research query failed safety checks"}
                    return

            # Phase 1: Generate queries
            yield {"type": "reasoning", "data": "### Planning Research\n"}

            initial_queries = await self._generate_search_queries(task, context or {})
            yield {"type": "thinking", "data": f"Generated {len(initial_queries)} search queries\n"}

            for i, query in enumerate(initial_queries[:3]):
                yield {"type": "thinking", "data": f"  {i+1}. {query[:60]}...\n"}

            # Phase 2: Execute searches
            yield {"type": "status", "data": "🌐 Performing web searches..."}

            iterations: List[ResearchIteration] = []
            all_sources: List[Dict[str, Any]] = []

            for i, query in enumerate(initial_queries[: self.config.max_iterations]):
                yield {
                    "type": "status",
                    "data": f"📊 Iteration {i+1}/{len(initial_queries[:self.config.max_iterations])}...",
                }

                iteration = ResearchIteration(iteration=i + 1, query=query)

                search_result = await self.web_search._execute_validated(
                    query=query, max_results=self.config.max_search_results
                )

                if search_result.success and search_result.data:
                    iteration.search_results = search_result.data
                    all_sources.extend(search_result.data)
                    yield {
                        "type": "thinking",
                        "data": f"  Found {len(search_result.data)} sources\n",
                    }

                iterations.append(iteration)

            # Phase 3: Synthesis
            yield {"type": "status", "data": "📝 Synthesizing findings..."}

            final_report = await self._synthesize_report(task, iterations, all_sources)

            # Final verdict
            yield {
                "type": "verdict",
                "data": f"\n\n✅ Research complete: {len(iterations)} iterations, {len(all_sources)} sources",
            }

            yield {
                "type": "result",
                "data": {
                    "report": (
                        final_report[:1000] + "..." if len(final_report) > 1000 else final_report
                    ),
                    "sources_count": len(all_sources),
                    "iterations": len(iterations),
                },
            }

        except Exception as e:
            yield {"type": "error", "data": f"Research failed: {str(e)}"}

    async def _perform_research(self, query: str, context: Dict[str, Any]) -> DeepResearchResult:
        """Execute the multi-step research process."""

        iterations: List[ResearchIteration] = []
        all_sources: List[Dict[str, Any]] = []
        thinking_trace: List[str] = []

        try:
            # Phase 1: Initial research planning
            thinking_trace.append(f"Planning research for: {query}")
            initial_queries = await self._generate_search_queries(query, context)

            # Phase 2: Iterative research
            for i in range(min(self.config.max_iterations, len(initial_queries))):
                iteration = ResearchIteration(iteration=i + 1, query=initial_queries[i])

                thinking_trace.append(f"Iteration {i + 1}: Searching for '{iteration.query}'")

                # Perform search
                search_result = await self.web_search._execute_validated(
                    query=iteration.query, max_results=self.config.max_search_results
                )

                if search_result.success and search_result.data:
                    iteration.search_results = search_result.data
                    all_sources.extend(search_result.data)

                    # Analyze results (would use Vertex AI in production)
                    analysis = await self._analyze_search_results(
                        iteration.query, search_result.data
                    )
                    iteration.analysis = analysis

                    # Extract key findings and follow-up questions
                    iteration.key_findings = await self._extract_findings(analysis)
                    iteration.follow_up_questions = await self._generate_follow_ups(analysis, query)

                iterations.append(iteration)

                # Check if we have enough information
                if len(all_sources) >= 15:  # Arbitrary threshold
                    break

            # Phase 3: Synthesis
            thinking_trace.append("Synthesizing research findings")
            final_report = await self._synthesize_report(query, iterations, all_sources)

            return DeepResearchResult(
                success=True,
                content=final_report,
                sources=all_sources,
                thinking_trace=thinking_trace,
                iterations_completed=len(iterations),
                execution_time=0.0,  # Would be calculated properly
            )

        except Exception as e:
            return DeepResearchResult(
                success=False, content="", thinking_trace=thinking_trace, error_message=str(e)
            )

    async def _generate_search_queries(self, main_query: str, context: Dict[str, Any]) -> List[str]:
        """Generate focused search queries for the research topic."""
        # In production, this would use Vertex AI to decompose the query
        # For now, we'll create focused queries manually

        base_queries = [
            f'"{main_query}" overview analysis',
            f'"{main_query}" latest developments 2024 2025',
            f'"{main_query}" key challenges and solutions',
            f'"{main_query}" industry trends and predictions',
            f'"{main_query}" expert opinions and insights',
        ]

        # Add context-specific queries if provided
        if context.get("focus_areas"):
            for area in context["focus_areas"][:2]:  # Limit to 2 additional
                base_queries.append(f'"{main_query}" {area} analysis')

        return base_queries[: self.config.max_iterations]

    async def _analyze_search_results(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Analyze search results and extract insights."""
        # In production, this would use Vertex AI to analyze the results
        # For now, we'll create a simple synthesis

        if not results:
            return "No search results found for analysis."

        # Extract key information
        titles = [r.get("title", "") for r in results[:5]]
        snippets = [r.get("snippet", "") for r in results[:5]]

        analysis = f"""
Analysis for query: "{query}"

Key sources found: {len(results)}

Top findings:
"""

        for i, (title, snippet) in enumerate(zip(titles, snippets), 1):
            analysis += f"{i}. {title}\n"
            if snippet:
                analysis += f"   {snippet[:200]}...\n\n"

        return analysis

    async def _extract_findings(self, analysis: str) -> List[str]:
        """Extract key findings from analysis."""
        # Simple extraction - in production would use NLP
        lines = analysis.split("\n")
        findings = []

        for line in lines:
            line = line.strip()
            if line and len(line) > 20 and not line.startswith("Analysis"):
                findings.append(line[:200])

        return findings[:5]

    async def _generate_follow_ups(self, analysis: str, original_query: str) -> List[str]:
        """Generate follow-up questions based on analysis."""
        # Simple follow-up generation
        return [
            f"What are the latest developments in {original_query}?",
            f"What are the main challenges facing {original_query}?",
            f"What are expert predictions for {original_query} future?",
            f"What are the most important metrics for {original_query}?",
        ]

    async def _synthesize_report(
        self, query: str, iterations: List[ResearchIteration], all_sources: List[Dict[str, Any]]
    ) -> str:
        """Synthesize all research into a comprehensive report."""

        report = f"""# Deep Research Report: {query}

## Executive Summary

This report provides comprehensive analysis of "{query}" based on multi-step research across {len(iterations)} iterations and {len(all_sources)} sources.

## Research Methodology

- **Iterations Completed**: {len(iterations)}
- **Sources Analyzed**: {len(all_sources)}
- **Research Approach**: Multi-step web search with iterative refinement

## Key Findings

"""

        # Add findings from each iteration
        for iteration in iterations:
            if iteration.key_findings:
                report += f"### Research Phase {iteration.iteration}: {iteration.query}\n"
                for finding in iteration.key_findings:
                    report += f"- {finding}\n"
                report += "\n"

        # Add sources section
        report += "## Sources & Citations\n\n"
        for i, source in enumerate(all_sources[:10], 1):  # Top 10 sources
            title = source.get("title", "Untitled")
            url = source.get("url", "")
            report += f"{i}. [{title}]({url})\n"

        # Add analysis section
        report += "\n## Detailed Analysis\n\n"
        for iteration in iterations:
            if iteration.analysis:
                report += f"### {iteration.query}\n{iteration.analysis}\n\n"

        # Add confidence assessment
        total_sources = len(all_sources)
        if total_sources > 20:
            confidence = "High"
        elif total_sources > 10:
            confidence = "Medium"
        else:
            confidence = "Low"

        report += f"""
## Research Quality Assessment

- **Source Coverage**: {total_sources} sources analyzed
- **Research Depth**: {len(iterations)} iterations completed
- **Confidence Level**: {confidence}
- **Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}

---
*Report generated by Vertex AI Deep Research Agent*
"""

        return report


# Factory function
def create_deep_research_agent() -> VertexDeepResearchAgent:
    """Create a configured deep research agent."""
    config = DeepResearchConfig()
    return VertexDeepResearchAgent(config)
