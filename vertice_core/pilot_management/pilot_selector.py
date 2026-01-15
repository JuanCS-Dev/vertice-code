"""
Enterprise Pilot Customer Selection & Management
===============================================

Strategic selection and onboarding of enterprise pilot customers.

This module provides comprehensive pilot program management including:
- Customer qualification and selection criteria
- Pilot program application and review process
- Dedicated success manager assignment
- Onboarding workflow automation
- Success metrics tracking and reporting

Part of the Enterprise Pilot Launch (Fase 2 Mês 7).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator


logger = logging.getLogger(__name__)


class PilotStatus(Enum):
    """Status of a pilot customer in the program."""

    APPLIED = "applied"
    QUALIFIED = "qualified"
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class CustomerTier(Enum):
    """Enterprise customer size tiers."""

    STARTUP = "startup"  # 1-50 employees
    SMB = "smb"  # 51-500 employees
    MID_MARKET = "mid_market"  # 501-2000 employees
    ENTERPRISE = "enterprise"  # 2001-10000 employees
    ENTERPRISE_PLUS = "enterprise_plus"  # 10000+ employees


class IndustrySector(Enum):
    """Industry sectors for customer classification."""

    TECHNOLOGY = "technology"
    FINANCIAL_SERVICES = "financial_services"
    HEALTHCARE = "healthcare"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    PROFESSIONAL_SERVICES = "professional_services"
    EDUCATION = "education"
    GOVERNMENT = "government"
    OTHER = "other"


class SuccessManager(BaseModel):
    """Dedicated success manager for enterprise pilots."""

    id: str
    name: str
    email: str
    specialization: List[str] = Field(default_factory=list)  # Industry specialties
    current_pilots: int = Field(default=0, ge=0, le=5)  # Max 5 pilots per manager
    performance_score: float = Field(default=0.0, ge=0.0, le=5.0)

    @property
    def availability_score(self) -> float:
        """Calculate availability score (higher = more available)."""
        # Base score from capacity
        capacity_score = max(0, 5 - self.current_pilots) / 5.0

        # Performance multiplier
        performance_multiplier = self.performance_score / 5.0 if self.performance_score > 0 else 0.5

        return capacity_score * performance_multiplier


class PilotCustomerProfile(BaseModel):
    """Comprehensive profile of a potential pilot customer."""

    company_name: str
    website: Optional[str] = None
    industry: IndustrySector
    tier: CustomerTier

    # Contact Information
    technical_contact: ContactInfo
    business_contact: ContactInfo
    executive_sponsor: Optional[ContactInfo] = None

    # Company Details
    employee_count: int = Field(ge=1)
    annual_revenue: Optional[float] = None  # In millions USD
    geography: str  # Country/Region

    # Technical Profile
    current_tech_stack: List[str] = Field(default_factory=list)
    development_team_size: int = Field(ge=1)
    cloud_provider: Optional[str] = None
    compliance_requirements: List[str] = Field(default_factory=list)

    # Pilot Requirements
    expected_users: int = Field(ge=1, le=5000)
    pilot_duration_weeks: int = Field(default=12, ge=4, le=24)
    key_use_cases: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)

    # Selection Scoring
    strategic_fit_score: float = Field(default=0.0, ge=0.0, le=10.0)
    technical_readiness_score: float = Field(default=0.0, ge=0.0, le=10.0)
    budget_alignment_score: float = Field(default=0.0, ge=0.0, le=10.0)

    @property
    def overall_score(self) -> float:
        """Calculate overall selection score."""
        weights = {"strategic_fit": 0.4, "technical_readiness": 0.4, "budget_alignment": 0.2}

        return (
            self.strategic_fit_score * weights["strategic_fit"]
            + self.technical_readiness_score * weights["technical_readiness"]
            + self.budget_alignment_score * weights["budget_alignment"]
        )

    @validator("employee_count")
    def validate_employee_count(cls, v: int, values: Dict[str, Any]) -> int:
        """Ensure employee count matches tier."""
        if "tier" in values:
            tier = values["tier"]
            if tier == CustomerTier.STARTUP and v > 50:
                raise ValueError("Startup tier limited to 50 employees")
            elif tier == CustomerTier.SMB and (v < 51 or v > 500):
                raise ValueError("SMB tier requires 51-500 employees")
            elif tier == CustomerTier.MID_MARKET and (v < 501 or v > 2000):
                raise ValueError("Mid-market tier requires 501-2000 employees")
            elif tier == CustomerTier.ENTERPRISE and (v < 2001 or v > 10000):
                raise ValueError("Enterprise tier requires 2001-10000 employees")
            elif tier == CustomerTier.ENTERPRISE_PLUS and v < 10001:
                raise ValueError("Enterprise Plus tier requires 10000+ employees")
        return v


class ContactInfo(BaseModel):
    """Contact information for pilot stakeholders."""

    name: str
    title: str
    email: str
    phone: Optional[str] = None


@dataclass
class PilotProgram:
    """Active pilot program for an enterprise customer."""

    id: str
    customer: PilotCustomerProfile
    status: PilotStatus = PilotStatus.APPLIED

    # Timeline
    applied_date: datetime = field(default_factory=datetime.utcnow)
    qualified_date: Optional[datetime] = None
    onboarded_date: Optional[datetime] = None
    started_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None

    # Assignments
    success_manager: Optional[SuccessManager] = None
    technical_lead: Optional[str] = None

    # Progress Tracking
    onboarding_progress: float = 0.0  # 0-100%
    adoption_metrics: Dict[str, Any] = field(default_factory=dict)
    feedback_sessions: List[Dict[str, Any]] = field(default_factory=list)

    # Success Metrics
    target_metrics: Dict[str, float] = field(default_factory=dict)
    current_metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_days(self) -> int:
        """Calculate actual pilot duration in days."""
        start = self.started_date or self.onboarded_date
        end = self.completed_date or datetime.utcnow()

        if start:
            return (end - start).days
        return 0

    @property
    def success_score(self) -> float:
        """Calculate overall pilot success score."""
        if not self.target_metrics or not self.current_metrics:
            return 0.0

        scores = []
        for metric, target in self.target_metrics.items():
            current = self.current_metrics.get(metric, 0)
            if target > 0:
                achievement = min(current / target, 1.0)  # Cap at 100%
                scores.append(achievement)

        return float(sum(scores) / len(scores)) if scores else 0.0


class PilotSelectionCriteria(BaseModel):
    """Criteria for selecting enterprise pilot customers."""

    # Strategic Priorities
    target_industries: List[IndustrySector] = Field(default_factory=list)
    target_tiers: List[CustomerTier] = Field(
        default_factory=lambda: [CustomerTier.ENTERPRISE, CustomerTier.ENTERPRISE_PLUS]
    )
    minimum_score: float = Field(default=7.0, ge=0.0, le=10.0)

    # Technical Requirements
    required_compliance: List[str] = Field(default_factory=list)  # SOC2, GDPR, HIPAA, etc.
    minimum_team_size: int = Field(default=50, ge=10)
    preferred_tech_stack: List[str] = Field(default_factory=list)

    # Business Requirements
    minimum_revenue: Optional[float] = None  # In millions USD
    preferred_geography: List[str] = Field(default_factory=list)

    # Program Constraints
    max_pilots: int = Field(default=5, ge=1, le=10)
    pilot_duration_weeks: int = Field(default=12, ge=4, le=24)


class PilotCustomerSelector:
    """
    Intelligent selection engine for enterprise pilot customers.

    Uses scoring algorithms and business rules to identify the most promising
    pilot candidates from the sales pipeline.
    """

    def __init__(self, criteria: PilotSelectionCriteria):
        """
        Initialize the customer selector.

        Args:
            criteria: Selection criteria for pilot candidates.
        """
        self.criteria = criteria
        self.logger = logging.getLogger(f"{__name__}.PilotCustomerSelector")

    async def evaluate_customer(self, profile: PilotCustomerProfile) -> Dict[str, Any]:
        """
        Evaluate a customer profile against selection criteria.

        Args:
            profile: Customer profile to evaluate.

        Returns:
            Detailed evaluation results with scores and recommendations.
        """
        evaluation = {
            "overall_score": 0.0,
            "strategic_fit_score": 0.0,
            "technical_readiness_score": 0.0,
            "budget_alignment_score": 0.0,
            "recommendation": "REJECT",
            "reasoning": [],
            "strengths": [],
            "concerns": [],
        }

        # Strategic Fit Scoring
        strategic_score = await self._calculate_strategic_fit(profile)
        evaluation["strategic_fit_score"] = strategic_score

        # Technical Readiness Scoring
        technical_score = await self._calculate_technical_readiness(profile)
        evaluation["technical_readiness_score"] = technical_score

        # Budget Alignment Scoring
        budget_score = await self._calculate_budget_alignment(profile)
        evaluation["budget_alignment_score"] = budget_score

        # Overall Score Calculation
        weights = {"strategic": 0.4, "technical": 0.4, "budget": 0.2}
        overall_score = (
            strategic_score * weights["strategic"]
            + technical_score * weights["technical"]
            + budget_score * weights["budget"]
        )
        evaluation["overall_score"] = overall_score

        # Recommendation Logic
        evaluation.update(await self._generate_recommendation(overall_score, profile))

        return evaluation

    async def _calculate_strategic_fit(self, profile: PilotCustomerProfile) -> float:
        """Calculate strategic fit score (0-10)."""
        score = 0.0

        # Industry alignment (3 points)
        if profile.industry in self.criteria.target_industries:
            score += 3.0
        elif not self.criteria.target_industries:  # No industry restrictions
            score += 2.0

        # Company size alignment (3 points)
        if profile.tier in self.criteria.target_tiers:
            score += 3.0
        elif profile.tier.value in [t.value for t in self.criteria.target_tiers]:
            score += 2.5

        # Geography preference (2 points)
        if profile.geography in self.criteria.preferred_geography:
            score += 2.0
        elif not self.criteria.preferred_geography:
            score += 1.5

        # Revenue alignment (2 points)
        if self.criteria.minimum_revenue and profile.annual_revenue:
            if profile.annual_revenue >= self.criteria.minimum_revenue:
                score += 2.0
            elif profile.annual_revenue >= self.criteria.minimum_revenue * 0.7:
                score += 1.0

        return min(10.0, score)

    async def _calculate_technical_readiness(self, profile: PilotCustomerProfile) -> float:
        """Calculate technical readiness score (0-10)."""
        score = 0.0

        # Team size requirement (3 points)
        if profile.development_team_size >= self.criteria.minimum_team_size:
            score += 3.0
        elif profile.development_team_size >= self.criteria.minimum_team_size * 0.7:
            score += 2.0
        elif profile.development_team_size >= self.criteria.minimum_team_size * 0.5:
            score += 1.0

        # Tech stack compatibility (3 points)
        compatible_tech = set(profile.current_tech_stack) & set(self.criteria.preferred_tech_stack)
        if self.criteria.preferred_tech_stack:
            compatibility_ratio = len(compatible_tech) / len(self.criteria.preferred_tech_stack)
            score += compatibility_ratio * 3.0
        else:
            score += 2.0  # Neutral if no tech preferences

        # Compliance requirements (4 points)
        required_compliance = set(self.criteria.required_compliance)
        customer_compliance = set(profile.compliance_requirements)

        if required_compliance.issubset(customer_compliance):
            score += 4.0
        else:
            missing = required_compliance - customer_compliance
            if not missing:
                score += 3.0
            elif len(missing) == 1:
                score += 2.0

        return min(10.0, score)

    async def _calculate_budget_alignment(self, profile: PilotCustomerProfile) -> float:
        """Calculate budget alignment score (0-10)."""
        score = 0.0

        # Revenue-based budget proxy (4 points)
        if profile.annual_revenue:
            if profile.annual_revenue >= 100:  # $100M+ ARR
                score += 4.0
            elif profile.annual_revenue >= 50:
                score += 3.0
            elif profile.annual_revenue >= 10:
                score += 2.0
            else:
                score += 1.0

        # Employee count as budget indicator (3 points)
        if profile.employee_count >= 1000:
            score += 3.0
        elif profile.employee_count >= 500:
            score += 2.0
        elif profile.employee_count >= 100:
            score += 1.0

        # Enterprise tier alignment (3 points)
        tier_scores = {
            CustomerTier.ENTERPRISE_PLUS: 3.0,
            CustomerTier.ENTERPRISE: 2.5,
            CustomerTier.MID_MARKET: 2.0,
            CustomerTier.SMB: 1.0,
            CustomerTier.STARTUP: 0.5,
        }
        score += tier_scores.get(profile.tier, 1.0)

        return min(10.0, score)

    async def _generate_recommendation(
        self, score: float, profile: PilotCustomerProfile
    ) -> Dict[str, Any]:
        """Generate recommendation based on overall score."""
        result: Dict[str, Any] = {
            "recommendation": "REJECT",
            "reasoning": [],
            "strengths": [],
            "concerns": [],
        }

        if score >= self.criteria.minimum_score:
            result["recommendation"] = "APPROVE"
            result["reasoning"].append(
                f"Overall score {score:.1f} meets minimum threshold of {self.criteria.minimum_score}"
            )
        elif score >= self.criteria.minimum_score * 0.8:
            result["recommendation"] = "REVIEW"
            result["reasoning"].append(
                f"Overall score {score:.1f} is close to threshold - requires additional review"
            )
        else:
            result["reasoning"].append(
                f"Overall score {score:.1f} below minimum threshold of {self.criteria.minimum_score}"
            )

        # Identify strengths and concerns
        if profile.industry in self.criteria.target_industries:
            result["strengths"].append(f"Strong industry alignment: {profile.industry.value}")
        else:
            result["concerns"].append(f"Industry {profile.industry.value} not in primary targets")

        if profile.development_team_size >= self.criteria.minimum_team_size:
            result["strengths"].append(
                f"Large development team: {profile.development_team_size} engineers"
            )
        else:
            result["concerns"].append(
                f"Team size {profile.development_team_size} below minimum {self.criteria.minimum_team_size}"
            )

        if profile.tier in [CustomerTier.ENTERPRISE, CustomerTier.ENTERPRISE_PLUS]:
            result["strengths"].append(f"Enterprise-scale organization: {profile.tier.value}")
        else:
            result["concerns"].append(f"Company size {profile.tier.value} may limit pilot impact")

        return result


class PilotProgramManager:
    """
    Comprehensive management system for enterprise pilot programs.

    Handles the complete lifecycle from customer selection through program completion,
    including success tracking, iteration management, and stakeholder communication.
    """

    def __init__(self) -> None:
        """Initialize the pilot program manager."""
        self.programs: Dict[str, PilotProgram] = {}
        self.success_managers: List[SuccessManager] = []
        self.selector = PilotCustomerSelector(PilotSelectionCriteria())
        self.logger = logging.getLogger(f"{__name__}.PilotProgramManager")

    async def submit_pilot_application(self, profile: PilotCustomerProfile) -> str:
        """
        Submit a new pilot application for evaluation.

        Args:
            profile: Customer profile for pilot consideration.

        Returns:
            Pilot program ID for tracking.
        """
        program_id = f"pilot_{profile.company_name.lower().replace(' ', '_')}_{int(datetime.utcnow().timestamp())}"

        program = PilotProgram(id=program_id, customer=profile, status=PilotStatus.APPLIED)

        self.programs[program_id] = program

        # Auto-qualify based on selection criteria
        await self._evaluate_application(program_id)

        self.logger.info(f"Pilot application submitted: {program_id} for {profile.company_name}")
        return program_id

    async def _evaluate_application(self, program_id: str) -> None:
        """Evaluate a pilot application and update status."""
        program = self.programs.get(program_id)
        if not program:
            return

        evaluation = await self.selector.evaluate_customer(program.customer)

        # Update customer profile with evaluation scores
        program.customer.strategic_fit_score = evaluation["strategic_fit_score"]
        program.customer.technical_readiness_score = evaluation["technical_readiness_score"]
        program.customer.budget_alignment_score = evaluation["budget_alignment_score"]

        # Update program status
        if evaluation["recommendation"] == "APPROVE":
            program.status = PilotStatus.QUALIFIED
            program.qualified_date = datetime.utcnow()
            await self._assign_success_manager(program)
        elif evaluation["recommendation"] == "REVIEW":
            program.status = PilotStatus.APPLIED  # Requires manual review
        else:
            program.status = PilotStatus.CANCELLED

    async def _assign_success_manager(self, program: PilotProgram) -> None:
        """Assign the best available success manager to a pilot program."""
        if not self.success_managers:
            self.logger.warning("No success managers available for assignment")
            return

        # Find best fit based on availability and specialization
        best_manager = None
        best_score = 0.0

        for manager in self.success_managers:
            if manager.current_pilots >= 5:  # Max capacity
                continue

            # Base score from availability
            score = manager.availability_score

            # Bonus for industry specialization
            if program.customer.industry.value in manager.specialization:
                score *= 1.5

            if score > best_score:
                best_score = score
                best_manager = manager

        if best_manager:
            program.success_manager = best_manager
            best_manager.current_pilots += 1
            self.logger.info(f"Assigned {best_manager.name} to pilot {program.id}")

    async def start_onboarding(self, program_id: str) -> bool:
        """
        Start the onboarding process for a qualified pilot.

        Args:
            program_id: Pilot program identifier.

        Returns:
            True if onboarding started successfully.
        """
        program = self.programs.get(program_id)
        if not program or program.status != PilotStatus.QUALIFIED:
            return False

        program.status = PilotStatus.ONBOARDING
        program.onboarded_date = datetime.utcnow()

        # Initialize onboarding tracking
        program.onboarding_progress = 0.0

        self.logger.info(f"Started onboarding for pilot {program_id}")
        return True

    async def update_pilot_progress(
        self, program_id: str, progress: float, metrics: Dict[str, Any]
    ) -> None:
        """
        Update progress and metrics for an active pilot.

        Args:
            program_id: Pilot program identifier.
            progress: Overall progress percentage (0-100).
            metrics: Current performance metrics.
        """
        program = self.programs.get(program_id)
        if not program:
            return

        program.onboarding_progress = progress
        program.current_metrics.update(metrics)

        # Check for completion criteria
        if progress >= 100.0 and program.status == PilotStatus.ONBOARDING:
            program.status = PilotStatus.ACTIVE
            program.started_date = datetime.utcnow()

        self.logger.info(f"Updated progress for pilot {program_id}: {progress}% complete")

    async def schedule_feedback_session(
        self, program_id: str, session_type: str, notes: str
    ) -> bool:
        """
        Schedule a feedback session for a pilot program.

        Args:
            program_id: Pilot program identifier.
            session_type: Type of feedback session (kickoff, weekly, milestone, etc.).
            notes: Additional notes about the session.

        Returns:
            True if session was scheduled successfully.
        """
        program = self.programs.get(program_id)
        if not program:
            return False

        session = {
            "type": session_type,
            "scheduled_date": datetime.utcnow() + timedelta(days=7),  # Default to 1 week out
            "notes": notes,
            "status": "scheduled",
        }

        program.feedback_sessions.append(session)
        self.logger.info(f"Scheduled {session_type} feedback session for pilot {program_id}")
        return True

    async def complete_pilot(self, program_id: str, success_score: float, feedback: str) -> bool:
        """
        Complete a pilot program with final assessment.

        Args:
            program_id: Pilot program identifier.
            success_score: Final success score (0-1).
            feedback: Final feedback and lessons learned.

        Returns:
            True if pilot was completed successfully.
        """
        program = self.programs.get(program_id)
        if not program:
            return False

        program.status = PilotStatus.COMPLETED if success_score >= 0.7 else PilotStatus.FAILED
        program.completed_date = datetime.utcnow()

        # Update final metrics
        program.current_metrics["final_success_score"] = success_score
        program.current_metrics["completion_feedback"] = feedback

        # Free up success manager
        if program.success_manager:
            program.success_manager.current_pilots = max(
                0, program.success_manager.current_pilots - 1
            )

        self.logger.info(f"Completed pilot {program_id} with success score {success_score}")
        return True

    async def get_pilot_report(self, program_id: str) -> Optional[Dict[str, Any]]:
        """
        Generate a comprehensive report for a pilot program.

        Args:
            program_id: Pilot program identifier.

        Returns:
            Complete pilot program report, or None if not found.
        """
        program = self.programs.get(program_id)
        if not program:
            return None

        return {
            "program_id": program.id,
            "customer": program.customer.dict(),
            "status": program.status.value,
            "timeline": {
                "applied": program.applied_date.isoformat(),
                "qualified": program.qualified_date.isoformat() if program.qualified_date else None,
                "onboarded": program.onboarded_date.isoformat() if program.onboarded_date else None,
                "started": program.started_date.isoformat() if program.started_date else None,
                "completed": program.completed_date.isoformat() if program.completed_date else None,
                "duration_days": program.duration_days,
            },
            "assignments": {
                "success_manager": (
                    program.success_manager.dict() if program.success_manager else None
                ),
                "technical_lead": program.technical_lead,
            },
            "progress": {
                "onboarding_progress": program.onboarding_progress,
                "success_score": program.success_score,
                "target_metrics": program.target_metrics,
                "current_metrics": program.current_metrics,
            },
            "engagement": {
                "feedback_sessions_count": len(program.feedback_sessions),
                "last_feedback_session": (
                    program.feedback_sessions[-1] if program.feedback_sessions else None
                ),
            },
        }

    async def get_programs_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all pilot programs.

        Returns:
            Summary statistics and status overview.
        """
        total_programs = len(self.programs)
        status_counts: Dict[str, int] = {}

        for program in self.programs.values():
            status_counts[program.status.value] = status_counts.get(program.status.value, 0) + 1

        active_programs = [
            p
            for p in self.programs.values()
            if p.status in [PilotStatus.ONBOARDING, PilotStatus.ACTIVE]
        ]

        avg_success_score = (
            sum(p.success_score for p in active_programs) / len(active_programs)
            if active_programs
            else 0.0
        )

        return {
            "total_programs": total_programs,
            "status_breakdown": status_counts,
            "active_programs": len(active_programs),
            "average_success_score": avg_success_score,
            "programs_by_industry": self._get_industry_breakdown(),
            "programs_by_tier": self._get_tier_breakdown(),
        }

    def _get_industry_breakdown(self) -> Dict[str, int]:
        """Get program count by industry sector."""
        breakdown: Dict[str, int] = {}
        for program in self.programs.values():
            industry = program.customer.industry.value
            breakdown[industry] = breakdown.get(industry, 0) + 1
        return breakdown

    def _get_tier_breakdown(self) -> Dict[str, int]:
        """Get program count by customer tier."""
        breakdown: Dict[str, int] = {}
        for program in self.programs.values():
            tier = program.customer.tier.value
            breakdown[tier] = breakdown.get(tier, 0) + 1
        return breakdown
