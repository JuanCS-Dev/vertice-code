"""
Vertice DevOps Agent

CI/CD and deployment specialist.
Uses Groq for fast infrastructure operations.

Responsibilities:
- CI/CD pipeline management
- Deployment automation
- Infrastructure configuration
- Monitoring setup
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, AsyncIterator
from enum import Enum
import logging

logger = logging.getLogger(__name__)


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


class DevOpsAgent:
    """
    DevOps Specialist - The Operator

    Uses Groq for:
    - Fast command generation
    - Infrastructure scripts
    - CI/CD configuration
    - Deployment automation

    Pattern: Automate everything, fail fast
    """

    name = "devops"
    description = """
    CI/CD and infrastructure specialist.
    Automates deployment, manages pipelines, monitors systems.
    Prioritizes reliability and reproducibility.
    """

    SYSTEM_PROMPT = """You are a DevOps specialist for Vertice Agency.

Your role is to automate infrastructure and deployments:

1. CI/CD PIPELINES
   - GitHub Actions / GitLab CI / Jenkins
   - Build, test, deploy stages
   - Parallelization for speed

2. CONTAINERIZATION
   - Dockerfile best practices
   - Multi-stage builds
   - Security scanning

3. INFRASTRUCTURE
   - Infrastructure as Code (Terraform, Pulumi)
   - Kubernetes manifests
   - Cloud configuration

4. MONITORING
   - Logging setup
   - Metrics collection
   - Alerting rules

Always:
- Use environment variables for secrets
- Implement health checks
- Plan for rollback
- Test in staging first
"""

    # Common CI/CD templates
    TEMPLATES = {
        "github-actions": """
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: echo "Deploy to production"
""",
        "dockerfile": """
# Multi-stage build for minimal image size
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0"]
""",
    }

    def __init__(self, provider: str = "groq"):
        self._provider_name = provider
        self._llm = None
        self._pipelines: Dict[str, PipelineRun] = {}

    async def create_pipeline(
        self,
        project_type: str,
        platform: str = "github-actions",
        steps: Optional[List[str]] = None,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """
        Create a CI/CD pipeline configuration.

        Args:
            project_type: Type of project (python, node, etc.)
            platform: CI/CD platform
            steps: Custom steps to include
            stream: Whether to stream output

        Yields:
            Pipeline configuration
        """
        yield f"[DevOps] Creating {platform} pipeline for {project_type}...\n"

        steps_str = ", ".join(steps) if steps else "build, test, deploy"

        prompt = f"""Create a CI/CD pipeline:

PROJECT TYPE: {project_type}
PLATFORM: {platform}
STEPS: {steps_str}

Include:
1. Dependency caching
2. Parallel test execution
3. Environment-specific deployments
4. Failure notifications

Generate complete, production-ready configuration.
"""

        # Return template for now
        if platform in self.TEMPLATES:
            yield f"\n```yaml\n{self.TEMPLATES[platform]}\n```\n"

        yield "\n[DevOps] Pipeline created\n"

    async def generate_dockerfile(
        self,
        project_type: str,
        base_image: Optional[str] = None,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """
        Generate a Dockerfile.

        Args:
            project_type: Type of project
            base_image: Optional base image override
            stream: Whether to stream output
        """
        yield f"[DevOps] Generating Dockerfile for {project_type}...\n"

        yield f"\n```dockerfile\n{self.TEMPLATES['dockerfile']}\n```\n"

        yield "\n[DevOps] Dockerfile generated\n"

    async def plan_deployment(
        self,
        config: DeploymentConfig,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """
        Plan a deployment.

        Args:
            config: Deployment configuration
            stream: Whether to stream output
        """
        yield f"[DevOps] Planning deployment to {config.environment.value}...\n"

        yield f"Version: {config.version}\n"
        yield f"Branch: {config.branch}\n"
        yield f"Replicas: {config.replicas}\n"

        if config.environment == DeploymentEnvironment.PRODUCTION:
            yield "\nProduction deployment requires L3_HUMAN_REQUIRED approval\n"
        elif config.environment == DeploymentEnvironment.STAGING:
            yield "\nStaging deployment requires L2_HUMAN_VETO (24h window)\n"
        else:
            yield "\nDevelopment deployment is L0_AUTONOMOUS\n"

        yield "\n[DevOps] Deployment plan ready\n"

    async def run_command(
        self,
        command: str,
        env: DeploymentEnvironment = DeploymentEnvironment.DEV,
    ) -> AsyncIterator[str]:
        """
        Run an infrastructure command.

        Args:
            command: Command to run
            env: Target environment
        """
        yield f"[DevOps] Running: {command}\n"
        yield f"[DevOps] Environment: {env.value}\n"

        # Safety checks
        dangerous_patterns = ["rm -rf /", "DROP DATABASE", ":(){:|:&};:"]
        for pattern in dangerous_patterns:
            if pattern in command:
                yield "[DevOps] BLOCKED: Dangerous command detected\n"
                return

        # TODO: Actually execute command in sandboxed environment

        yield "[DevOps] Command execution simulated\n"

    def get_status(self) -> Dict:
        """Get agent status."""
        return {
            "name": self.name,
            "provider": self._provider_name,
            "active_pipelines": len(self._pipelines),
        }


# Singleton instance
devops = DevOpsAgent()
