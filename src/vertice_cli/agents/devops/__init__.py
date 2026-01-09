"""
DevOps Module - The Infrastructure Guardian.

Autonomous DevOps operations with:
- Incident detection and remediation (30 seconds vs 30 minutes)
- Zero-downtime deployments with ArgoCD/Flux
- Infrastructure generation (Docker, K8s, CI/CD, Terraform)
- Real-time health monitoring

Usage:
    from vertice_cli.agents.devops import DevOpsAgent, create_devops_agent

    agent = create_devops_agent(llm_client, auto_remediate=True)
    result = await agent.execute(AgentTask(request="Deploy new version"))
"""

# Models
from .models import (
    IncidentSeverity,
    RemediationAction,
    DeploymentStrategy,
    IncidentDetection,
    DeploymentPlan,
    InfrastructureHealth,
)

# Components
from .incident_responder import IncidentResponder
from .deployment_orchestrator import DeploymentOrchestrator
from .health_checker import HealthChecker

# Generators
from .generators import (
    BaseGenerator,
    DockerfileGenerator,
    KubernetesGenerator,
    CICDGenerator,
    TerraformGenerator,
)

# Agent
from .agent import DevOpsAgent, create_devops_agent

__all__ = [
    # Models
    "IncidentSeverity",
    "RemediationAction",
    "DeploymentStrategy",
    "IncidentDetection",
    "DeploymentPlan",
    "InfrastructureHealth",
    # Components
    "IncidentResponder",
    "DeploymentOrchestrator",
    "HealthChecker",
    # Generators
    "BaseGenerator",
    "DockerfileGenerator",
    "KubernetesGenerator",
    "CICDGenerator",
    "TerraformGenerator",
    # Agent
    "DevOpsAgent",
    "create_devops_agent",
]
