"""
Enterprise Billing & Analytics Module - Monetization enterprise-grade.

Implements agentic AI pricing models, advanced analytics, and billing automation
for enterprise-scale operations. Based on 2026 enterprise SaaS research.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from vertice_core.agents.context.types import ExecutionResult


class PricingTier(str, Enum):
    """Enterprise pricing tiers based on 2026 market research."""

    STARTUP = "startup"  # $99/month - 10 users, 100K tokens
    PROFESSIONAL = "professional"  # $499/month - 50 users, 500K tokens
    ENTERPRISE = "enterprise"  # $1,999/month - 200 users, 2M tokens
    ENTERPRISE_PLUS = "enterprise_plus"  # Custom pricing
    ENTERPRISE_ELITE = "enterprise_elite"  # Strategic accounts


class PricingModel(str, Enum):
    """Pricing models for 2026 enterprise SaaS."""

    USAGE_BASED = "usage_based"  # Traditional usage-based
    VALUE_BASED = "value_based"  # ROI-driven pricing
    OUTCOME_BASED = "outcome_based"  # Success/outcome metrics
    HYBRID = "hybrid"  # Mix of models
    ENTERPRISE_CUSTOM = "enterprise_custom"  # Fully negotiated


class BillingCycle(str, Enum):
    """Billing cycle options."""

    MONTHLY = "monthly"
    ANNUALLY = "annually"  # 20% discount
    QUARTERLY = "quarterly"


class UsageType(str, Enum):
    """Types of usage that can be billed."""

    AI_TOKENS = "ai_tokens"  # LLM API calls
    ACTIVE_USERS = "active_users"  # Monthly active users
    STORAGE_GB = "storage_gb"  # Data storage
    API_CALLS = "api_calls"  # REST API usage
    AGENT_EXECUTIONS = "agent_executions"  # Agent runs
    CODE_GENERATIONS = "code_generations"  # Code output


@dataclass
class PricingPlan:
    """Enterprise pricing plan with usage tiers and value-based features."""

    # Required fields (no defaults)
    tier: PricingTier
    name: str
    description: str
    base_price_monthly: float
    max_users: int
    max_ai_tokens: int  # Monthly
    max_storage_gb: int
    max_api_calls: int  # Monthly

    # Optional fields (with defaults)
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    pricing_model: PricingModel = PricingModel.USAGE_BASED

    # Value-Based Pricing Features (2026)
    roi_guarantee: Optional[float] = None  # ROI percentage guarantee
    outcome_metrics: List[str] = field(default_factory=list)  # Success metrics tracked
    value_multipliers: Dict[str, float] = field(default_factory=dict)  # Value-based adjustments

    # Enterprise features
    custom_sla: bool = False
    priority_support: bool = False

    # Overage pricing per unit
    overage_ai_tokens_per_1k: float = 0.02  # $0.02 per 1K tokens
    overage_storage_per_gb: float = 0.50  # $0.50 per GB/month
    overage_api_calls_per_1k: float = 0.01  # $0.01 per 1K calls

    # Features included
    features: List[str] = field(default_factory=list)

    # Enterprise-specific
    custom_contract: bool = False
    white_glove_onboarding: bool = False
    dedicated_success_manager: bool = False
    custom_integrations: bool = False

    def calculate_monthly_cost(self, usage: Dict[UsageType, int]) -> float:
        """Calculate monthly cost including overages."""
        base_cost = self.base_price_monthly

        # Calculate overages
        overage_cost = 0.0

        # AI tokens overage
        ai_tokens_used = usage.get(UsageType.AI_TOKENS, 0)
        if ai_tokens_used > self.max_ai_tokens:
            excess_tokens = ai_tokens_used - self.max_ai_tokens
            overage_cost += (excess_tokens / 1000) * self.overage_ai_tokens_per_1k

        # Storage overage
        storage_used = usage.get(UsageType.STORAGE_GB, 0)
        if storage_used > self.max_storage_gb:
            excess_storage = storage_used - self.max_storage_gb
            overage_cost += excess_storage * self.overage_storage_per_gb

        # API calls overage
        api_calls_used = usage.get(UsageType.API_CALLS, 0)
        if api_calls_used > self.max_api_calls:
            excess_calls = api_calls_used - self.max_api_calls
            overage_cost += (excess_calls / 1000) * self.overage_api_calls_per_1k

        return base_cost + overage_cost

    def calculate_value_based_cost(
        self, usage: Dict[UsageType, int], outcomes: Dict[str, Any]
    ) -> float:
        """
        Calculate cost based on value delivered and outcomes achieved (2026 model).

        Args:
            usage: Standard usage metrics
            outcomes: Business outcomes achieved (ROI, efficiency gains, etc.)

        Returns:
            Value-adjusted monthly cost
        """
        base_cost = self.calculate_monthly_cost(usage)

        if self.pricing_model == PricingModel.VALUE_BASED:
            # Apply value multipliers based on outcomes
            value_multiplier = 1.0

            for outcome_key, outcome_value in outcomes.items():
                if outcome_key in self.value_multipliers:
                    multiplier = self.value_multipliers[outcome_key]

                    # Apply outcome-based adjustments
                    if outcome_key == "roi_achieved" and outcome_value > 100:
                        # Higher ROI = willingness to pay more
                        value_multiplier *= min(1.5, 1.0 + (outcome_value - 100) * 0.005)
                    elif outcome_key == "efficiency_gain" and outcome_value > 20:
                        # Significant efficiency gains justify premium
                        value_multiplier *= min(1.3, 1.0 + (outcome_value - 20) * 0.01)

            base_cost *= value_multiplier

        return base_cost

    def get_roi_calculator_url(self) -> Optional[str]:
        """Get URL for ROI calculator (2026 enterprise requirement)."""
        if self.roi_guarantee:
            return f"/roi-calculator/{self.tier.value}"
        return None


@dataclass
class UsageRecord:
    """Individual usage record for billing."""

    tenant_id: str
    usage_type: UsageType
    quantity: int
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    # For AI-specific tracking
    model_used: Optional[str] = None
    agent_type: Optional[str] = None
    success: bool = True


@dataclass
class BillingPeriod:
    """Billing period with usage summary."""

    tenant_id: str
    period_start: datetime
    period_end: datetime
    pricing_plan: PricingPlan

    # Usage summary
    usage_summary: Dict[UsageType, int] = field(default_factory=dict)

    # Calculated costs
    base_cost: float = 0.0
    overage_cost: float = 0.0
    total_cost: float = 0.0

    # Status
    status: str = "pending"  # pending, invoiced, paid
    invoice_id: Optional[str] = None

    def add_usage(self, record: UsageRecord) -> None:
        """Add usage record to period."""
        if record.usage_type not in self.usage_summary:
            self.usage_summary[record.usage_type] = 0
        self.usage_summary[record.usage_type] += record.quantity

    def calculate_costs(self) -> None:
        """Calculate billing costs for this period."""
        self.base_cost = self.pricing_plan.base_price_monthly
        overage_cost = 0.0

        # Calculate overages
        for usage_type, quantity in self.usage_summary.items():
            if usage_type == UsageType.AI_TOKENS and quantity > self.pricing_plan.max_ai_tokens:
                excess = quantity - self.pricing_plan.max_ai_tokens
                overage_cost += (excess / 1000) * self.pricing_plan.overage_ai_tokens_per_1k
            elif usage_type == UsageType.STORAGE_GB and quantity > self.pricing_plan.max_storage_gb:
                excess = quantity - self.pricing_plan.max_storage_gb
                overage_cost += excess * self.pricing_plan.overage_storage_per_gb
            elif usage_type == UsageType.API_CALLS and quantity > self.pricing_plan.max_api_calls:
                excess = quantity - self.pricing_plan.max_api_calls
                overage_cost += (excess / 1000) * self.pricing_plan.overage_api_calls_per_1k

        self.overage_cost = overage_cost
        self.total_cost = self.base_cost + self.overage_cost


@dataclass
class AnalyticsMetrics:
    """Real-time analytics metrics for enterprise dashboard."""

    tenant_id: str
    period: str  # "daily", "weekly", "monthly"

    # Usage metrics
    total_ai_tokens: int = 0
    total_api_calls: int = 0
    active_users: int = 0
    storage_used_gb: float = 0.0

    # Performance metrics
    avg_response_time_ms: float = 0.0
    success_rate_percent: float = 100.0
    agent_execution_count: int = 0

    # Revenue metrics
    mrr: float = 0.0  # Monthly Recurring Revenue
    overage_revenue: float = 0.0
    total_revenue: float = 0.0

    # Predictive metrics
    projected_usage_next_month: Dict[UsageType, int] = field(default_factory=dict)
    churn_risk_score: float = 0.0  # 0-100, higher = more likely to churn
    expansion_opportunity_score: float = 0.0  # 0-100, higher = more likely to expand

    # Agent-specific metrics
    agent_performance: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dashboard_format(self) -> Dict[str, Any]:
        """Convert to dashboard-friendly format."""
        return {
            "usage": {
                "ai_tokens": self.total_ai_tokens,
                "api_calls": self.total_api_calls,
                "active_users": self.active_users,
                "storage_gb": self.storage_used_gb,
            },
            "performance": {
                "avg_response_time_ms": self.avg_response_time_ms,
                "success_rate": self.success_rate_percent,
                "agent_executions": self.agent_execution_count,
            },
            "revenue": {
                "mrr": self.mrr,
                "overage": self.overage_revenue,
                "total": self.total_revenue,
            },
            "predictions": {
                "next_month_usage": self.projected_usage_next_month,
                "churn_risk": self.churn_risk_score,
                "expansion_potential": self.expansion_opportunity_score,
            },
            "agents": self.agent_performance,
        }


__all__ = [
    "PricingTier",
    "BillingCycle",
    "UsageType",
    "PricingPlan",
    "UsageRecord",
    "BillingPeriod",
    "AnalyticsMetrics",
]
