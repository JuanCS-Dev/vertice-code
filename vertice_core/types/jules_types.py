"""
Jules-specific data types for Google Jules integration.

Defines session states, activities, and configuration structures
shared across all Jules components.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class JulesSessionState(Enum):
    """Jules session lifecycle states (official API v1alpha)."""

    STATE_UNSPECIFIED = "STATE_UNSPECIFIED"
    QUEUED = "QUEUED"
    PLANNING = "PLANNING"
    AWAITING_PLAN_APPROVAL = "AWAITING_PLAN_APPROVAL"
    AWAITING_USER_FEEDBACK = "AWAITING_USER_FEEDBACK"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"


class JulesActivityType(Enum):
    """Types of Jules activities (official API v1alpha).

    Each activity has exactly one event type field.
    """

    PLAN_GENERATED = "planGenerated"      # { plan: Plan }
    PLAN_APPROVED = "planApproved"        # { planId: string }
    PROGRESS_UPDATED = "progressUpdated"  # { title, description }
    SESSION_COMPLETED = "sessionCompleted" # {}
    SESSION_FAILED = "sessionFailed"      # { reason: string }
    USER_MESSAGED = "userMessaged"        # { userMessage: string }
    AGENT_MESSAGED = "agentMessaged"      # { agentMessage: string }


@dataclass
class JulesSource:
    """Connected repository source."""

    id: str
    name: str
    provider: str  # "github", "gitlab", etc.
    url: Optional[str] = None


@dataclass
class JulesPlanStep:
    """Single step in a Jules execution plan (official API v1alpha)."""

    step_id: str           # id in API
    index: int             # 0-based position in sequence
    title: str             # step name
    description: str = ""  # step details


@dataclass
class JulesPlan:
    """Generated execution plan from Jules."""

    plan_id: str
    steps: List[JulesPlanStep] = field(default_factory=list)
    estimated_duration: Optional[str] = None
    files_to_modify: List[str] = field(default_factory=list)
    files_to_create: List[str] = field(default_factory=list)
    raw_content: str = ""


@dataclass
class JulesActivity:
    """Activity event from Jules session (official API v1alpha)."""

    activity_id: str              # name in API (sessions/{}/activities/{})
    type: JulesActivityType
    timestamp: datetime           # createTime in API
    originator: str = ""          # "user" | "agent" | "system"
    description: str = ""         # activity summary from API
    data: Dict[str, Any] = field(default_factory=dict)  # event type data
    message: str = ""             # extracted human-readable message


@dataclass
class JulesSession:
    """Jules session data (official API v1alpha)."""

    session_id: str              # name in API (sessions/{id})
    state: JulesSessionState
    title: str
    prompt: str
    created_at: datetime         # createTime in API
    updated_at: datetime         # updateTime in API
    url: str = ""                # web app session URL
    plan: Optional[JulesPlan] = None
    activities: List[JulesActivity] = field(default_factory=list)
    source_context: Optional[Dict[str, Any]] = None
    result_url: Optional[str] = None  # outputs.pullRequest.url
    error_message: Optional[str] = None


@dataclass
class JulesConfig:
    """Configuration for Jules client."""

    api_key: str
    base_url: str = "https://jules.googleapis.com/v1alpha"
    poll_interval: float = 5.0  # seconds
    max_poll_attempts: int = 360  # 30 minutes at 5s intervals
    timeout: float = 30.0  # HTTP request timeout
    require_plan_approval: bool = True  # Always manual per user preference


__all__ = [
    "JulesSessionState",
    "JulesActivityType",
    "JulesSource",
    "JulesPlanStep",
    "JulesPlan",
    "JulesActivity",
    "JulesSession",
    "JulesConfig",
]
