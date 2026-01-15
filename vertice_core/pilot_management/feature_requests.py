"""
Feature Request Management
==========================

Core feature request data models and basic management.

This module provides:
- Feature request data structures
- Status tracking and updates
- Basic feature lifecycle management

Part of the Product Iteration Engine.
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


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


class FeatureRequestManager:
    """
    Basic manager for feature requests.
    """

    def __init__(self) -> None:
        """Initialize the feature request manager."""
        self.feature_requests: Dict[str, FeatureRequest] = {}
        self.logger = logging.getLogger(f"{__name__}.FeatureRequestManager")

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

        self.logger.info(f"Submitted feature request: {feature_id} - {title}")
        return feature_id

    async def update_feature_status(self, feature_id: str, status: FeatureStatus) -> bool:
        """
        Update the status of a feature request.

        Args:
            feature_id: Feature identifier
            status: New status

        Returns:
            True if update was successful
        """
        feature = self.feature_requests.get(feature_id)
        if not feature:
            return False

        feature.status = status
        if status == FeatureStatus.COMPLETED:
            feature.completion_date = datetime.utcnow()

        self.logger.info(f"Updated feature {feature_id} status to {status.value}")
        return True
