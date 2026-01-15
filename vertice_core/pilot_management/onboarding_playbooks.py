"""
Enterprise Onboarding Playbooks
===============================

Structured onboarding playbooks for different enterprise customer profiles.

This module provides:
- Customizable onboarding templates
- Phase-based milestone tracking
- Success criteria definition
- Risk assessment and mitigation

Part of the Customer Success Foundation.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class OnboardingMilestone(BaseModel):
    """A milestone in the onboarding process."""

    id: str
    phase: str
    title: str
    description: str
    estimated_duration_days: int = Field(ge=1, le=30)

    # Dependencies and prerequisites
    prerequisites: List[str] = Field(default_factory=list)
    dependent_milestones: List[str] = Field(default_factory=list)

    # Success criteria
    success_criteria: List[str] = Field(default_factory=list)
    verification_method: str = "manual"  # manual, automated, stakeholder_review

    # Resources and assignments
    primary_responsible: str = "success_manager"
    supporting_roles: List[str] = Field(default_factory=list)
    required_resources: List[str] = Field(default_factory=list)

    # Risk assessment
    risk_level: str = "low"
    risk_mitigation_plan: List[str] = Field(default_factory=list)


class OnboardingPlaybook(BaseModel):
    """Complete onboarding playbook for enterprise customers."""

    id: str
    name: str
    description: str

    # Target customer profile
    applicable_tiers: List[str] = Field(default_factory=list)
    applicable_industries: List[str] = Field(default_factory=list)
    complexity_level: str = "standard"  # simple, standard, complex, enterprise

    # Timeline and phases
    estimated_duration_weeks: int = Field(ge=2, le=24)
    phases: List[str] = Field(
        default_factory=lambda: [
            "preparation",
            "discovery",
            "planning",
            "execution",
            "validation",
            "optimization",
            "completion",
        ]
    )

    # Milestones and deliverables
    milestones: List[OnboardingMilestone] = Field(default_factory=list)

    # Resources and checklists
    pre_onboarding_checklist: List[str] = Field(default_factory=list)
    weekly_checkpoints: Dict[int, List[str]] = Field(default_factory=dict)
    success_metrics: Dict[str, float] = Field(default_factory=dict)

    # Risk management
    common_risk_factors: List[str] = Field(default_factory=list)
    escalation_triggers: Dict[str, str] = Field(default_factory=dict)

    # Templates and collateral
    email_templates: Dict[str, str] = Field(default_factory=dict)
    meeting_agendas: Dict[str, List[str]] = Field(default_factory=dict)
    documentation_links: List[str] = Field(default_factory=list)


class OnboardingPlaybookManager:
    """
    Manager for enterprise onboarding playbooks.

    Provides customizable playbooks for different customer profiles
    and automated playbook execution tracking.
    """

    def __init__(self) -> None:
        """Initialize the playbook manager."""
        self.playbooks: Dict[str, OnboardingPlaybook] = {}
        self.logger = logging.getLogger(f"{__name__}.OnboardingPlaybookManager")

    def register_playbook(self, playbook: OnboardingPlaybook) -> None:
        """Register a new onboarding playbook."""
        self.playbooks[playbook.id] = playbook
        self.logger.info(f"Registered onboarding playbook: {playbook.name}")

    def get_playbook_for_customer(
        self, customer_profile: Dict[str, Any]
    ) -> Optional[OnboardingPlaybook]:
        """
        Get the best matching playbook for a customer profile.

        Args:
            customer_profile: Customer profile information

        Returns:
            Best matching playbook or None
        """
        customer_tier = customer_profile.get("tier", "enterprise")
        customer_industry = customer_profile.get("industry", "technology")
        customer_size = customer_profile.get("employee_count", 1000)

        best_match = None
        best_score = 0

        for playbook in self.playbooks.values():
            score = 0

            # Tier matching
            if customer_tier in playbook.applicable_tiers:
                score += 3
            elif playbook.applicable_tiers:  # Has restrictions but doesn't match
                continue  # Skip incompatible playbooks

            # Industry matching
            if customer_industry in playbook.applicable_industries:
                score += 2

            # Size appropriateness
            if customer_size >= 5000 and "enterprise" in playbook.complexity_level:
                score += 2
            elif customer_size >= 1000 and playbook.complexity_level in ["standard", "complex"]:
                score += 1

            if score > best_score:
                best_score = score
                best_match = playbook

        return best_match

    def customize_playbook_for_customer(
        self, playbook: OnboardingPlaybook, customer_profile: Dict[str, Any]
    ) -> OnboardingPlaybook:
        """
        Customize a playbook for specific customer needs.

        Args:
            playbook: Base playbook to customize
            customer_profile: Customer-specific information

        Returns:
            Customized playbook
        """
        import copy

        customized = copy.deepcopy(playbook)

        # Adjust timeline based on customer size
        customer_size = customer_profile.get("employee_count", 1000)
        if customer_size > 5000:
            customized.estimated_duration_weeks = int(customized.estimated_duration_weeks * 1.3)
        elif customer_size < 500:
            customized.estimated_duration_weeks = max(
                4, int(customized.estimated_duration_weeks * 0.8)
            )

        # Add customer-specific milestones if needed
        industry = customer_profile.get("industry", "technology")
        if industry == "healthcare":
            hipaa_milestone = OnboardingMilestone(
                id="hipaa_compliance_review",
                phase="validation",
                title="HIPAA Compliance Review",
                description="Review and validate HIPAA compliance measures",
                estimated_duration_days=3,
                success_criteria=["PHI data handling validated", "Breach response plan confirmed"],
                primary_responsible="success_manager",
                risk_level="high",
            )
            customized.milestones.append(hipaa_milestone)

        return customized

    def create_default_enterprise_playbook(self) -> OnboardingPlaybook:
        """Create a default enterprise onboarding playbook."""
        return OnboardingPlaybook(
            id="enterprise_default",
            name="Enterprise Onboarding Playbook",
            description="Standard onboarding process for enterprise customers",
            applicable_tiers=["enterprise", "enterprise_plus"],
            complexity_level="enterprise",
            estimated_duration_weeks=12,
            pre_onboarding_checklist=[
                "Schedule executive kickoff meeting",
                "Identify technical and business stakeholders",
                "Review contract and success criteria",
                "Set up customer success team assignments",
                "Prepare environment access and credentials",
            ],
            success_metrics={
                "user_adoption": 80.0,
                "system_uptime": 99.9,
                "user_satisfaction": 8.5,
                "roi_achievement": 100.0,
            },
        )
