"""
Feature Prioritization Engine
============================

Advanced feature prioritization using RICE scoring and enterprise factors.

This module provides:
- RICE scoring algorithm implementation
- Enterprise-specific prioritization factors
- Automated priority calculation and ranking

Part of the Product Iteration Engine.
"""

from __future__ import annotations

import logging
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from .feature_requests import (
    FeatureRequest,
    BusinessValue,
    EffortLevel,
    CustomerSegment,
    FeatureCategory,
)


logger = logging.getLogger(__name__)


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
        return v


class PrioritizationEngine:
    """
    Advanced feature prioritization engine using RICE scoring.
    """

    def __init__(self, criteria: Optional[PrioritizationCriteria] = None) -> None:
        """Initialize the prioritization engine."""
        self.criteria = criteria or PrioritizationCriteria()
        self.logger = logging.getLogger(f"{__name__}.PrioritizationEngine")

    async def prioritize_feature(self, feature: FeatureRequest) -> float:
        """
        Calculate priority score for a feature using RICE methodology.

        Args:
            feature: Feature request to prioritize

        Returns:
            Priority score (0-100)
        """
        # RICE components
        reach_score = self._calculate_reach_score(feature)
        impact_score = self._calculate_impact_score(feature)
        confidence_score = self._calculate_confidence_score(feature)
        effort_score = self._calculate_effort_score(feature)

        # Enterprise-specific factors
        strategic_score = self._calculate_strategic_alignment(feature)
        satisfaction_score = self._calculate_customer_satisfaction_impact(feature)
        compliance_score = self._calculate_compliance_security_value(feature)

        # Weighted calculation
        rice_score = (
            reach_score * self.criteria.reach_weight
            + impact_score * self.criteria.impact_weight
            + confidence_score * self.criteria.confidence_weight
            + (1 / effort_score) * self.criteria.effort_weight  # Lower effort = higher priority
        )

        enterprise_score = (
            strategic_score * self.criteria.strategic_alignment_weight
            + satisfaction_score * self.criteria.customer_satisfaction_weight
            + compliance_score * self.criteria.compliance_security_weight
        )

        # Final priority score (0-100 scale)
        priority_score = min(100.0, (rice_score * 0.7 + enterprise_score * 0.3) * 10)

        self.logger.debug(f"Calculated priority score for {feature.id}: {priority_score}")
        return priority_score

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

        # Adjust based on feature category
        category_multipliers = {
            FeatureCategory.SECURITY: 1.2,  # Security affects everyone
            FeatureCategory.COMPLIANCE: 1.1,  # Compliance is enterprise-wide
            FeatureCategory.PERFORMANCE: 1.1,  # Performance affects all users
            FeatureCategory.USABILITY: 1.0,  # Standard reach
            FeatureCategory.INTEGRATION: 0.9,  # Depends on integration usage
            FeatureCategory.ANALYTICS: 0.8,  # Analytics have limited reach
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
        confidence = 7.0  # Base confidence

        # Adjust based on feature attributes
        if feature.business_impact and len(feature.business_impact) > 100:
            confidence += 1.0

        if feature.success_metrics and len(feature.success_metrics) >= 3:
            confidence += 1.0

        if feature.technical_description:
            confidence += 0.5

        if feature.dependencies:
            confidence -= 0.5

        # Category-specific confidence adjustments
        category_confidence = {
            FeatureCategory.SECURITY: 0.9,
            FeatureCategory.COMPLIANCE: 0.9,
            FeatureCategory.PERFORMANCE: 0.8,
            FeatureCategory.USABILITY: 0.8,
            FeatureCategory.INTEGRATION: 0.7,
            FeatureCategory.ANALYTICS: 0.8,
            FeatureCategory.API: 0.9,
            FeatureCategory.ADMINISTRATION: 0.9,
            FeatureCategory.MOBILE: 0.7,
            FeatureCategory.AI_ML: 0.6,
        }

        confidence *= category_confidence.get(feature.category, 0.8)

        return max(1.0, min(10.0, confidence))

    def _calculate_effort_score(self, feature: FeatureRequest) -> float:
        """Calculate effort score (1-10) - development effort required."""
        effort_multipliers = {
            EffortLevel.EXTRA_SMALL: 1,
            EffortLevel.SMALL: 2,
            EffortLevel.MEDIUM: 4,
            EffortLevel.LARGE: 7,
            EffortLevel.EXTRA_LARGE: 9,
            EffortLevel.EPIC: 10,
        }

        base_effort = effort_multipliers.get(feature.technical_complexity, 4)

        # Adjust for dependencies
        if feature.dependencies:
            base_effort += len(feature.dependencies) * 0.5

        # Category-specific effort adjustments
        category_efforts = {
            FeatureCategory.SECURITY: 1.2,
            FeatureCategory.COMPLIANCE: 1.1,
            FeatureCategory.PERFORMANCE: 1.1,
            FeatureCategory.USABILITY: 1.0,
            FeatureCategory.INTEGRATION: 1.3,
            FeatureCategory.ANALYTICS: 1.1,
            FeatureCategory.API: 1.0,
            FeatureCategory.ADMINISTRATION: 0.9,
            FeatureCategory.MOBILE: 1.2,
            FeatureCategory.AI_ML: 1.4,
        }

        return min(10.0, base_effort * category_efforts.get(feature.category, 1.0))

    def _calculate_strategic_alignment(self, feature: FeatureRequest) -> float:
        """Calculate strategic alignment score (0-10)."""
        # Check if feature aligns with strategic initiatives
        if any(
            init in feature.title.lower() or init in feature.description.lower()
            for init in self.criteria.strategic_initiatives
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
        compliance_categories = {
            FeatureCategory.SECURITY: 10.0,
            FeatureCategory.COMPLIANCE: 9.0,
            FeatureCategory.ADMINISTRATION: 3.0,
        }

        return compliance_categories.get(feature.category, 2.0)
