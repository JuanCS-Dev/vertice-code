"""
Enterprise Pilot Management Package
===================================

Comprehensive management system for enterprise pilot programs.

This package provides:
- Strategic customer selection and qualification
- Pilot program lifecycle management
- Success manager assignment and tracking
- Onboarding workflow automation
- Progress monitoring and reporting

Part of the Enterprise Pilot Launch (Fase 2 Mês 7).
"""

__version__ = "1.0.0"

from .pilot_selector import (
    PilotCustomerSelector,
    PilotProgramManager,
    PilotProgram,
    PilotCustomerProfile,
    SuccessManager,
    PilotSelectionCriteria,
    PilotStatus,
    CustomerTier,
    IndustrySector,
    ContactInfo,
)

from .iteration_manager import (
    WeeklyIterationManager,
    WeeklyIteration,
    IterationGoal,
    FeedbackEntry,
    SuccessMetricsSnapshot,
    IterationPlanningTemplate,
    IterationStatus,
    FeedbackType,
    MetricTrend,
)

from .onboarding_playbooks import OnboardingPlaybookManager, OnboardingPlaybook, OnboardingMilestone

from .health_monitoring import (
    HealthMonitoringEngine,
    HealthMetric,
    HealthCheckResult,
    CustomerHealthProfile,
    HealthStatus,
    RiskLevel,
)

from .session_management import SessionManager, OnboardingSession

from .customer_success_manager import CustomerSuccessManager

from .feature_requests import (
    FeatureRequestManager,
    FeatureRequest,
    FeatureStatus,
    FeatureCategory,
    BusinessValue,
    EffortLevel,
    CustomerSegment,
)

from .feature_prioritization import (
    PrioritizationEngine,
    PrioritizationCriteria,
)

from .roadmap_management import (
    RoadmapManager,
    RoadmapMilestone,
)

from .iteration_planning import (
    IterationPlanningManager,
    IterationPlan,
)

__all__ = [
    # Pilot Selection
    "PilotCustomerSelector",
    "PilotProgramManager",
    "PilotProgram",
    "PilotCustomerProfile",
    "SuccessManager",
    "PilotSelectionCriteria",
    "PilotStatus",
    "CustomerTier",
    "IndustrySector",
    "ContactInfo",
    # Iteration Management
    "WeeklyIterationManager",
    "WeeklyIteration",
    "IterationGoal",
    "FeedbackEntry",
    "SuccessMetricsSnapshot",
    "IterationPlanningTemplate",
    "IterationStatus",
    "FeedbackType",
    "MetricTrend",
    # Onboarding Playbooks
    "OnboardingPlaybookManager",
    "OnboardingPlaybook",
    "OnboardingMilestone",
    # Health Monitoring
    "HealthMonitoringEngine",
    "HealthMetric",
    "HealthCheckResult",
    "CustomerHealthProfile",
    "HealthStatus",
    "RiskLevel",
    # Session Management
    "SessionManager",
    "OnboardingSession",
    # Customer Success Manager
    "CustomerSuccessManager",
    # Product Iteration
    "FeatureRequestManager",
    "FeatureRequest",
    "PrioritizationEngine",
    "PrioritizationCriteria",
    "RoadmapManager",
    "RoadmapMilestone",
    "IterationPlanningManager",
    "IterationPlan",
    "FeatureStatus",
    "FeatureCategory",
    "BusinessValue",
    "EffortLevel",
    "CustomerSegment",
]
