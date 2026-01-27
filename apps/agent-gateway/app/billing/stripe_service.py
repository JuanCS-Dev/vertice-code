"""
Stripe Service for Payment Processing.

Handles all Stripe API interactions:
- Checkout session creation
- Customer portal
- Subscription management
- Webhook processing

Requires: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET in environment.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Stripe SDK
try:
    import stripe

    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logger.warning("Stripe SDK not installed - billing disabled")


class SubscriptionStatus(str, Enum):
    """Subscription status."""

    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    TRIALING = "trialing"
    UNPAID = "unpaid"
    NONE = "none"


class PricingTier(str, Enum):
    """Pricing tier."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class StripeConfig:
    """Stripe configuration."""

    secret_key: str = ""
    webhook_secret: str = ""
    publishable_key: str = ""
    # Price IDs (from Stripe Dashboard)
    pro_monthly_price_id: str = ""
    pro_yearly_price_id: str = ""
    # URLs
    success_url: str = "https://app.vertice.ai/settings/billing?success=true"
    cancel_url: str = "https://app.vertice.ai/settings/billing?canceled=true"
    portal_return_url: str = "https://app.vertice.ai/settings/billing"

    @classmethod
    def from_env(cls) -> "StripeConfig":
        """Load config from environment."""
        return cls(
            secret_key=os.getenv("STRIPE_SECRET_KEY", ""),
            webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", ""),
            publishable_key=os.getenv("STRIPE_PUBLISHABLE_KEY", ""),
            pro_monthly_price_id=os.getenv("STRIPE_PRO_MONTHLY_PRICE_ID", ""),
            pro_yearly_price_id=os.getenv("STRIPE_PRO_YEARLY_PRICE_ID", ""),
            success_url=os.getenv(
                "STRIPE_SUCCESS_URL",
                "https://app.vertice.ai/settings/billing?success=true",
            ),
            cancel_url=os.getenv(
                "STRIPE_CANCEL_URL",
                "https://app.vertice.ai/settings/billing?canceled=true",
            ),
            portal_return_url=os.getenv(
                "STRIPE_PORTAL_RETURN_URL",
                "https://app.vertice.ai/settings/billing",
            ),
        )


class StripeService:
    """
    Service for Stripe payment processing.

    Handles checkout, subscriptions, and webhooks.
    """

    def __init__(self, config: Optional[StripeConfig] = None):
        """Initialize Stripe service."""
        self.config = config or StripeConfig.from_env()
        self._initialized = False

        if STRIPE_AVAILABLE and self.config.secret_key:
            stripe.api_key = self.config.secret_key
            self._initialized = True
            logger.info("Stripe service initialized")
        else:
            logger.warning("Stripe not configured - billing disabled")

    @property
    def is_available(self) -> bool:
        """Check if Stripe is available."""
        return self._initialized

    async def create_checkout_session(
        self,
        customer_email: str,
        org_id: str,
        user_id: str,
        price_id: Optional[str] = None,
        yearly: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session.

        Args:
            customer_email: Customer email
            org_id: Organization ID
            user_id: User ID
            price_id: Optional specific price ID
            yearly: Use yearly pricing

        Returns:
            Dict with checkout_url and session_id
        """
        if not self._initialized:
            raise RuntimeError("Stripe not initialized")

        # Determine price
        if not price_id:
            price_id = (
                self.config.pro_yearly_price_id if yearly else self.config.pro_monthly_price_id
            )

        if not price_id:
            raise ValueError("No price ID configured")

        try:
            session = stripe.checkout.Session.create(
                mode="subscription",
                payment_method_types=["card"],
                customer_email=customer_email,
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=self.config.success_url,
                cancel_url=self.config.cancel_url,
                metadata={
                    "org_id": org_id,
                    "user_id": user_id,
                },
                subscription_data={
                    "metadata": {
                        "org_id": org_id,
                        "user_id": user_id,
                    },
                },
            )

            logger.info(f"Created checkout session {session.id} for org {org_id}")

            return {
                "checkout_url": session.url,
                "session_id": session.id,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe checkout error: {e}")
            raise RuntimeError(f"Checkout failed: {e.user_message}")

    async def create_portal_session(
        self,
        customer_id: str,
    ) -> Dict[str, Any]:
        """
        Create a Stripe Customer Portal session.

        Args:
            customer_id: Stripe customer ID

        Returns:
            Dict with portal_url
        """
        if not self._initialized:
            raise RuntimeError("Stripe not initialized")

        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=self.config.portal_return_url,
            )

            return {"portal_url": session.url}

        except stripe.error.StripeError as e:
            logger.error(f"Stripe portal error: {e}")
            raise RuntimeError(f"Portal session failed: {e.user_message}")

    async def get_customer_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get customer by email."""
        if not self._initialized:
            return None

        try:
            customers = stripe.Customer.list(email=email, limit=1)
            if customers.data:
                return customers.data[0].to_dict()
            return None
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get customer: {e}")
            return None

    async def get_subscription(
        self,
        subscription_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get subscription details."""
        if not self._initialized:
            return None

        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            return sub.to_dict()
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get subscription: {e}")
            return None

    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True,
    ) -> bool:
        """
        Cancel a subscription.

        Args:
            subscription_id: Stripe subscription ID
            at_period_end: Cancel at end of period (default) or immediately

        Returns:
            True if successful
        """
        if not self._initialized:
            return False

        try:
            if at_period_end:
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                )
            else:
                stripe.Subscription.delete(subscription_id)

            logger.info(f"Canceled subscription {subscription_id}")
            return True

        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {e}")
            return False

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Verify and parse webhook payload.

        Args:
            payload: Raw request body
            signature: Stripe-Signature header

        Returns:
            Parsed event or None if invalid
        """
        if not self._initialized:
            return None

        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                self.config.webhook_secret,
            )
            return event.to_dict()

        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "initialized": self._initialized,
            "stripe_available": STRIPE_AVAILABLE,
            "has_secret_key": bool(self.config.secret_key),
            "has_webhook_secret": bool(self.config.webhook_secret),
            "has_pro_monthly_price": bool(self.config.pro_monthly_price_id),
            "has_pro_yearly_price": bool(self.config.pro_yearly_price_id),
        }


# Global instance
_stripe_service: Optional[StripeService] = None


def get_stripe_service() -> StripeService:
    """Get global Stripe service instance."""
    global _stripe_service
    if _stripe_service is None:
        _stripe_service = StripeService()
    return _stripe_service
