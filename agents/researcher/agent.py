"""
Vertice Researcher Agent

Documentation and web search specialist with Agentic RAG.

Key Features:
- Documentation lookup
- Web research
- Codebase search
- Agentic RAG (via mixin)

Reference:
- Agentic RAG Survey (arXiv:2501.09136)
- MA-RAG: Multi-Agent RAG (arXiv:2505.20096)
"""

from __future__ import annotations

from typing import Dict, List, Optional, AsyncIterator
import logging

from .types import ResearchReport
from .agentic_rag import AgenticRAGMixin

logger = logging.getLogger(__name__)


class ResearcherAgent(AgenticRAGMixin):
    """
    Research Specialist - The Knowledge Hunter

    Capabilities:
    - Documentation lookup
    - Web research synthesis
    - Codebase semantic search
    - Agentic RAG (via mixin)
    """

    name = "researcher"
    description = """
    Documentation and research specialist with Agentic RAG.
    Uses adaptive retrieval and multi-hop reasoning.
    Always cites sources and provides confidence levels.
    """

    SYSTEM_PROMPT = """You are a research specialist for Vertice Agency.

Your role is to find accurate information quickly:

1. SEARCH thoroughly
   - Official documentation first
   - Reputable sources (MDN, docs, official repos)
   - Recent content (check dates)

2. SYNTHESIZE clearly
   - Summarize key points
   - Extract relevant code examples
   - Note version compatibility

3. CITE always
   - Include source URLs
   - Note publish/update dates
   - Rate source reliability

NEVER guess or make up information.
Say "I couldn't find..." if unsure.
"""

    DOC_SOURCES = {
        "python": "https://docs.python.org/3/",
        "javascript": "https://developer.mozilla.org/",
        "typescript": "https://www.typescriptlang.org/docs/",
        "react": "https://react.dev/",
        "node": "https://nodejs.org/docs/",
        "rust": "https://doc.rust-lang.org/",
        "go": "https://go.dev/doc/",
    }

    def __init__(self, provider: str = "vertex-ai") -> None:
        self._provider_name = provider
        self._llm = None
        self._cache: Dict[str, ResearchReport] = {}

    async def research(
        self,
        query: str,
        context: Optional[str] = None,
        sources: Optional[List[str]] = None,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """
        Research a topic.

        Args:
            query: What to research
            context: Additional context
            sources: Specific sources to check
            stream: Whether to stream output

        Yields:
            Research findings and synthesis
        """
        yield f"[Researcher] Researching: {query}\n"

        if query in self._cache:
            yield "[Researcher] Found in cache\n"
            cached = self._cache[query]
            yield f"\n{cached.summary}\n"
            return

        yield "[Researcher] Searching sources...\n"

        rag_result = await self.agentic_research(query)

        yield "\n## Research Results\n\n"
        yield f"**Complexity**: {rag_result.complexity.value}\n"
        yield f"**Strategy**: {rag_result.strategy_used.value}\n"
        yield f"**Confidence**: {rag_result.confidence:.2f}\n\n"

        yield f"### Answer\n{rag_result.final_answer}\n\n"

        if rag_result.sources:
            yield "### Sources\n"
            for src in rag_result.sources[:5]:
                yield f"- {src}\n"

        yield "\n[Researcher] Research complete\n"

    async def lookup_docs(
        self,
        topic: str,
        language: str,
    ) -> AsyncIterator[str]:
        """
        Look up documentation for a specific language/framework.

        Args:
            topic: What to look up
            language: Programming language or framework
        """
        yield f"[Researcher] Looking up {topic} in {language} docs...\n"

        base_url = self.DOC_SOURCES.get(language.lower())
        if base_url:
            yield f"[Researcher] Primary source: {base_url}\n"

        rag_result = await self.quick_lookup(f"{language} {topic} documentation")

        yield f"\n{rag_result.final_answer}\n"
        yield "[Researcher] Documentation lookup complete\n"

    async def search_codebase(
        self,
        query: str,
        file_patterns: Optional[List[str]] = None,
    ) -> AsyncIterator[str]:
        """
        Search within the current codebase.

        Args:
            query: What to search for
            file_patterns: File patterns to search (e.g., ["*.py", "*.ts"])
        """
        yield f"[Researcher] Searching codebase for: {query}\n"

        patterns = file_patterns or ["*"]
        yield f"[Researcher] Patterns: {', '.join(patterns)}\n"

        rag_result = await self.quick_lookup(f"codebase {query}")

        yield f"\n{rag_result.final_answer}\n"
        yield "[Researcher] Codebase search complete\n"

    async def summarize(
        self,
        content: str,
        max_length: int = 500,
    ) -> str:
        """
        Summarize content.

        Args:
            content: Text to summarize
            max_length: Maximum summary length

        Returns:
            Summarized text
        """
        if len(content) <= max_length:
            return content
        return content[:max_length] + "..."

    def get_status(self) -> Dict:
        """Get agent status."""
        return {
            "name": self.name,
            "provider": self._provider_name,
            "cached_queries": len(self._cache),
            "agentic_rag_enabled": True,
        }


# Singleton instance
researcher = ResearcherAgent()
