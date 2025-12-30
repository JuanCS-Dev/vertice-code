"""
Vertice Architect Agent

System design and architecture specialist.
Uses Claude for deep reasoning about system design.

Responsibilities:
- System architecture design
- Technology stack decisions
- API design
- Scalability planning
- Technical debt assessment
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, AsyncIterator
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DesignPattern(str, Enum):
    """Common design patterns."""
    MICROSERVICES = "microservices"
    MONOLITH = "monolith"
    SERVERLESS = "serverless"
    EVENT_DRIVEN = "event_driven"
    LAYERED = "layered"
    HEXAGONAL = "hexagonal"
    CQRS = "cqrs"


@dataclass
class ArchitectureDecision:
    """An Architecture Decision Record (ADR)."""
    id: str
    title: str
    context: str
    decision: str
    consequences: List[str]
    alternatives: List[str] = field(default_factory=list)
    status: str = "proposed"  # proposed, accepted, deprecated, superseded


@dataclass
class SystemDesign:
    """Complete system design document."""
    name: str
    description: str
    components: List[Dict]
    data_flow: List[Dict]
    technology_stack: Dict[str, str]
    decisions: List[ArchitectureDecision]
    diagrams: Dict[str, str] = field(default_factory=dict)


class ArchitectAgent:
    """
    System Design Specialist - The Visionary

    Uses Claude Sonnet for:
    - High-level system design
    - Component architecture
    - API design
    - Scalability planning
    - Trade-off analysis

    Pattern: Think deeply, document decisions
    """

    name = "architect"
    description = """
    System architecture and design specialist.
    Makes high-level technical decisions with clear reasoning.
    Documents all decisions as ADRs (Architecture Decision Records).
    """

    SYSTEM_PROMPT = """You are the Chief Architect for Vertice Agency.

Your role is to make high-level technical decisions with:
1. Clear reasoning
2. Trade-off analysis
3. Long-term thinking
4. Documented alternatives

For EVERY decision, produce an ADR:
- Title: Short, descriptive name
- Context: Why is this decision needed?
- Decision: What was decided?
- Consequences: What are the implications?
- Alternatives: What else was considered?

Design Principles:
- KISS: Keep It Simple, Stupid
- YAGNI: You Aren't Gonna Need It
- DRY: Don't Repeat Yourself
- Separation of Concerns
- Single Responsibility

Always consider:
- Scalability
- Maintainability
- Testability
- Security
- Cost
"""

    def __init__(self, provider: str = "claude"):
        self._provider_name = provider
        self._llm = None
        self._decisions: List[ArchitectureDecision] = []

    async def design(
        self,
        requirement: str,
        context: Optional[str] = None,
        constraints: Optional[List[str]] = None,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """
        Design a system architecture.

        Args:
            requirement: What needs to be built
            context: Existing system context
            constraints: Technical or business constraints
            stream: Whether to stream output

        Yields:
            Design document and decisions
        """
        yield f"[Architect] Analyzing requirement...\n"

        constraints_str = "\n".join(f"- {c}" for c in constraints) if constraints else "None specified"

        prompt = f"""Design a system architecture for:

REQUIREMENT: {requirement}

EXISTING CONTEXT:
{context or "Greenfield project"}

CONSTRAINTS:
{constraints_str}

Provide:
1. High-level architecture diagram (ASCII)
2. Component breakdown
3. Technology stack recommendations
4. Data flow description
5. Key ADRs (Architecture Decision Records)
6. Risk assessment

Be thorough but pragmatic. Prefer proven patterns.
"""

        yield "[Architect] Designing architecture...\n\n"

        # TODO: Call LLM for actual design

        # Return template for now
        yield "## Proposed Architecture\n\n"
        yield "```\n"
        yield "┌─────────────────────────────────────────┐\n"
        yield "│              CLIENT LAYER               │\n"
        yield "│   (Web App / Mobile / CLI)              │\n"
        yield "└────────────────────┬────────────────────┘\n"
        yield "                     │\n"
        yield "                     ▼\n"
        yield "┌─────────────────────────────────────────┐\n"
        yield "│              API GATEWAY                │\n"
        yield "│   (Auth / Rate Limit / Routing)         │\n"
        yield "└────────────────────┬────────────────────┘\n"
        yield "                     │\n"
        yield "     ┌───────────────┼───────────────┐\n"
        yield "     ▼               ▼               ▼\n"
        yield "┌─────────┐   ┌─────────┐   ┌─────────┐\n"
        yield "│ Service │   │ Service │   │ Service │\n"
        yield "│    A    │   │    B    │   │    C    │\n"
        yield "└────┬────┘   └────┬────┘   └────┬────┘\n"
        yield "     │             │             │\n"
        yield "     └─────────────┼─────────────┘\n"
        yield "                   ▼\n"
        yield "┌─────────────────────────────────────────┐\n"
        yield "│              DATA LAYER                 │\n"
        yield "│   (PostgreSQL / Redis / S3)             │\n"
        yield "└─────────────────────────────────────────┘\n"
        yield "```\n\n"

        yield "[Architect] Design complete. Review ADRs for decisions.\n"

    async def decide(
        self,
        question: str,
        options: List[str],
        context: Optional[str] = None,
    ) -> ArchitectureDecision:
        """
        Make an architecture decision.

        Args:
            question: The decision to be made
            options: Available options
            context: Relevant context

        Returns:
            Architecture Decision Record
        """
        import uuid

        # TODO: Call LLM for analysis

        decision = ArchitectureDecision(
            id=str(uuid.uuid4())[:8],
            title=question[:50],
            context=context or "Technical decision required",
            decision=options[0] if options else "TBD",
            consequences=["To be analyzed"],
            alternatives=options[1:] if len(options) > 1 else [],
            status="proposed",
        )

        self._decisions.append(decision)
        return decision

    async def review_architecture(
        self,
        codebase_summary: str,
    ) -> AsyncIterator[str]:
        """
        Review existing architecture.

        Identifies technical debt and improvement opportunities.
        """
        yield "[Architect] Reviewing architecture...\n"

        prompt = f"""Review this codebase architecture:

{codebase_summary}

Analyze:
1. Architecture patterns in use
2. Technical debt
3. Scalability concerns
4. Security considerations
5. Improvement opportunities

Be constructive and prioritize recommendations.
"""

        yield "[Architect] Analysis complete.\n"

        # TODO: Call LLM for actual analysis

    def get_decisions(self) -> List[ArchitectureDecision]:
        """Get all recorded decisions."""
        return self._decisions

    def get_status(self) -> Dict:
        """Get agent status."""
        return {
            "name": self.name,
            "provider": self._provider_name,
            "decisions_made": len(self._decisions),
        }


# Singleton instance
architect = ArchitectAgent()
