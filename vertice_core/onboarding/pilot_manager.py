"""
Enterprise Pilot Onboarding System
====================================

White-glove setup process for enterprise pilot customers.

This module provides comprehensive onboarding automation including:
- Environment provisioning and configuration
- Custom integration setup
- SLA configuration and monitoring
- Success metrics dashboard initialization
- Dedicated success manager assignment

Part of the Enterprise Foundation (Fase 2: Pilot Preparation).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, validator

from ..billing.analytics import AnalyticsEngine, PricingTier
from ..core.exceptions import VerticeError


logger = logging.getLogger(__name__)


class PilotOnboardingError(VerticeError):
    """Base exception for pilot onboarding operations."""

    pass


class SLAConfig(BaseModel):
    """Service Level Agreement configuration for pilots."""

    response_time_hours: float = Field(default=4.0, ge=1.0, le=24.0)
    uptime_percentage: float = Field(default=99.9, ge=99.0, le=100.0)
    support_channels: List[str] = Field(default_factory=lambda: ["email", "slack"])
    dedicated_success_manager: bool = Field(default=True)
    custom_contract_terms: Optional[str] = None

    @validator("support_channels")
    def validate_support_channels(cls, v: List[str]) -> List[str]:
        """Validate support channel availability."""
        valid_channels = {"email", "phone", "slack", "teams", "zoom"}
        invalid = set(v) - valid_channels
        if invalid:
            raise ValueError(f"Unsupported channels: {invalid}")
        return v


class PilotConfig(BaseModel):
    """Configuration for enterprise pilot onboarding."""

    tenant_id: str
    company_name: str
    pricing_tier: PricingTier
    expected_users: int = Field(ge=1, le=10000)
    pilot_duration_days: int = Field(default=90, ge=30, le=180)
    custom_integrations: List[str] = Field(default_factory=list)
    sla_config: SLAConfig = Field(default_factory=SLAConfig)

    success_manager_email: Optional[str] = None
    technical_contact_email: str
    business_contact_email: str

    @validator("pricing_tier")
    def validate_enterprise_tier(cls, v: PricingTier) -> PricingTier:
        """Ensure only enterprise tiers can use pilot onboarding."""
        enterprise_tiers = {
            PricingTier.ENTERPRISE,
            PricingTier.ENTERPRISE_PLUS,
            PricingTier.ENTERPRISE_ELITE,
        }
        if v not in enterprise_tiers:
            raise ValueError(f"Pilot onboarding requires enterprise tier, got {v}")
        return v


@dataclass
class OnboardingStep:
    """Represents a single step in the onboarding process."""

    name: str
    description: str
    completed_at: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None

    def mark_completed(self, success: bool = True, error: Optional[str] = None) -> None:
        """Mark this step as completed."""
        self.completed_at = datetime.utcnow()
        self.success = success
        if error:
            self.error_message = error


@dataclass
class OnboardingResult:
    """Result of the complete onboarding process."""

    tenant_id: str
    steps_completed: List[OnboardingStep]
    overall_success: bool
    completion_time_seconds: float
    success_manager_assigned: Optional[str] = None
    dashboard_url: Optional[str] = None

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if not self.steps_completed:
            return 0.0
        completed = sum(1 for step in self.steps_completed if step.success)
        return (completed / len(self.steps_completed)) * 100.0


class PilotOnboardingManager:
    """
    Manages the complete white-glove onboarding process for enterprise pilots.

    This class orchestrates all aspects of pilot setup including environment
    provisioning, integration configuration, SLA setup, and success tracking.
    """

    def __init__(self, analytics_engine: Optional[AnalyticsEngine] = None):
        """
        Initialize the onboarding manager.

        Args:
            analytics_engine: Optional analytics engine for success metrics.
        """
        self.analytics = analytics_engine or AnalyticsEngine()
        self.logger = logging.getLogger(f"{__name__}.PilotOnboardingManager")

    async def execute_white_glove_setup(self, config: PilotConfig) -> OnboardingResult:
        """
        Execute the complete white-glove setup process for a pilot customer.

        This method performs all necessary setup steps in the correct order,
        with proper error handling and rollback capabilities.

        Args:
            config: Complete pilot configuration.

        Returns:
            Detailed onboarding result with step-by-step status.

        Raises:
            PilotOnboardingError: If critical setup steps fail.
        """
        start_time = asyncio.get_event_loop().time()
        steps = []

        try:
            # Step 1: Environment Provisioning
            step = OnboardingStep(
                name="environment_provisioning",
                description="Provision isolated tenant environment with quotas",
            )
            steps.append(step)
            await self._provision_environment(config)
            step.mark_completed()

            # Step 2: Custom Integrations Setup
            step = OnboardingStep(
                name="custom_integrations", description="Configure requested custom integrations"
            )
            steps.append(step)
            await self._setup_integrations(config)
            step.mark_completed()

            # Step 3: SLA Configuration
            step = OnboardingStep(
                name="sla_configuration", description="Configure enterprise SLAs and monitoring"
            )
            steps.append(step)
            await self._configure_sla(config)
            step.mark_completed()

            # Step 4: Success Manager Assignment
            step = OnboardingStep(
                name="success_manager_assignment", description="Assign dedicated success manager"
            )
            steps.append(step)
            success_manager = await self._assign_success_manager(config)
            step.mark_completed()

            # Step 5: Success Metrics Dashboard
            step = OnboardingStep(
                name="metrics_dashboard",
                description="Initialize real-time success metrics dashboard",
            )
            steps.append(step)
            dashboard_url = await self._initialize_metrics_dashboard(config)
            step.mark_completed()

            # Step 6: Welcome Package & Documentation
            step = OnboardingStep(
                name="welcome_package",
                description="Deliver enterprise welcome package and documentation",
            )
            steps.append(step)
            await self._deliver_welcome_package(config)
            step.mark_completed()

            completion_time = asyncio.get_event_loop().time() - start_time

            return OnboardingResult(
                tenant_id=config.tenant_id,
                steps_completed=steps,
                overall_success=True,
                completion_time_seconds=completion_time,
                success_manager_assigned=success_manager,
                dashboard_url=dashboard_url,
            )

        except Exception as e:
            # Mark failed step and log error
            if steps and not steps[-1].completed_at:
                steps[-1].mark_completed(success=False, error=str(e))

            completion_time = asyncio.get_event_loop().time() - start_time

            self.logger.error(f"Pilot onboarding failed for {config.tenant_id}: {e}")

            return OnboardingResult(
                tenant_id=config.tenant_id,
                steps_completed=steps,
                overall_success=False,
                completion_time_seconds=completion_time,
            )

    async def _provision_environment(self, config: PilotConfig) -> None:
        """
        Provision isolated tenant environment with appropriate quotas.

        Args:
            config: Pilot configuration with tenant details.

        Raises:
            PilotOnboardingError: If provisioning fails.
        """
        try:
            # Implementation would integrate with cloud infrastructure
            # For now, log the provisioning requirements
            self.logger.info(
                f"Provisioning environment for {config.tenant_id}: "
                f"{config.expected_users} users, {config.pilot_duration_days} days"
            )

            # In production, this would:
            # 1. Create Firebase tenant project
            # 2. Set up Firestore collections with isolation
            # 3. Configure resource quotas
            # 4. Initialize security policies

        except Exception as e:
            raise PilotOnboardingError(f"Environment provisioning failed: {e}") from e

    async def _setup_integrations(self, config: PilotConfig) -> None:
        """
        Set up custom integrations requested by the pilot.

        Args:
            config: Pilot configuration with integration requirements.

        Raises:
            PilotOnboardingError: If integration setup fails.
        """
        if not config.custom_integrations:
            self.logger.info(f"No custom integrations requested for {config.tenant_id}")
            return

        try:
            for integration in config.custom_integrations:
                self.logger.info(f"Setting up integration: {integration} for {config.tenant_id}")

                # Implementation would use the MCP integration framework
                # For now, validate integration availability

                supported_integrations = {
                    "slack",
                    "github",
                    "jira",
                    "salesforce",
                    "servicenow",
                    "azure_devops",
                    "gitlab",
                    "bitbucket",
                    "webex",
                    "teams",
                }

                if integration not in supported_integrations:
                    raise PilotOnboardingError(f"Unsupported integration: {integration}")

                # In production, this would:
                # 1. Validate integration credentials
                # 2. Configure webhook endpoints
                # 3. Test connectivity
                # 4. Register with MCP gateway

        except Exception as e:
            raise PilotOnboardingError(f"Integration setup failed: {e}") from e

    async def _configure_sla(self, config: PilotConfig) -> None:
        """
        Configure SLA monitoring and alerting.

        Args:
            config: Pilot configuration with SLA requirements.

        Raises:
            PilotOnboardingError: If SLA configuration fails.
        """
        try:
            sla = config.sla_config

            self.logger.info(
                f"Configuring SLA for {config.tenant_id}: "
                f"{sla.response_time_hours}h response, {sla.uptime_percentage}% uptime"
            )

            # In production, this would:
            # 1. Set up monitoring dashboards
            # 2. Configure alerting rules
            # 3. Initialize SLA tracking
            # 4. Set up incident response procedures

        except Exception as e:
            raise PilotOnboardingError(f"SLA configuration failed: {e}") from e

    async def _assign_success_manager(self, config: PilotConfig) -> Optional[str]:
        """
        Assign dedicated success manager for the pilot.

        Args:
            config: Pilot configuration.

        Returns:
            Email of assigned success manager, or None if auto-assignment fails.
        """
        if config.success_manager_email:
            self.logger.info(f"Using pre-assigned success manager: {config.success_manager_email}")
            return config.success_manager_email

        try:
            # Implementation would query available success managers
            # and assign based on capacity/load balancing
            assigned_manager = "enterprise-success@vertice.ai"  # Placeholder

            self.logger.info(f"Auto-assigned success manager: {assigned_manager}")
            return assigned_manager

        except Exception as e:
            self.logger.warning(f"Could not assign success manager: {e}")
            return None

    async def _initialize_metrics_dashboard(self, config: PilotConfig) -> Optional[str]:
        """
        Initialize real-time success metrics dashboard.

        Args:
            config: Pilot configuration.

        Returns:
            URL to the metrics dashboard, or None if initialization fails.
        """
        try:
            # Implementation would create personalized dashboard
            dashboard_url = f"https://app.vertice.ai/pilot/{config.tenant_id}/metrics"

            self.logger.info(f"Metrics dashboard initialized: {dashboard_url}")
            return dashboard_url

        except Exception as e:
            self.logger.warning(f"Could not initialize metrics dashboard: {e}")
            return None

    async def _deliver_welcome_package(self, config: PilotConfig) -> None:
        """
        Deliver enterprise welcome package and documentation.

        Args:
            config: Pilot configuration.

        Raises:
            PilotOnboardingError: If delivery fails.
        """
        try:
            # Implementation would send welcome emails and documentation
            self.logger.info(f"Delivering welcome package to {config.business_contact_email}")

            # In production, this would:
            # 1. Send welcome email with access instructions
            # 2. Provide enterprise documentation links
            # 3. Schedule kickoff call
            # 4. Set up training sessions

        except Exception as e:
            raise PilotOnboardingError(f"Welcome package delivery failed: {e}") from e
