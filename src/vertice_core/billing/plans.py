"""
Enterprise Pricing Plans - Pre-configured plans for 2026 enterprise market.

Based on extensive research of enterprise SaaS pricing models,
focusing on agentic AI and usage-based billing.
"""

from .types import BillingCycle, PricingPlan, PricingTier, UsageType


# Pre-configured enterprise pricing plans
ENTERPRISE_PRICING_PLANS = {
    PricingTier.STARTUP: PricingPlan(
        tier=PricingTier.STARTUP,
        name="Startup",
        description="Perfect for small teams getting started with AI-powered development",
        base_price_monthly=99.0,
        billing_cycle=BillingCycle.MONTHLY,
        max_users=10,
        max_ai_tokens=100_000,  # 100K tokens/month
        max_storage_gb=5,
        max_api_calls=10_000,
        features=[
            "AI-powered code assistance",
            "Basic agent orchestration",
            "5GB cloud storage",
            "Email support",
            "Basic analytics",
        ],
        white_glove_onboarding=False,
        dedicated_success_manager=False,
        custom_integrations=False,
    ),
    PricingTier.PROFESSIONAL: PricingPlan(
        tier=PricingTier.PROFESSIONAL,
        name="Professional",
        description="For growing teams that need advanced AI capabilities and collaboration",
        base_price_monthly=499.0,
        billing_cycle=BillingCycle.MONTHLY,
        max_users=50,
        max_ai_tokens=500_000,  # 500K tokens/month
        max_storage_gb=25,
        max_api_calls=50_000,
        features=[
            "Advanced AI agents",
            "Multi-agent orchestration",
            "25GB cloud storage",
            "Priority email support",
            "Advanced analytics dashboard",
            "API access",
            "Custom workflows",
        ],
        white_glove_onboarding=True,
        dedicated_success_manager=False,
        custom_integrations=False,
    ),
    PricingTier.ENTERPRISE: PricingPlan(
        tier=PricingTier.ENTERPRISE,
        name="Enterprise",
        description="Full enterprise-grade AI platform with advanced security and compliance",
        base_price_monthly=1999.0,
        billing_cycle=BillingCycle.MONTHLY,
        max_users=200,
        max_ai_tokens=2_000_000,  # 2M tokens/month
        max_storage_gb=100,
        max_api_calls=200_000,
        features=[
            "All Professional features",
            "Enterprise security (SOC 2, GDPR)",
            "100GB cloud storage",
            "24/7 phone support",
            "Dedicated success manager",
            "Custom integrations",
            "Advanced compliance tools",
            "Audit logs",
            "SAML SSO",
            "Advanced RBAC",
        ],
        white_glove_onboarding=True,
        dedicated_success_manager=True,
        custom_integrations=True,
    ),
    PricingTier.ENTERPRISE_PLUS: PricingPlan(
        tier=PricingTier.ENTERPRISE_PLUS,
        name="Enterprise Plus",
        description="Custom enterprise solution with enhanced limits and premium support",
        base_price_monthly=4999.0,  # Custom pricing typically starts here
        billing_cycle=BillingCycle.MONTHLY,
        max_users=500,
        max_ai_tokens=10_000_000,  # 10M tokens/month
        max_storage_gb=500,
        max_api_calls=1_000_000,
        features=[
            "All Enterprise features",
            "500GB cloud storage",
            "Custom AI model training",
            "On-premise deployment option",
            "Custom SLAs",
            "Advanced reporting",
            "Technical account management",
        ],
        custom_contract=True,
        white_glove_onboarding=True,
        dedicated_success_manager=True,
        custom_integrations=True,
    ),
    PricingTier.ENTERPRISE_ELITE: PricingPlan(
        tier=PricingTier.ENTERPRISE_ELITE,
        name="Enterprise Elite",
        description="Strategic partnership tier with unlimited potential and white-glove service",
        base_price_monthly=9999.0,  # Premium custom pricing
        billing_cycle=BillingCycle.ANNUALLY,  # Annual contracts typical
        max_users=1000,  # Essentially unlimited with custom terms
        max_ai_tokens=50_000_000,  # 50M tokens/month base
        max_storage_gb=2000,  # 2TB
        max_api_calls=5_000_000,  # 5M calls/month
        features=[
            "All Enterprise Plus features",
            "Unlimited scaling",
            "Custom AI model development",
            "Dedicated engineering team",
            "Strategic roadmap influence",
            "Executive sponsorship",
            "Custom compliance frameworks",
        ],
        custom_contract=True,
        white_glove_onboarding=True,
        dedicated_success_manager=True,
        custom_integrations=True,
    ),
}


def get_pricing_plan(tier: PricingTier) -> PricingPlan:
    """Get pricing plan by tier."""
    return ENTERPRISE_PRICING_PLANS[tier]


def get_all_plans() -> dict[PricingTier, PricingPlan]:
    """Get all available pricing plans."""
    return ENTERPRISE_PRICING_PLANS.copy()


def calculate_annual_discount(plan: PricingPlan) -> float:
    """Calculate annual billing discount."""
    if plan.billing_cycle == BillingCycle.ANNUALLY:
        return plan.base_price_monthly * 12 * 0.8  # 20% discount
    return plan.base_price_monthly * 12


def find_best_fit_plan(
    users: int, expected_tokens: int, expected_storage: int, expected_api_calls: int = 0
) -> PricingTier:
    """
    Find the best-fit pricing tier based on expected usage.

    Uses a simple algorithm to recommend the most cost-effective tier.
    """
    # Calculate costs for each tier
    costs = {}
    for tier, plan in ENTERPRISE_PRICING_PLANS.items():
        usage = {
            UsageType.AI_TOKENS: expected_tokens,
            UsageType.STORAGE_GB: expected_storage,
            UsageType.API_CALLS: expected_api_calls,
        }
        monthly_cost = plan.calculate_monthly_cost(usage)
        costs[tier] = monthly_cost

    # Find minimum cost tier that can handle the usage
    best_tier = PricingTier.STARTUP
    min_cost = float("inf")

    for tier, plan in ENTERPRISE_PRICING_PLANS.items():
        if (
            users <= plan.max_users
            and expected_tokens <= plan.max_ai_tokens
            and expected_storage <= plan.max_storage_gb
            and expected_api_calls <= plan.max_api_calls
        ):
            if costs[tier] < min_cost:
                min_cost = costs[tier]
                best_tier = tier

    return best_tier


__all__ = [
    "ENTERPRISE_PRICING_PLANS",
    "get_pricing_plan",
    "get_all_plans",
    "calculate_annual_discount",
    "find_best_fit_plan",
]
