"""
DevOps Domain Models - Data structures for DevOps operations.

Contains:
- IncidentSeverity: Severity levels enum
- RemediationAction: Autonomous remediation types
- DeploymentStrategy: Deployment strategies
- IncidentDetection: Detected incident with response plan
- DeploymentPlan: Deployment with safety guarantees
- InfrastructureHealth: Real-time health assessment
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


class IncidentSeverity(str, Enum):
    """Incident severity levels."""

    P0 = "p0"  # Critical - immediate action
    P1 = "p1"  # High - action within 1 hour
    P2 = "p2"  # Medium - action within 24 hours
    P3 = "p3"  # Low - action when possible


class RemediationAction(str, Enum):
    """Types of autonomous remediation actions."""

    RESTART_POD = "restart_pod"
    SCALE_DEPLOYMENT = "scale_deployment"
    ROLLBACK_DEPLOYMENT = "rollback_deployment"
    ADJUST_RESOURCES = "adjust_resources"
    CLEAR_CACHE = "clear_cache"
    RESTART_SERVICE = "restart_service"
    TRIGGER_BACKUP = "trigger_backup"


class DeploymentStrategy(str, Enum):
    """Deployment strategies."""

    ROLLING_UPDATE = "rolling_update"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    RECREATE = "recreate"


@dataclass
class IncidentDetection:
    """Detected incident with autonomous response plan."""

    incident_id: str
    severity: IncidentSeverity
    description: str
    affected_services: List[str]
    root_cause: str
    recommended_actions: List[RemediationAction]
    can_auto_remediate: bool
    time_to_detect: float  # seconds
    predicted_impact: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "severity": self.severity.value,
            "description": self.description,
            "affected_services": self.affected_services,
            "root_cause": self.root_cause,
            "recommended_actions": [a.value for a in self.recommended_actions],
            "can_auto_remediate": self.can_auto_remediate,
            "time_to_detect": self.time_to_detect,
            "predicted_impact": self.predicted_impact,
        }


@dataclass
class DeploymentPlan:
    """Deployment plan with safety guarantees."""

    deployment_id: str
    strategy: DeploymentStrategy
    pre_checks: List[str]
    deployment_steps: List[str]
    post_checks: List[str]
    rollback_plan: List[str]
    estimated_downtime: float  # seconds
    health_check_endpoint: str
    success_criteria: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deployment_id": self.deployment_id,
            "strategy": self.strategy.value,
            "estimated_downtime": self.estimated_downtime,
            "health_check_endpoint": self.health_check_endpoint,
            "pre_checks": self.pre_checks,
            "post_checks": self.post_checks,
            "success_criteria": self.success_criteria,
        }


@dataclass
class InfrastructureHealth:
    """Real-time infrastructure health assessment."""

    overall_score: float  # 0-100
    cluster_health: float
    application_health: float
    cost_efficiency: float
    security_posture: float
    predicted_issues: List[str]
    recommendations: List[str]
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "cluster_health": self.cluster_health,
            "application_health": self.application_health,
            "cost_efficiency": self.cost_efficiency,
            "security_posture": self.security_posture,
            "predicted_issues": self.predicted_issues,
            "recommendations": self.recommendations,
        }
