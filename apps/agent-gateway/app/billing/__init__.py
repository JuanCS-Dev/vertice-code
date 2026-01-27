"""
Billing Module for Vertice SaaS.

Implements Stripe-based monetization with:
- Subscription management (Free/Pro tiers)
- Usage-based billing for AI compute
- Customer portal integration
- Webhook handling for events

Part of M7: Monetization & Billing.
"""

from billing.stripe_service import (
    StripeService,
    get_stripe_service,
    SubscriptionStatus,
    PricingTier,
)
from billing.subscription import (
    SubscriptionManager,
    Subscription,
    UsageRecord,
)
from billing.guards import (
    SubscriptionGuard,
    check_subscription,
    require_pro,
)

__all__ = [
    # Stripe
    "StripeService",
    "get_stripe_service",
    "SubscriptionStatus",
    "PricingTier",
    # Subscription
    "SubscriptionManager",
    "Subscription",
    "UsageRecord",
    # Guards
    "SubscriptionGuard",
    "check_subscription",
    "require_pro",
]
