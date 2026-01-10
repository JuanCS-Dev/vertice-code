"""
Enterprise Product Iteration Engine
====================================

Comprehensive system for managing enterprise feature requests, prioritization,
and product iteration based on customer feedback and business value.

This module provides:
- Feature request collection and management
- Enterprise customer feedback integration
- Multi-dimensional prioritization framework
- Product roadmap planning and tracking
- Iteration planning and delivery management
- Business value and ROI analysis

Part of the Enterprise Pilot Launch (Fase 2 Mês 7).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator



logger = logging.getLogger(__name__)


class FeatureStatus(Enum):
    """Status of a feature request in the development lifecycle."""

    SUBMITTED = "submitted"
    REVIEWED = "reviewed"
    PRIORITIZED = "prioritized"
    PLANNED = "planned"
    IN_DEVELOPMENT = "in_development"
    TESTING = "testing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class FeatureCategory(Enum):
    """Categories for feature classification."""

    SECURITY = "security"
    COMPLIANCE = "compliance"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    USABILITY = "usability"
    ANALYTICS = "analytics"
    ADMINISTRATION = "administration"
    API = "api"
    MOBILE = "mobile"
    AI_ML = "ai_ml"


class BusinessValue(Enum):
    """Business value assessment levels."""

    TRANSFORMATIONAL = "transformational"  # Game-changing capability
    HIGH = "high"  # Significant competitive advantage
    MEDIUM = "medium"  # Important but not critical
    LOW = "low"  # Nice to have
    MINIMAL = "minimal"  # Questionable value


class EffortLevel(Enum):
    """Development effort estimation levels."""

    EXTRA_SMALL = "extra_small"  # 1-2 days
    SMALL = "small"  # 3-7 days
    MEDIUM = "medium"  # 1-3 weeks
    LARGE = "large"  # 1-2 months
    EXTRA_LARGE = "extra_large"  # 2-6 months
    EPIC = "epic"  # 6+ months


class CustomerSegment(Enum):
    """Customer segments for feature targeting."""

    STARTUP = "startup"
    SMB = "smb"
    MID_MARKET = "mid_market"
    ENTERPRISE = "enterprise"
    ENTERPRISE_PLUS = "enterprise_plus"
    ALL = "all"


class FeatureRequest(BaseModel):
    """A feature request from customers or internal stakeholders."""

    id: str
    title: str
    description: str
    category: FeatureCategory

    # Request metadata
    submitted_by: str  # Customer ID or internal user
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    customer_segment: CustomerSegment

    # Business context
    business_value: BusinessValue
    business_impact: str  # Detailed business impact description
    success_metrics: List[str] = Field(default_factory=list)

    # Technical details
    technical_description: Optional[str] = None
    technical_complexity: EffortLevel
    dependencies: List[str] = Field(default_factory=list)  # Other features/systems required

    # Status and tracking
    status: FeatureStatus = FeatureStatus.SUBMITTED
    priority_score: float = 0.0  # Calculated priority score
    target_release: Optional[str] = None  # Version/quarter target

    # Relationships
    related_features: List[str] = Field(default_factory=list)  # Related feature IDs
    customer_feedback_id: Optional[str] = None  # Link to customer feedback

    # Progress tracking
    assigned_to: Optional[str] = None
    estimated_effort: Optional[EffortLevel] = None
    actual_effort: Optional[float] = None  # Days spent
    completion_date: Optional[datetime] = None

    @property
    def is_completed(self) -> bool:
        """Check if the feature is completed."""
        return self.status == FeatureStatus.COMPLETED

    @property
    def is_active(self) -> bool:
        """Check if the feature is actively being worked on."""
        return self.status in [FeatureStatus.IN_DEVELOPMENT, FeatureStatus.TESTING]

    @property
    def age_days(self) -> int:
        """Calculate how many days since submission."""
        return (datetime.utcnow() - self.submitted_at).days


class PrioritizationCriteria(BaseModel):
    """Criteria for feature prioritization."""

    # RICE scoring weights (Reach, Impact, Confidence, Effort)
    reach_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    impact_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    confidence_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    effort_weight: float = Field(default=0.25, ge=0.0, le=1.0)

    # Additional enterprise factors
    strategic_alignment_weight: float = Field(default=0.2, ge=0.0, le=1.0)
    customer_satisfaction_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    compliance_security_weight: float = Field(default=0.1, ge=0.0, le=1.0)

    # Business constraints
    max_effort_days: int = Field(default=90, ge=1, le=365)
    strategic_initiatives: List[str] = Field(default_factory=list)  # Must-have features

    @field_validator(
        "reach_weight",
        "impact_weight",
        "confidence_weight",
        "effort_weight",
        "strategic_alignment_weight",
        "customer_satisfaction_weight",
        "compliance_security_weight",
    )
    @classmethod
    def validate_weights(cls, v: float) -> float:
        """Ensure weights are valid individual values."""
        # This would be validated at the model level, but for now just check individual values
        return v


class RoadmapMilestone(BaseModel):
    """A milestone in the product roadmap."""

    id: str
    name: str
    description: str
    target_date: datetime
    theme: str  # Strategic theme (e.g., "Enterprise Expansion", "AI Enhancement")

    # Content
    planned_features: List[str] = Field(default_factory=list)  # Feature IDs
    key_objectives: List[str] = Field(default_factory=list)

    # Status
    status: str = "planned"  # planned, in_progress, completed, delayed
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)

    # Business impact
    expected_business_value: float = 0.0  # Expected revenue impact
    risk_level: str = "medium"  # low, medium, high, critical


@dataclass
class IterationPlan:
    """A product iteration plan (sprint/release)."""

    id: str
    name: str
    start_date: datetime
    end_date: datetime

    # Capacity and goals
    team_capacity_days: int  # Total team capacity in person-days
    planned_features: List[str] = field(default_factory=list)  # Feature IDs
    stretch_goals: List[str] = field(default_factory=list)  # Nice-to-have features

    # Status
    status: str = "planned"  # planned, active, completed
    completed_features: List[str] = field(default_factory=list)

    # Metrics
    planned_velocity: float = 0.0  # Story points or feature points
    actual_velocity: float = 0.0
    quality_score: float = 0.0  # 0-100 quality assessment

    @property
    def duration_days(self) -> int:
        """Calculate iteration duration."""
        return (self.end_date - self.start_date).days

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        total_features = len(self.planned_features)
        if total_features == 0:
            return 100.0
        return (len(self.completed_features) / total_features) * 100.0

    @property
    def capacity_utilization(self) -> float:
        """Calculate capacity utilization."""
        # Simplified calculation based on planned vs actual features
        planned_effort = sum(self._estimate_feature_effort(fid) for fid in self.planned_features)
        if planned_effort == 0:
            return 0.0
        return min(100.0, (planned_effort / self.team_capacity_days) * 100.0)

    def _estimate_feature_effort(self, feature_id: str) -> float:
        """Estimate effort for a feature (simplified)."""
        # In production, this would look up actual estimates
        effort_map = {"small": 3, "medium": 10, "large": 25, "extra_large": 60}
        # Default to medium effort
        return effort_map.get("medium", 10)


class ProductIterationEngine:
    """
    Enterprise product iteration engine for feature prioritization and roadmap management.

    Provides sophisticated prioritization algorithms, roadmap planning, and iteration
    management specifically designed for enterprise SaaS products.
    """

    def __init__(self) -> None:
        """Initialize the product iteration engine."""
        self.feature_requests: Dict[str, FeatureRequest] = {}
        self.roadmap_milestones: Dict[str, RoadmapMilestone] = {}
        self.iteration_plans: Dict[str, IterationPlan] = {}
        self.prioritization_criteria = PrioritizationCriteria()
        self.logger = logging.getLogger(f"{__name__}.ProductIterationEngine")

    async def submit_feature_request(
        self,
        title: str,
        description: str,
        category: FeatureCategory,
        submitted_by: str,
        customer_segment: CustomerSegment,
        business_value: BusinessValue,
        business_impact: str,
        technical_complexity: EffortLevel,
        success_metrics: Optional[List[str]] = None,
    ) -> str:
        """
        Submit a new feature request.

        Args:
            title: Feature title
            description: Detailed description
            category: Feature category
            submitted_by: Customer or user ID
            customer_segment: Target customer segment
            business_value: Business value assessment
            business_impact: Business impact description
            technical_complexity: Development effort level
            success_metrics: Success measurement criteria

        Returns:
            Feature request ID
        """
        feature_id = f"feat_{int(datetime.utcnow().timestamp())}_{hash(title) % 1000}"

        feature = FeatureRequest(
            id=feature_id,
            title=title,
            description=description,
            category=category,
            submitted_by=submitted_by,
            customer_segment=customer_segment,
            business_value=business_value,
            business_impact=business_impact,
            technical_complexity=technical_complexity,
            success_metrics=success_metrics or [],
        )

        self.feature_requests[feature_id] = feature

        # Auto-prioritize the new feature
        await self._prioritize_feature(feature_id)

        self.logger.info(f"Submitted feature request: {feature_id} - {title}")
        return feature_id

    async def _prioritize_feature(self, feature_id: str) -> None:
        """Calculate and assign priority score to a feature."""
        feature = self.feature_requests.get(feature_id)
        if not feature:
            return

        # RICE scoring components
        reach_score = self._calculate_reach_score(feature)
        impact_score = self._calculate_impact_score(feature)
        confidence_score = self._calculate_confidence_score(feature)
        effort_score = self._calculate_effort_score(feature)

        # Enterprise-specific factors
        strategic_score = self._calculate_strategic_alignment(feature)
        satisfaction_score = self._calculate_customer_satisfaction_impact(feature)
        compliance_score = self._calculate_compliance_security_value(feature)

        # Weighted calculation
        criteria = self.prioritization_criteria
        rice_score = (
            reach_score * criteria.reach_weight
            + impact_score * criteria.impact_weight
            + confidence_score * criteria.confidence_weight
            + (1 / effort_score) * criteria.effort_weight  # Lower effort = higher priority
        )

        enterprise_score = (
            strategic_score * criteria.strategic_alignment_weight
            + satisfaction_score * criteria.customer_satisfaction_weight
            + compliance_score * criteria.compliance_security_weight
        )

        # Final priority score (0-100 scale)
        feature.priority_score = min(100.0, (rice_score * 0.7 + enterprise_score * 0.3) * 10)

        # Update status if not already reviewed
        if feature.status == FeatureStatus.SUBMITTED:
            feature.status = FeatureStatus.REVIEWED

    def _calculate_reach_score(self, feature: FeatureRequest) -> float:
        """Calculate reach score (0-10) - how many users/customers affected."""
        # Base reach by customer segment
        segment_multipliers = {
            CustomerSegment.STARTUP: 1,
            CustomerSegment.SMB: 3,
            CustomerSegment.MID_MARKET: 5,
            CustomerSegment.ENTERPRISE: 7,
            CustomerSegment.ENTERPRISE_PLUS: 9,
            CustomerSegment.ALL: 10,
        }

        base_reach = segment_multipliers.get(feature.customer_segment, 5)

        # Adjust based on feature category (some features have broader impact)
        category_multipliers = {
            FeatureCategory.SECURITY: 1.2,  # Security affects everyone
            FeatureCategory.COMPLIANCE: 1.1,  # Compliance is enterprise-wide
            FeatureCategory.PERFORMANCE: 1.1,  # Performance affects all users
            FeatureCategory.USABILITY: 1.0,  # Standard reach
            FeatureCategory.INTEGRATION: 0.9,  # Depends on integration usage
            FeatureCategory.ANALYTICS: 0.8,  # Analytics features have limited reach
            FeatureCategory.API: 0.8,  # API features affect developers
            FeatureCategory.ADMINISTRATION: 0.7,  # Admin features have limited reach
            FeatureCategory.MOBILE: 0.6,  # Mobile features affect mobile users
            FeatureCategory.AI_ML: 0.9,  # AI features have good reach
        }

        return min(10.0, base_reach * category_multipliers.get(feature.category, 1.0))

    def _calculate_impact_score(self, feature: FeatureRequest) -> float:
        """Calculate impact score (0-10) - business impact magnitude."""
        # Base impact from business value assessment
        value_multipliers = {
            BusinessValue.TRANSFORMATIONAL: 10,
            BusinessValue.HIGH: 7,
            BusinessValue.MEDIUM: 5,
            BusinessValue.LOW: 3,
            BusinessValue.MINIMAL: 1,
        }

        base_impact = value_multipliers.get(feature.business_value, 5)

        # Category-specific impact adjustments
        category_impacts = {
            FeatureCategory.SECURITY: 1.3,  # Security has high impact
            FeatureCategory.COMPLIANCE: 1.2,  # Compliance is critical for enterprise
            FeatureCategory.PERFORMANCE: 1.1,  # Performance affects user experience
            FeatureCategory.USABILITY: 1.0,  # Standard impact
            FeatureCategory.INTEGRATION: 1.1,  # Integrations enable broader use
            FeatureCategory.ANALYTICS: 0.9,  # Analytics provide insights
            FeatureCategory.API: 0.8,  # APIs enable ecosystem growth
            FeatureCategory.ADMINISTRATION: 0.7,  # Admin features have indirect impact
            FeatureCategory.MOBILE: 0.9,  # Mobile expands accessibility
            FeatureCategory.AI_ML: 1.4,  # AI features have transformative potential
        }

        return min(10.0, base_impact * category_impacts.get(feature.category, 1.0))

    def _calculate_confidence_score(self, feature: FeatureRequest) -> float:
        """Calculate confidence score (0-10) - certainty of estimates and impact."""
        # Start with base confidence
        confidence = 7.0  # Moderate confidence

        # Adjust based on feature attributes
        if feature.business_impact and len(feature.business_impact) > 100:
            confidence += 1.0  # Detailed business case increases confidence

        if feature.success_metrics and len(feature.success_metrics) >= 3:
            confidence += 1.0  # Clear success metrics increase confidence

        if feature.technical_description:
            confidence += 0.5  # Technical details increase confidence

        if feature.dependencies:
            confidence -= 0.5  # Dependencies decrease confidence

        # Category-specific confidence adjustments
        category_confidence = {
            FeatureCategory.SECURITY: 0.9,  # Security requirements are well understood
            FeatureCategory.COMPLIANCE: 0.9,  # Compliance requirements are clear
            FeatureCategory.PERFORMANCE: 0.8,  # Performance requirements are measurable
            FeatureCategory.USABILITY: 0.8,  # UX can be validated
            FeatureCategory.INTEGRATION: 0.7,  # Integrations have variable complexity
            FeatureCategory.ANALYTICS: 0.8,  # Analytics requirements are definable
            FeatureCategory.API: 0.9,  # API requirements are well specified
            FeatureCategory.ADMINISTRATION: 0.9,  # Admin requirements are clear
            FeatureCategory.MOBILE: 0.7,  # Mobile development has variables
            FeatureCategory.AI_ML: 0.6,  # AI features have higher uncertainty
        }

        confidence *= category_confidence.get(feature.category, 0.8)

        return max(1.0, min(10.0, confidence))

    def _calculate_effort_score(self, feature: FeatureRequest) -> float:
        """Calculate effort score (1-10) - development effort required."""
        # Base effort from complexity assessment
        effort_multipliers = {
            EffortLevel.EXTRA_SMALL: 1,
            EffortLevel.SMALL: 2,
            EffortLevel.MEDIUM: 4,
            EffortLevel.LARGE: 7,
            EffortLevel.EXTRA_LARGE: 9,
            EffortLevel.EPIC: 10,
        }

        base_effort = float(effort_multipliers.get(feature.technical_complexity, 4))

        # Adjust for dependencies
        if feature.dependencies:
            base_effort += len(feature.dependencies) * 0.5

        # Category-specific effort adjustments
        category_efforts = {
            FeatureCategory.SECURITY: 1.2,  # Security features require extra care
            FeatureCategory.COMPLIANCE: 1.1,  # Compliance has documentation overhead
            FeatureCategory.PERFORMANCE: 1.1,  # Performance optimization is complex
            FeatureCategory.USABILITY: 1.0,  # Standard effort
            FeatureCategory.INTEGRATION: 1.3,  # Integrations add complexity
            FeatureCategory.ANALYTICS: 1.1,  # Analytics requires data modeling
            FeatureCategory.API: 1.0,  # Standard API development
            FeatureCategory.ADMINISTRATION: 0.9,  # Admin features are typically simpler
            FeatureCategory.MOBILE: 1.2,  # Mobile development has platform considerations
            FeatureCategory.AI_ML: 1.4,  # AI features require specialized expertise
        }

        return min(10.0, base_effort * category_efforts.get(feature.category, 1.0))

    def _calculate_strategic_alignment(self, feature: FeatureRequest) -> float:
        """Calculate strategic alignment score (0-10)."""
        # Check if feature aligns with strategic initiatives
        if any(
            init in feature.title.lower() or init in feature.description.lower()
            for init in self.prioritization_criteria.strategic_initiatives
        ):
            return 9.0

        # Category-based strategic alignment
        strategic_categories = {
            FeatureCategory.SECURITY: 8.0,
            FeatureCategory.COMPLIANCE: 9.0,
            FeatureCategory.AI_ML: 7.0,
        }

        return strategic_categories.get(feature.category, 5.0)

    def _calculate_customer_satisfaction_impact(self, feature: FeatureRequest) -> float:
        """Calculate customer satisfaction impact (0-10)."""
        # Features that directly improve user experience score higher
        satisfaction_categories = {
            FeatureCategory.USABILITY: 8.0,
            FeatureCategory.PERFORMANCE: 7.0,
            FeatureCategory.SECURITY: 6.0,
            FeatureCategory.ANALYTICS: 5.0,
            FeatureCategory.INTEGRATION: 6.0,
        }

        return satisfaction_categories.get(feature.category, 4.0)

    def _calculate_compliance_security_value(self, feature: FeatureRequest) -> float:
        """Calculate compliance and security value (0-10)."""
        # Security and compliance features have high enterprise value
        compliance_categories = {
            FeatureCategory.SECURITY: 10.0,
            FeatureCategory.COMPLIANCE: 9.0,
            FeatureCategory.ADMINISTRATION: 3.0,  # May include compliance features
        }

        return compliance_categories.get(feature.category, 2.0)

    async def get_prioritized_features(
        self,
        limit: int = 50,
        min_score: float = 0.0,
        category_filter: Optional[FeatureCategory] = None,
        status_filter: Optional[List[FeatureStatus]] = None,
    ) -> List[FeatureRequest]:
        """
        Get prioritized list of feature requests.

        Args:
            limit: Maximum number of features to return
            min_score: Minimum priority score
            category_filter: Filter by category
            status_filter: Filter by status

        Returns:
            Prioritized list of feature requests
        """
        features = list(self.feature_requests.values())

        # Apply filters
        if category_filter:
            features = [f for f in features if f.category == category_filter]

        if status_filter:
            features = [f for f in features if f.status in status_filter]

        # Filter by minimum score
        features = [f for f in features if f.priority_score >= min_score]

        # Sort by priority score (descending)
        features.sort(key=lambda f: f.priority_score, reverse=True)

        return features[:limit]

    async def create_roadmap_milestone(
        self,
        name: str,
        description: str,
        target_date: datetime,
        theme: str,
        planned_features: List[str],
        key_objectives: List[str],
    ) -> str:
        """
        Create a new roadmap milestone.

        Args:
            name: Milestone name
            description: Milestone description
            target_date: Target completion date
            theme: Strategic theme
            planned_features: List of feature IDs
            key_objectives: Key objectives

        Returns:
            Milestone ID
        """
        milestone_id = f"milestone_{int(datetime.utcnow().timestamp())}"

        milestone = RoadmapMilestone(
            id=milestone_id,
            name=name,
            description=description,
            target_date=target_date,
            theme=theme,
            planned_features=planned_features,
            key_objectives=key_objectives,
        )

        self.roadmap_milestones[milestone_id] = milestone

        # Update feature targets
        for feature_id in planned_features:
            if feature_id in self.feature_requests:
                self.feature_requests[feature_id].target_release = name

        self.logger.info(f"Created roadmap milestone: {milestone_id} - {name}")
        return milestone_id

    async def create_iteration_plan(
        self,
        name: str,
        start_date: datetime,
        end_date: datetime,
        team_capacity_days: int,
        planned_features: List[str],
    ) -> str:
        """
        Create a new iteration plan.

        Args:
            name: Iteration name
            start_date: Iteration start date
            end_date: Iteration end date
            team_capacity_days: Team capacity in person-days
            planned_features: List of feature IDs to include

        Returns:
            Iteration plan ID
        """
        iteration_id = f"iteration_{int(datetime.utcnow().timestamp())}"

        iteration = IterationPlan(
            id=iteration_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            team_capacity_days=team_capacity_days,
            planned_features=planned_features,
        )

        self.iteration_plans[iteration_id] = iteration

        # Update feature status
        for feature_id in planned_features:
            if feature_id in self.feature_requests:
                self.feature_requests[feature_id].status = FeatureStatus.PLANNED
                self.feature_requests[feature_id].target_release = name

        self.logger.info(f"Created iteration plan: {iteration_id} - {name}")
        return iteration_id

    async def get_roadmap_view(self) -> Dict[str, Any]:
        """
        Get a comprehensive roadmap view.

        Returns:
            Roadmap data including milestones, features, and timelines
        """
        # Get all milestones sorted by date
        milestones = list(self.roadmap_milestones.values())
        milestones.sort(key=lambda m: m.target_date)

        # Calculate roadmap metrics
        total_features = sum(len(m.planned_features) for m in milestones)
        completed_features = sum(
            len(
                [
                    f
                    for f in m.planned_features
                    if f in self.feature_requests and self.feature_requests[f].is_completed
                ]
            )
            for m in milestones
        )

        roadmap_completion = (
            (completed_features / total_features * 100) if total_features > 0 else 0
        )

        return {
            "milestones": [
                {
                    "id": m.id,
                    "name": m.name,
                    "theme": m.theme,
                    "target_date": m.target_date.isoformat(),
                    "status": m.status,
                    "progress_percentage": m.progress_percentage,
                    "planned_features_count": len(m.planned_features),
                    "completed_features_count": len(
                        [
                            f
                            for f in m.planned_features
                            if f in self.feature_requests and self.feature_requests[f].is_completed
                        ]
                    ),
                }
                for m in milestones
            ],
            "summary": {
                "total_milestones": len(milestones),
                "total_features": total_features,
                "completed_features": completed_features,
                "roadmap_completion_percentage": roadmap_completion,
                "next_milestone": milestones[0].name if milestones else None,
                "next_milestone_date": (
                    milestones[0].target_date.isoformat() if milestones else None
                ),
            },
            "themes": self._get_theme_breakdown(milestones),
        }

    def _get_theme_breakdown(self, milestones: List[RoadmapMilestone]) -> Dict[str, Any]:
        """Get breakdown of features by theme."""
        themes = {}
        for milestone in milestones:
            theme = milestone.theme
            if theme not in themes:
                themes[theme] = {"milestones": 0, "features": 0, "completed_features": 0}

            themes[theme]["milestones"] += 1
            themes[theme]["features"] += len(milestone.planned_features)
            themes[theme]["completed_features"] += len(
                [
                    f
                    for f in milestone.planned_features
                    if f in self.feature_requests and self.feature_requests[f].is_completed
                ]
            )

        return themes

    async def get_iteration_backlog(self) -> List[FeatureRequest]:
        """
        Get the current iteration backlog (prioritized features not yet planned).

        Returns:
            List of features ready for iteration planning
        """
        backlog = [
            f
            for f in self.feature_requests.values()
            if f.status in [FeatureStatus.REVIEWED, FeatureStatus.PRIORITIZED]
            and f.priority_score >= 50  # High priority features
        ]

        # Sort by priority score
        backlog.sort(key=lambda f: f.priority_score, reverse=True)

        return backlog[:20]  # Top 20 backlog items

    async def analyze_feature_impact(self, feature_id: str) -> Dict[str, Any]:
        """
        Analyze the business and technical impact of a feature.

        Args:
            feature_id: Feature ID to analyze

        Returns:
            Detailed impact analysis
        """
        feature = self.feature_requests.get(feature_id)
        if not feature:
            return {}

        # Calculate business impact metrics
        business_impact = {
            "revenue_potential": self._estimate_revenue_impact(feature),
            "customer_satisfaction_improvement": self._estimate_satisfaction_impact(feature),
            "competitive_advantage": self._assess_competitive_advantage(feature),
            "strategic_alignment_score": self._calculate_strategic_alignment(feature),
        }

        # Calculate technical impact metrics
        technical_impact = {
            "development_effort_days": self._estimate_development_effort(feature),
            "technical_risk_level": self._assess_technical_risk(feature),
            "maintenance_complexity": self._assess_maintenance_complexity(feature),
            "scalability_impact": self._assess_scalability_impact(feature),
        }

        # Calculate overall ROI
        dev_effort = technical_impact.get("development_effort_days", 15)
        revenue_potential = business_impact.get("revenue_potential", 100000)
        development_cost = (
            dev_effort if isinstance(dev_effort, (int, float)) else 15
        ) * 800  # $800/day avg
        annual_benefit = (
            revenue_potential if isinstance(revenue_potential, (int, float)) else 100000
        ) * 0.3  # 30% annual benefit
        roi_percentage = (
            ((annual_benefit - development_cost) / development_cost * 100)
            if development_cost > 0
            else 0
        )

        return {
            "feature_id": feature_id,
            "business_impact": business_impact,
            "technical_impact": technical_impact,
            "overall_assessment": {
                "roi_percentage": roi_percentage,
                "payback_months": (
                    development_cost / (annual_benefit / 12) if annual_benefit > 0 else 999
                ),
                "recommendation": (
                    "APPROVE"
                    if roi_percentage > 50
                    else "REVIEW" if roi_percentage > 0 else "REJECT"
                ),
                "confidence_level": "HIGH" if feature.success_metrics else "MEDIUM",
            },
        }

    def _estimate_revenue_impact(self, feature: FeatureRequest) -> float:
        """Estimate annual revenue impact."""
        # Simplified revenue estimation based on category and business value
        base_impact = {
            BusinessValue.TRANSFORMATIONAL: 500000,
            BusinessValue.HIGH: 250000,
            BusinessValue.MEDIUM: 100000,
            BusinessValue.LOW: 25000,
            BusinessValue.MINIMAL: 5000,
        }

        category_multipliers = {
            FeatureCategory.AI_ML: 1.5,
            FeatureCategory.INTEGRATION: 1.3,
            FeatureCategory.SECURITY: 1.2,
            FeatureCategory.PERFORMANCE: 1.1,
        }

        base = base_impact.get(feature.business_value, 50000)
        multiplier = category_multipliers.get(feature.category, 1.0)

        return base * multiplier

    def _estimate_satisfaction_impact(self, feature: FeatureRequest) -> float:
        """Estimate customer satisfaction improvement (0-10)."""
        base_satisfaction = {
            BusinessValue.TRANSFORMATIONAL: 9.0,
            BusinessValue.HIGH: 7.0,
            BusinessValue.MEDIUM: 5.0,
            BusinessValue.LOW: 3.0,
            BusinessValue.MINIMAL: 1.0,
        }

        return base_satisfaction.get(feature.business_value, 4.0)

    def _assess_competitive_advantage(self, feature: FeatureRequest) -> str:
        """Assess competitive advantage potential."""
        if feature.business_value == BusinessValue.TRANSFORMATIONAL:
            return "GAME_CHANGER"
        elif feature.business_value == BusinessValue.HIGH:
            return "STRONG_ADVANTAGE"
        elif feature.category in [FeatureCategory.AI_ML, FeatureCategory.SECURITY]:
            return "MODERATE_ADVANTAGE"
        else:
            return "MINIMAL_ADVANTAGE"

    def _estimate_development_effort(self, feature: FeatureRequest) -> float:
        """Estimate development effort in days."""
        effort_days = {
            EffortLevel.EXTRA_SMALL: 2,
            EffortLevel.SMALL: 5,
            EffortLevel.MEDIUM: 15,
            EffortLevel.LARGE: 45,
            EffortLevel.EXTRA_LARGE: 90,
            EffortLevel.EPIC: 180,
        }

        return effort_days.get(feature.technical_complexity, 15)

    def _assess_technical_risk(self, feature: FeatureRequest) -> str:
        """Assess technical risk level."""
        if feature.category in [FeatureCategory.AI_ML, FeatureCategory.SECURITY]:
            return "HIGH"
        elif feature.technical_complexity in [EffortLevel.EPIC, EffortLevel.EXTRA_LARGE]:
            return "HIGH"
        elif len(feature.dependencies) > 3:
            return "MEDIUM"
        else:
            return "LOW"

    def _assess_maintenance_complexity(self, feature: FeatureRequest) -> str:
        """Assess maintenance complexity."""
        if feature.category == FeatureCategory.AI_ML:
            return "HIGH"
        elif feature.technical_complexity in [EffortLevel.EPIC]:
            return "HIGH"
        elif feature.category in [FeatureCategory.INTEGRATION, FeatureCategory.API]:
            return "MEDIUM"
        else:
            return "LOW"

    def _assess_scalability_impact(self, feature: FeatureRequest) -> str:
        """Assess scalability impact."""
        if feature.category == FeatureCategory.PERFORMANCE:
            return "HIGH_POSITIVE"
        elif feature.category == FeatureCategory.AI_ML:
            return "HIGH_NEGATIVE"
        elif feature.technical_complexity in [EffortLevel.EPIC]:
            return "MEDIUM_NEGATIVE"
        else:
            return "NEUTRAL"
