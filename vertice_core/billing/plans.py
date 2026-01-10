"""
Pricing plans configuration for Vertice SaaS.

Defines all available pricing tiers and their features.
"""

from .analytics import PricingTier, PricingPlan

# Enterprise pricing plans as defined in the roadmap
ENTERPRISE_PRICING_PLANS = {
    PricingTier.ENTERPRISE: PricingPlan(
        name="Enterprise",
        base_price_monthly=1999.0,
        white_glove_onboarding=True,
        dedicated_success_manager=True,
        custom_integrations=True,
        features=[
            "Custom integrations",
            "Advanced RBAC",
            "Audit logs",
            "Priority support",
            "99.9% uptime SLA",
        ],
    ),
    PricingTier.ENTERPRISE_PLUS: PricingPlan(
        name="Enterprise Plus",
        base_price_monthly=4999.0,
        white_glove_onboarding=True,
        dedicated_success_manager=True,
        custom_integrations=True,
        features=[
            "All Enterprise features",
            "Custom SLAs",
            "Dedicated infrastructure",
            "Advanced analytics",
            "24/7 phone support",
            "On-premise deployment option",
        ],
    ),
    PricingTier.ENTERPRISE_ELITE: PricingPlan(
        name="Enterprise Elite",
        base_price_monthly=9999.0,
        white_glove_onboarding=True,
        dedicated_success_manager=True,
        custom_integrations=True,
        features=[
            "All Enterprise Plus features",
            "Custom AI models",
            "Executive sponsorship",
            "Strategic consulting",
            "Custom development",
            "99.99% uptime SLA",
        ],
    ),
}

# Professional tier for smaller enterprises
PROFESSIONAL_PLAN = PricingPlan(
    name="Professional",
    base_price_monthly=499.0,
    white_glove_onboarding=True,
    dedicated_success_manager=False,
    custom_integrations=False,
    features=["Team collaboration", "Advanced analytics", "Priority support", "99.5% uptime SLA"],
)
