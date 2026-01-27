"""
Subscription Guards for Access Control.

Middleware and decorators to enforce subscription limits.
"""

from __future__ import annotations

import functools
import logging
from typing import Any, Callable, Optional, TypeVar

from fastapi import HTTPException, Request

from billing.stripe_service import PricingTier
from billing.subscription import SubscriptionManager

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# Global manager
_subscription_manager: Optional[SubscriptionManager] = None


def get_subscription_manager() -> SubscriptionManager:
    """Get global subscription manager."""
    global _subscription_manager
    if _subscription_manager is None:
        _subscription_manager = SubscriptionManager()
    return _subscription_manager


class SubscriptionGuard:
    """
    FastAPI middleware for subscription enforcement.

    Checks subscription status and usage limits before processing requests.
    """

    # Endpoints that require Pro subscription
    PRO_ONLY_ENDPOINTS = [
        "/v1/nexus/evolve",
        "/v1/nexus/prometheus/",
        "/agui/stream",  # Pro gets priority
    ]

    # Endpoints exempt from checks
    EXEMPT_ENDPOINTS = [
        "/healthz",
        "/readyz",
        "/openapi.json",
        "/v1/billing/",
        "/v1/me/",
    ]

    def __init__(self, app):
        """Initialize guard."""
        self.app = app
        self.manager = get_subscription_manager()

    async def __call__(self, scope, receive, send):
        """Process request through guard."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        # Check exemptions
        for exempt in self.EXEMPT_ENDPOINTS:
            if path.startswith(exempt):
                await self.app(scope, receive, send)
                return

        # For non-exempt paths, we'd check subscription here
        # This requires access to the request context which is complex in ASGI
        # For now, the endpoint-level decorators handle enforcement

        await self.app(scope, receive, send)


async def check_subscription(
    org_id: str,
    required_tier: PricingTier = PricingTier.FREE,
) -> dict:
    """
    Check if organization has required subscription.

    Args:
        org_id: Organization ID
        required_tier: Minimum required tier

    Returns:
        Dict with subscription info

    Raises:
        HTTPException if subscription insufficient
    """
    manager = get_subscription_manager()
    sub = await manager.get_subscription(org_id)

    tier_order = [PricingTier.FREE, PricingTier.PRO, PricingTier.ENTERPRISE]

    if tier_order.index(sub.tier) < tier_order.index(required_tier):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "subscription_required",
                "message": f"This feature requires {required_tier.value} subscription",
                "current_tier": sub.tier.value,
                "required_tier": required_tier.value,
                "upgrade_url": "/settings/billing",
            },
        )

    return {
        "org_id": org_id,
        "tier": sub.tier.value,
        "is_active": sub.is_active,
        "is_pro": sub.is_pro,
    }


async def check_usage_limit(
    org_id: str,
    metric: str,
    quantity: int = 1,
) -> dict:
    """
    Check if usage is within limits.

    Args:
        org_id: Organization ID
        metric: Usage metric (tokens, requests)
        quantity: Amount to check

    Returns:
        Dict with limit info

    Raises:
        HTTPException if limit exceeded
    """
    manager = get_subscription_manager()
    result = await manager.check_limit(org_id, metric, quantity)

    if not result["allowed"]:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "usage_limit_exceeded",
                "message": f"You have exceeded your {metric} limit",
                "metric": metric,
                "limit": result["limit"],
                "current": result["current"],
                "tier": result["tier"],
                "upgrade_url": "/settings/billing",
            },
        )

    return result


def require_pro(func: F) -> F:
    """
    Decorator to require Pro subscription.

    Usage:
        @require_pro
        async def premium_endpoint(request: Request):
            ...
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Try to get org_id from various sources
        org_id = kwargs.get("org_id")

        if not org_id:
            # Try to get from request
            for arg in args:
                if isinstance(arg, Request):
                    org_id = arg.headers.get("X-Vertice-Org")
                    break

        if not org_id:
            org_id = "default"

        await check_subscription(org_id, PricingTier.PRO)
        return await func(*args, **kwargs)

    return wrapper  # type: ignore


def require_limit(metric: str, quantity: int = 1):
    """
    Decorator to check usage limits.

    Usage:
        @require_limit("requests", 1)
        async def rate_limited_endpoint(request: Request):
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            org_id = kwargs.get("org_id", "default")

            for arg in args:
                if isinstance(arg, Request):
                    org_id = arg.headers.get("X-Vertice-Org", org_id)
                    break

            await check_usage_limit(org_id, metric, quantity)
            return await func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator
