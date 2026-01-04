"""
Researcher Agent Types

Dataclasses and types for Researcher Agent.
Includes Agentic RAG types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class QueryComplexity(str, Enum):
    """Query complexity levels for adaptive retrieval."""
    SIMPLE = "simple"       # Direct answer, no retrieval needed
    MODERATE = "moderate"   # Single-step retrieval
    COMPLEX = "complex"     # Multi-hop reasoning required


class RetrievalStrategy(str, Enum):
    """Retrieval strategies based on complexity."""
    DIRECT_ANSWER = "direct"           # No retrieval, use knowledge
    SINGLE_RETRIEVAL = "single"        # One retrieval pass
    MULTI_HOP = "multi_hop"            # Iterative retrieval
    CORRECTIVE = "corrective"          # Retrieve + verify + correct


@dataclass
class ResearchResult:
    """A single research finding."""
    source: str
    title: str
    content: str
    url: Optional[str] = None
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchReport:
    """Complete research report."""
    query: str
    summary: str
    findings: List[ResearchResult]
    sources: List[str]
    confidence: float  # 0-1


# =============================================================================
# AGENTIC RAG TYPES
# =============================================================================

@dataclass
class RetrievalPlan:
    """
    Plan for multi-hop retrieval.

    Based on Agentic RAG planning pattern: decompose query
    into retrievable sub-questions.
    """
    original_query: str
    sub_queries: List[str]
    sources_to_check: List[str]
    estimated_hops: int
    reasoning: str


@dataclass
class RetrievalStep:
    """A single step in the retrieval process."""
    query: str
    source: str
    results: List[ResearchResult]
    relevance_assessment: str
    needs_more: bool


@dataclass
class SufficiencyEvaluation:
    """
    Evaluation of whether we have enough information.

    Core Agentic RAG pattern: decide when to stop retrieving.
    """
    sufficient: bool
    confidence: float
    missing_aspects: List[str]
    recommendation: str  # "generate", "retrieve_more", "refine_query"


@dataclass
class AgenticRAGResult:
    """Complete result from Agentic RAG process."""
    query: str
    complexity: QueryComplexity
    strategy_used: RetrievalStrategy
    retrieval_steps: List[RetrievalStep]
    final_answer: str
    confidence: float
    sources: List[str]
    reasoning_trace: List[str]
    iterations: int


# =============================================================================
# RETRIEVAL AGENTS
# =============================================================================

class RetrievalAgent(ABC):
    """
    Base class for specialized retrieval agents.

    Implements multi-agent RAG pattern with different
    agents for different data sources.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name."""
        pass

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Type of source this agent handles."""
        pass

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        limit: int = 5,
    ) -> List[ResearchResult]:
        """Retrieve results for query."""
        pass


class DocumentationAgent(RetrievalAgent):
    """Agent specialized for documentation retrieval."""

    @property
    def name(self) -> str:
        return "documentation"

    @property
    def source_type(self) -> str:
        return "docs"

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
    ) -> List[ResearchResult]:
        """
        Search documentation sources.

        Searches local docs/ directory and README files.
        """
        import asyncio
        from pathlib import Path

        results: List[ResearchResult] = []
        cwd = Path.cwd()

        # Search in docs/ directory
        docs_dir = cwd / "docs"
        readme_files = list(cwd.glob("**/README*.md"))[:limit]
        doc_files = list(docs_dir.glob("**/*.md"))[:limit] if docs_dir.exists() else []

        all_files = (readme_files + doc_files)[:limit]

        for doc_path in all_files:
            try:
                content = doc_path.read_text(encoding="utf-8", errors="ignore")
                query_lower = query.lower()

                # Simple relevance: check if query terms appear
                if any(term in content.lower() for term in query_lower.split()):
                    # Extract relevant snippet
                    lines = content.split("\n")
                    relevant_lines = [
                        line for line in lines
                        if any(term in line.lower() for term in query_lower.split())
                    ][:5]

                    results.append(ResearchResult(
                        source=str(doc_path.relative_to(cwd)),
                        title=doc_path.name,
                        content="\n".join(relevant_lines) or content[:500],
                        relevance_score=0.7,
                        metadata={"type": "local_doc"},
                    ))
            except (FileNotFoundError, PermissionError, IOError, UnicodeDecodeError):
                continue

        return results[:limit]


class WebSearchAgent(RetrievalAgent):
    """Agent specialized for web search."""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def source_type(self) -> str:
        return "web"

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
    ) -> List[ResearchResult]:
        """
        Search the web using httpx.

        Uses DuckDuckGo HTML search as fallback.
        """
        import httpx

        results: List[ResearchResult] = []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # DuckDuckGo HTML search (no API key needed)
                url = "https://html.duckduckgo.com/html/"
                response = await client.post(url, data={"q": query})

                if response.status_code == 200:
                    # Parse results (basic extraction)
                    html = response.text
                    # Extract result snippets (simplified)
                    import re
                    snippets = re.findall(
                        r'<a class="result__a"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>',
                        html
                    )

                    for i, (href, title) in enumerate(snippets[:limit]):
                        results.append(ResearchResult(
                            source="duckduckgo",
                            title=title.strip(),
                            content=f"Web result for: {query}",
                            url=href,
                            relevance_score=0.8 - (i * 0.1),
                            metadata={"type": "web_search"},
                        ))
        except (httpx.HTTPError, ConnectionError, TimeoutError):
            pass

        return results[:limit]


class CodebaseAgent(RetrievalAgent):
    """Agent specialized for codebase search."""

    @property
    def name(self) -> str:
        return "codebase"

    @property
    def source_type(self) -> str:
        return "code"

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
    ) -> List[ResearchResult]:
        """
        Search the codebase using grep.

        Searches Python files for query terms.
        """
        import subprocess
        from pathlib import Path

        results: List[ResearchResult] = []
        cwd = Path.cwd()

        try:
            # Use grep to find matching files
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

                    # Extract matching lines
                    lines = content.split("\n")
                    matching = [
                        f"L{i+1}: {line.strip()}"
                        for i, line in enumerate(lines)
                        if query.lower() in line.lower()
                    ][:5]

                    results.append(ResearchResult(
                        source=file_path,
                        title=Path(file_path).name,
                        content="\n".join(matching),
                        relevance_score=0.9,
                        metadata={"type": "codebase", "language": "python"},
                    ))
                except (FileNotFoundError, PermissionError, IOError, UnicodeDecodeError):
                    continue

        except subprocess.TimeoutExpired:
            pass
        except FileNotFoundError:
            # grep not available
            pass

        return results[:limit]
