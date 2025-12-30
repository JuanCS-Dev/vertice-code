"""
Architect Agent Types

Dataclasses and types for Architect Agent.
Includes Three Loops framework types.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum


class DesignLevel(str, Enum):
    """Abstraction levels for architecture."""
    SYSTEM = "system"
    SERVICE = "service"
    COMPONENT = "component"
    MODULE = "module"


@dataclass
class DesignProposal:
    """Architecture design proposal."""
    id: str
    name: str
    description: str
    level: DesignLevel
    components: List[str]
    dependencies: List[str]
    trade_offs: List[str]
    diagram_url: Optional[str] = None


@dataclass
class ArchitectureReview:
    """Review of architecture proposal."""
    proposal_id: str
    score: float
    strengths: List[str]
    concerns: List[str]
    recommendations: List[str]


# =============================================================================
# THREE LOOPS FRAMEWORK TYPES
# =============================================================================

class ArchitectLoop(str, Enum):
    """
    Three Loops classification for human-AI collaboration.

    Based on InfoQ "Where Architects Sit in the Era of AI":
    - IN: Architect decides, AI assists
    - ON: AI operates, architect supervises
    - OUT: AI self-designs with guardrails

    Reference: https://www.infoq.com/articles/architects-ai-era/
    """
    IN_THE_LOOP = "AITL"   # Architect In The Loop - co-design, human decides
    ON_THE_LOOP = "AOTL"   # Architect On The Loop - AI operates, human supervises
    OUT_OF_LOOP = "AOOTL"  # Architect Out Of Loop - AI self-designs


class DecisionImpact(str, Enum):
    """Impact level of architectural decisions."""
    CRITICAL = "critical"    # Affects entire system, hard to reverse
    HIGH = "high"            # Affects multiple services
    MEDIUM = "medium"        # Affects single service
    LOW = "low"              # Localized change


class DecisionRisk(str, Enum):
    """Risk level of architectural decisions."""
    HIGH = "high"        # Unknown territory, complex dependencies
    MEDIUM = "medium"    # Some uncertainty, manageable
    LOW = "low"          # Well-understood patterns


@dataclass
class LoopContext:
    """Context for loop selection decision."""
    decision_type: str
    impact: DecisionImpact
    risk: DecisionRisk
    agent_confidence: float
    requires_domain_expertise: bool
    ethical_considerations: bool
    regulatory_implications: bool


@dataclass
class LoopRecommendation:
    """Recommendation for which loop to use."""
    recommended_loop: ArchitectLoop
    confidence: float
    reasoning: str
    guardrails: List[str]
    transition_triggers: List[str]


@dataclass
class ThreeLoopsDesignResult:
    """Result of designing with Three Loops pattern."""
    loop_used: ArchitectLoop
    design: DesignProposal
    human_interventions: List[str]
    ai_decisions: List[str]
    confidence_score: float


# Loop selection matrix
LOOP_RULES: Dict[Tuple[DecisionImpact, DecisionRisk], ArchitectLoop] = {
    # (Impact, Risk) -> Loop
    (DecisionImpact.CRITICAL, DecisionRisk.HIGH): ArchitectLoop.IN_THE_LOOP,
    (DecisionImpact.CRITICAL, DecisionRisk.MEDIUM): ArchitectLoop.IN_THE_LOOP,
    (DecisionImpact.CRITICAL, DecisionRisk.LOW): ArchitectLoop.ON_THE_LOOP,
    (DecisionImpact.HIGH, DecisionRisk.HIGH): ArchitectLoop.IN_THE_LOOP,
    (DecisionImpact.HIGH, DecisionRisk.MEDIUM): ArchitectLoop.ON_THE_LOOP,
    (DecisionImpact.HIGH, DecisionRisk.LOW): ArchitectLoop.ON_THE_LOOP,
    (DecisionImpact.MEDIUM, DecisionRisk.HIGH): ArchitectLoop.ON_THE_LOOP,
    (DecisionImpact.MEDIUM, DecisionRisk.MEDIUM): ArchitectLoop.ON_THE_LOOP,
    (DecisionImpact.MEDIUM, DecisionRisk.LOW): ArchitectLoop.OUT_OF_LOOP,
    (DecisionImpact.LOW, DecisionRisk.HIGH): ArchitectLoop.ON_THE_LOOP,
    (DecisionImpact.LOW, DecisionRisk.MEDIUM): ArchitectLoop.OUT_OF_LOOP,
    (DecisionImpact.LOW, DecisionRisk.LOW): ArchitectLoop.OUT_OF_LOOP,
}
