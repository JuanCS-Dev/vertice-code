"""
Enterprise Billing & Analytics Module - Complete monetization solution.

This module provides:
- Enterprise pricing models with usage-based billing
- Real-time analytics dashboards
- Automated billing with Stripe integration
- Tax compliance for global enterprise customers
- Revenue analytics and predictive insights
"""

from .analytics import AnalyticsEngine
from .billing import BillingEngine, Invoice, InvoiceItem, TaxInfo
from .plans import (
    ENTERPRISE_PRICING_PLANS,
    calculate_annual_discount,
    find_best_fit_plan,
    get_all_plans,
    get_pricing_plan,
)
from .types import (
    AnalyticsMetrics,
    BillingCycle,
    BillingPeriod,
    PricingPlan,
    PricingTier,
    UsageRecord,
    UsageType,
)


__all__ = [
    # Core engines
    "AnalyticsEngine",
    "BillingEngine",
    # Data structures
    "AnalyticsMetrics",
    "BillingCycle",
    "BillingPeriod",
    "PricingPlan",
    "PricingTier",
    "UsageRecord",
    "UsageType",
    "Invoice",
    "InvoiceItem",
    "TaxInfo",
    # Pricing utilities
    "ENTERPRISE_PRICING_PLANS",
    "get_pricing_plan",
    "get_all_plans",
    "calculate_annual_discount",
    "find_best_fit_plan",
]
