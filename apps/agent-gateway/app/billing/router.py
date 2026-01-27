"""
Billing REST API Router.

Endpoints for:
- Stripe Checkout
- Customer Portal
- Subscription management
- Webhooks

Part of M7: Monetization & Billing.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from billing.stripe_service import get_stripe_service, PricingTier
from billing.subscription import SubscriptionManager, Subscription
from billing.guards import get_subscription_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/billing", tags=["billing"])


# ============================================================================
# Request/Response Models
# ============================================================================


class CheckoutRequest(BaseModel):
    """Request to create checkout session."""

    yearly: bool = Field(False, description="Use yearly pricing")
    price_id: Optional[str] = Field(None, description="Specific price ID")


class CheckoutResponse(BaseModel):
    """Checkout session response."""

    checkout_url: str
    session_id: str


class PortalResponse(BaseModel):
    """Customer portal response."""

    portal_url: str


class SubscriptionResponse(BaseModel):
    """Subscription status response."""

    org_id: str
    tier: str
    status: str
    is_active: bool
    is_pro: bool
    current_period_end: Optional[str]
    cancel_at_period_end: bool


class UsageSummaryResponse(BaseModel):
    """Usage summary response."""

    org_id: str
    metric: str
    total: int
    limit: int
    period_days: int
    tier: str


# ============================================================================
# Checkout Endpoints
# ============================================================================


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    request: CheckoutRequest,
    user_email: str = "user@example.com",  # TODO: Get from auth
    user_id: str = "anonymous",
    org_id: str = "default",
) -> CheckoutResponse:
    """
    Create a Stripe Checkout session for subscription.

    Redirects user to Stripe's hosted checkout page.
    """
    stripe_service = get_stripe_service()

    if not stripe_service.is_available:
        raise HTTPException(
            status_code=503,
            detail="Billing service not configured",
        )

    try:
        result = await stripe_service.create_checkout_session(
            customer_email=user_email,
            org_id=org_id,
            user_id=user_id,
            price_id=request.price_id,
            yearly=request.yearly,
        )

        return CheckoutResponse(
            checkout_url=result["checkout_url"],
            session_id=result["session_id"],
        )

    except Exception as e:
        logger.error(f"Checkout creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portal", response_model=PortalResponse)
async def create_portal_session(
    org_id: str = "default",
) -> PortalResponse:
    """
    Create a Stripe Customer Portal session.

    Allows customers to manage their subscription, update payment methods,
    view invoices, and cancel.
    """
    stripe_service = get_stripe_service()
    manager = get_subscription_manager()

    if not stripe_service.is_available:
        raise HTTPException(
            status_code=503,
            detail="Billing service not configured",
        )

    # Get subscription to find Stripe customer ID
    sub = await manager.get_subscription(org_id)

    if not sub.stripe_customer_id:
        raise HTTPException(
            status_code=404,
            detail="No subscription found for this organization",
        )

    try:
        result = await stripe_service.create_portal_session(
            customer_id=sub.stripe_customer_id,
        )

        return PortalResponse(portal_url=result["portal_url"])

    except Exception as e:
        logger.error(f"Portal session creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Subscription Endpoints
# ============================================================================


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    org_id: str = "default",
) -> SubscriptionResponse:
    """Get current subscription status for organization."""
    manager = get_subscription_manager()
    sub = await manager.get_subscription(org_id)

    return SubscriptionResponse(
        org_id=sub.org_id,
        tier=sub.tier.value,
        status=sub.status.value,
        is_active=sub.is_active,
        is_pro=sub.is_pro,
        current_period_end=(sub.current_period_end.isoformat() if sub.current_period_end else None),
        cancel_at_period_end=sub.cancel_at_period_end,
    )


@router.get("/usage/{metric}", response_model=UsageSummaryResponse)
async def get_usage(
    metric: str,
    org_id: str = "default",
    days: int = 30,
) -> UsageSummaryResponse:
    """Get usage summary for a metric."""
    manager = get_subscription_manager()
    usage = await manager.get_usage_summary(org_id, metric, days)

    return UsageSummaryResponse(
        org_id=usage["org_id"],
        metric=usage["metric"],
        total=usage["total"],
        limit=usage["limit"],
        period_days=usage["period_days"],
        tier=usage["tier"],
    )


@router.get("/limits")
async def get_limits(org_id: str = "default") -> Dict[str, Any]:
    """Get all limits for organization's tier."""
    manager = get_subscription_manager()
    sub = await manager.get_subscription(org_id)
    limits = manager.TIER_LIMITS.get(sub.tier, manager.TIER_LIMITS[PricingTier.FREE])

    return {
        "org_id": org_id,
        "tier": sub.tier.value,
        "limits": limits,
    }


# ============================================================================
# Webhook Endpoint
# ============================================================================


@router.post("/webhooks/stripe")
async def handle_stripe_webhook(request: Request) -> Dict[str, str]:
    """
    Handle Stripe webhook events.

    Events handled:
    - checkout.session.completed
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.paid
    - invoice.payment_failed
    """
    stripe_service = get_stripe_service()
    manager = get_subscription_manager()

    # Get raw body and signature
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")

    # Verify webhook
    event = stripe_service.verify_webhook_signature(body, signature)

    if not event:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event_type = event.get("type", "")
    data = event.get("data", {}).get("object", {})

    logger.info(f"Received Stripe webhook: {event_type}")

    try:
        if event_type == "checkout.session.completed":
            await _handle_checkout_completed(manager, data)

        elif event_type == "customer.subscription.updated":
            await _handle_subscription_updated(manager, data)

        elif event_type == "customer.subscription.deleted":
            await _handle_subscription_deleted(manager, data)

        elif event_type == "invoice.paid":
            logger.info(f"Invoice paid: {data.get('id')}")

        elif event_type == "invoice.payment_failed":
            await _handle_payment_failed(manager, data)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _handle_checkout_completed(
    manager: SubscriptionManager,
    data: Dict[str, Any],
) -> None:
    """Handle checkout.session.completed event."""
    from billing.stripe_service import SubscriptionStatus

    metadata = data.get("metadata", {})
    org_id = metadata.get("org_id", "")
    user_id = metadata.get("user_id", "")
    customer_id = data.get("customer", "")
    subscription_id = data.get("subscription", "")

    if not org_id:
        logger.warning("Checkout completed without org_id in metadata")
        return

    # Create/update subscription record
    sub = Subscription(
        org_id=org_id,
        user_id=user_id,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
        status=SubscriptionStatus.ACTIVE,
        tier=PricingTier.PRO,
    )

    await manager.upsert_subscription(sub)
    logger.info(f"Subscription created for org {org_id}")


async def _handle_subscription_updated(
    manager: SubscriptionManager,
    data: Dict[str, Any],
) -> None:
    """Handle customer.subscription.updated event."""
    from billing.stripe_service import SubscriptionStatus
    from datetime import datetime, timezone

    subscription_id = data.get("id", "")
    status = data.get("status", "")
    cancel_at_period_end = data.get("cancel_at_period_end", False)
    current_period_end = data.get("current_period_end")

    metadata = data.get("metadata", {})
    org_id = metadata.get("org_id", "")

    if not org_id:
        logger.warning("Subscription updated without org_id")
        return

    sub = await manager.get_subscription(org_id)
    sub.stripe_subscription_id = subscription_id
    sub.status = (
        SubscriptionStatus(status)
        if status in SubscriptionStatus.__members__.values()
        else sub.status
    )
    sub.cancel_at_period_end = cancel_at_period_end

    if current_period_end:
        sub.current_period_end = datetime.fromtimestamp(current_period_end, tz=timezone.utc)

    await manager.upsert_subscription(sub)
    logger.info(f"Subscription updated for org {org_id}: {status}")


async def _handle_subscription_deleted(
    manager: SubscriptionManager,
    data: Dict[str, Any],
) -> None:
    """Handle customer.subscription.deleted event."""
    from billing.stripe_service import SubscriptionStatus

    metadata = data.get("metadata", {})
    org_id = metadata.get("org_id", "")

    if not org_id:
        return

    sub = await manager.get_subscription(org_id)
    sub.status = SubscriptionStatus.CANCELED
    sub.tier = PricingTier.FREE

    await manager.upsert_subscription(sub)
    logger.info(f"Subscription canceled for org {org_id}")


async def _handle_payment_failed(
    manager: SubscriptionManager,
    data: Dict[str, Any],
) -> None:
    """Handle invoice.payment_failed event."""

    subscription_id = data.get("subscription", "")
    # In production, you'd look up org_id by subscription_id
    # For now, log the failure
    logger.warning(f"Payment failed for subscription {subscription_id}")


# ============================================================================
# Pricing Info (Public)
# ============================================================================


@router.get("/pricing")
async def get_pricing() -> Dict[str, Any]:
    """Get pricing information (public endpoint)."""
    return {
        "tiers": [
            {
                "id": "free",
                "name": "Free",
                "price_id": "price_1SqYt7PiY45Q31DMEEIwSl3H",
                "price_monthly": 0,
                "price_yearly": 0,
                "description": "Start exploring the future of code",
                "features": [
                    "50 requests/day",
                    "100K tokens/month",
                    "Gemini 3 Flash",
                    "Community support",
                ],
            },
            {
                "id": "developer",
                "name": "Developer",
                "price_id": "price_1SqYt4PiY45Q31DMv6A4VKis",
                "price_monthly": 19,
                "price_yearly": 190,
                "popular": True,
                "description": "For individual builders shipping fast",
                "features": [
                    "1,000 requests/day",
                    "5M tokens/month",
                    "Gemini 3 Pro + Flash",
                    "Priority support",
                    "Advanced analytics",
                ],
            },
            {
                "id": "team",
                "name": "Team",
                "price_id": "price_1SqYt6PiY45Q31DMApTVIIJw",
                "price_monthly": 49,
                "price_yearly": 490,
                "description": "Collaborative AI for ambitious teams",
                "features": [
                    "5,000 requests/day",
                    "25M tokens/month",
                    "All models including Pro",
                    "Team collaboration",
                    "Shared workspaces",
                    "Admin controls",
                ],
            },
        ],
        "currency": "USD",
    }


@router.get("/stats")
async def get_billing_stats() -> Dict[str, Any]:
    """Get billing service statistics."""
    stripe_service = get_stripe_service()
    manager = get_subscription_manager()

    return {
        "stripe": stripe_service.get_stats(),
        "subscriptions": manager.get_stats(),
    }
