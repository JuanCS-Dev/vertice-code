"""
Vertice Architect Agent

System design and architecture specialist with Three Loops framework.

Key Features:
- System architecture design
- Component diagrams
- Trade-off analysis
- Three Loops human-AI collaboration (via mixin)

Reference:
- https://www.infoq.com/articles/architects-ai-era/
"""

from __future__ import annotations

from typing import Dict, List, Optional, AsyncIterator
import logging

from .types import (
    DesignLevel,
    DesignProposal,
    ArchitectureReview,
)
from .autonomy_compat import ThreeLoopsMixin  # Deprecated, uses BoundedAutonomy internally
from agents.base import BaseAgent

logger = logging.getLogger(__name__)


class ArchitectAgent(ThreeLoopsMixin, BaseAgent):
    """
    Architecture Specialist - The System Designer

    Capabilities:
    - System architecture design
    - Service decomposition
    - Component diagrams
    - Trade-off analysis
    - Three Loops pattern (via mixin)
    """

    name = "architect"
    description = """
    System design and architecture specialist.
    Uses Three Loops for human-AI collaboration.
    Provides clear trade-off analysis for decisions.
    """

    SYSTEM_PROMPT = """You are a senior architect for Vertice Agency.

Your role is to design robust, scalable systems:

1. ANALYZE requirements
   - Functional requirements
   - Non-functional requirements (scale, performance, security)
   - Constraints and limitations

2. DESIGN solutions
   - Multiple options with trade-offs
   - Diagrams (Mermaid format)
   - Component interactions

3. DOCUMENT clearly
   - Architecture Decision Records (ADRs)
   - Sequence diagrams
   - Deployment diagrams

Always consider:
- Scalability (horizontal/vertical)
- Reliability (fault tolerance)
- Security (defense in depth)
- Maintainability (modularity)
"""

    def __init__(self, provider: str = "claude") -> None:
        super().__init__()  # Initialize BaseAgent (observability)
        self._provider_name = provider
        self._llm = None
        self._proposals: Dict[str, DesignProposal] = {}

    async def design(
        self,
        requirements: str,
        level: DesignLevel = DesignLevel.SERVICE,
        constraints: Optional[List[str]] = None,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """
        Design architecture based on requirements.

        Args:
            requirements: What to design
            level: Abstraction level
            constraints: Design constraints
            stream: Whether to stream output

        Yields:
            Design proposal and diagrams
        """
        yield f"[Architect] Analyzing requirements for {level.value} design...\n"

        context = self.classify_decision(requirements)
        loop_rec = self.select_loop(context)

        yield f"[Architect] Loop: {loop_rec.recommended_loop.value} "
        yield f"(confidence: {loop_rec.confidence:.2f})\n"
        yield f"[Architect] Reasoning: {loop_rec.reasoning}\n\n"

        yield "## Architecture Proposal\n\n"

        if constraints:
            yield "### Constraints\n"
            for c in constraints:
                yield f"- {c}\n"
            yield "\n"

        yield "### Components\n"
        yield "- Component A: Handles user requests\n"
        yield "- Component B: Business logic processing\n"
        yield "- Component C: Data persistence\n\n"

        yield "### Diagram\n"
        yield "```mermaid\n"
        yield "graph TD\n"
        yield "    A[Client] --> B[API Gateway]\n"
        yield "    B --> C[Service]\n"
        yield "    C --> D[Database]\n"
        yield "```\n\n"

        yield "### Trade-offs\n"
        yield "| Aspect | Pro | Con |\n"
        yield "|--------|-----|-----|\n"
        yield "| Simplicity | Easy to understand | Limited scalability |\n"
        yield "| Flexibility | Can evolve | More complexity |\n\n"

        yield f"### Guardrails ({loop_rec.recommended_loop.value})\n"
        for g in loop_rec.guardrails:
            yield f"- {g}\n"

        yield "\n[Architect] Design complete\n"

    async def review(
        self,
        proposal: DesignProposal,
    ) -> ArchitectureReview:
        """
        Review an architecture proposal.

        Args:
            proposal: Proposal to review

        Returns:
            ArchitectureReview with assessment
        """
        strengths = []
        concerns = []
        recommendations = []

        if len(proposal.components) >= 2:
            strengths.append("Good separation of concerns")
        else:
            concerns.append("Consider breaking down into smaller components")

        if proposal.trade_offs:
            strengths.append("Trade-offs clearly documented")
        else:
            concerns.append("Missing trade-off analysis")
            recommendations.append("Add trade-off analysis for key decisions")

        if len(proposal.dependencies) > 5:
            concerns.append("High number of dependencies")
            recommendations.append("Consider reducing coupling")
        else:
            strengths.append("Dependencies well managed")

        base_score = 70.0
        score = base_score + (len(strengths) * 10) - (len(concerns) * 10)
        score = max(0.0, min(100.0, score))

        return ArchitectureReview(
            proposal_id=proposal.id,
            score=score,
            strengths=strengths,
            concerns=concerns,
            recommendations=recommendations,
        )

    async def diagram(
        self,
        description: str,
        diagram_type: str = "flowchart",
    ) -> AsyncIterator[str]:
        """
        Generate architecture diagram.

        Args:
            description: What to diagram
            diagram_type: Type of diagram (flowchart, sequence, etc.)
        """
        yield f"[Architect] Generating {diagram_type} diagram...\n\n"

        yield "```mermaid\n"
        if diagram_type == "sequence":
            yield "sequenceDiagram\n"
            yield "    participant Client\n"
            yield "    participant API\n"
            yield "    participant Service\n"
            yield "    Client->>API: Request\n"
            yield "    API->>Service: Process\n"
            yield "    Service-->>API: Response\n"
            yield "    API-->>Client: Result\n"
        else:
            yield "graph TD\n"
            yield "    A[Start] --> B[Process]\n"
            yield "    B --> C{Decision}\n"
            yield "    C -->|Yes| D[Action A]\n"
            yield "    C -->|No| E[Action B]\n"
            yield "    D --> F[End]\n"
            yield "    E --> F\n"
        yield "```\n"

        yield "\n[Architect] Diagram generated\n"

    def get_status(self) -> Dict:
        """Get agent status."""
        return {
            "name": self.name,
            "provider": self._provider_name,
            "proposals": len(self._proposals),
            "three_loops_enabled": True,
        }


# Singleton instance
architect = ArchitectAgent()
