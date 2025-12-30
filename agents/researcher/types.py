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
        """Search documentation sources."""
        return []


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
        """Search the web."""
        return []


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
        """Search the codebase."""
        return []
