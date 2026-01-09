"""
Vertice Agency - Multi-Agent System

Agent Roster:
- Orchestrator: Lead agent, coordinates all others (Claude)
- Coder: Fast code generation (Groq)
- Reviewer: Code review and security (Vertex AI)
- Architect: System design (Claude)
- Researcher: Documentation and web search (Vertex AI)
- DevOps: CI/CD and deployment (Groq)
"""

from .orchestrator.agent import OrchestratorAgent, orchestrator
from .coder.agent import CoderAgent, coder
from .reviewer.agent import ReviewerAgent, reviewer
from .architect.agent import ArchitectAgent, architect
from .researcher.agent import ResearcherAgent, researcher
from .devops.agent import DevOpsAgent, devops

__all__ = [
    # Lead Agent
    "OrchestratorAgent",
    "orchestrator",
    # Specialists
    "CoderAgent",
    "coder",
    "ReviewerAgent",
    "reviewer",
    "ArchitectAgent",
    "architect",
    "ResearcherAgent",
    "researcher",
    "DevOpsAgent",
    "devops",
]
