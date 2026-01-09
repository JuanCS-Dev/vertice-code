"""
DevOps Agent Types

Dataclasses and types for DevOps Agent.
Includes AWS-style incident handling types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class DeploymentEnvironment(str, Enum):
    """Deployment environments."""
    DEV = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class PipelineStatus(str, Enum):
    """CI/CD pipeline status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DeploymentConfig:
    """Deployment configuration."""
    environment: DeploymentEnvironment
    branch: str
    version: str
    replicas: int = 1
    resources: Dict[str, str] = field(default_factory=dict)
    env_vars: Dict[str, str] = field(default_factory=dict)
    health_check: Optional[str] = None


@dataclass
class PipelineRun:
    """A CI/CD pipeline run."""
    id: str
    name: str
    status: PipelineStatus
    steps: List[Dict]
    started_at: str
    finished_at: Optional[str] = None
    logs: List[str] = field(default_factory=list)


# =============================================================================
# AWS-STYLE INCIDENT HANDLING TYPES
# =============================================================================

class IncidentSeverity(str, Enum):
    """Incident severity levels."""
    SEV1 = "sev1"  # Critical - immediate response required
    SEV2 = "sev2"  # High - significant impact
    SEV3 = "sev3"  # Medium - partial impact
    SEV4 = "sev4"  # Low - minimal impact


class IncidentStatus(str, Enum):
    """Incident lifecycle status."""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    POSTMORTEM = "postmortem"


class RootCauseCategory(str, Enum):
    """Categories of root causes."""
    CODE_CHANGE = "code_change"
    RESOURCE_LIMIT = "resource_limit"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    TRAFFIC_SPIKE = "traffic_spike"
    DATA_ISSUE = "data_issue"
    INFRASTRUCTURE = "infrastructure"
    UNKNOWN = "unknown"


@dataclass
class TopologyNode:
    """
    A node in the system topology map.

    AWS DevOps Agent: "builds a topology map of an application's
    resources and their relationships"
    """
    id: str
    name: str
    type: str  # service, database, cache, queue, etc.
    environment: str
    dependencies: List[str] = field(default_factory=list)
    health_status: str = "healthy"
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class Alert:
    """An alert from monitoring systems."""
    id: str
    source: str
    severity: IncidentSeverity
    title: str
    description: str
    affected_resources: List[str]
    triggered_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InvestigationStep:
    """A step in the incident investigation."""
    id: str
    action: str
    findings: str
    timestamp: str
    data_sources: List[str]
    confidence: float


@dataclass
class RootCauseAnalysis:
    """Root cause analysis result."""
    category: RootCauseCategory
    description: str
    confidence: float
    evidence: List[str]
    contributing_factors: List[str]
    related_changes: List[Dict[str, Any]]


@dataclass
class Remediation:
    """A proposed remediation action."""
    id: str
    action: str
    description: str
    risk_level: str
    requires_approval: bool
    estimated_impact: str
    rollback_plan: str


@dataclass
class Incident:
    """Complete incident record."""
    id: str
    title: str
    severity: IncidentSeverity
    status: IncidentStatus
    alerts: List[Alert]
    affected_services: List[str]
    detected_at: str
    investigation_steps: List[InvestigationStep] = field(default_factory=list)
    root_cause: Optional[RootCauseAnalysis] = None
    remediations: List[Remediation] = field(default_factory=list)
    resolved_at: Optional[str] = None
    timeline: List[Dict[str, str]] = field(default_factory=list)
    mttr_seconds: Optional[int] = None

    def add_timeline_event(self, event: str) -> None:
        """Add event to incident timeline."""
        self.timeline.append({
            "timestamp": datetime.now().isoformat(),
            "event": event,
        })
