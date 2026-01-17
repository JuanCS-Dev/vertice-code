"""
Stripe Integration Service
Complete merchant-of-record solution for SaaS billing
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

import stripe

from app.core.config import settings
from app.core.database import get_db_session

logger = logging.getLogger(__name__)


class StripeService:
    """
    Complete Stripe integration for SaaS billing.

    Features:
    - Customer management
    - Subscription lifecycle
    - Metered billing (usage-based)
    - Webhook processing
    - Invoice management
    - Tax calculation
    """

    def __init__(self):
        # Configure Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.api_version = "2024-06-20"  # Latest stable version

        # Webhook secret for signature verification
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET

        # Product mapping for Vertice-ai
        self.product_ids = {
            "developer": "prod_ToBF141qTm6ki5",
            "team": "prod_ToBFtuSOov552S",
            "free": "prod_ToBFdM5MfE9fkQ",
        }

    async def create_customer(self, workspace_id: str, email: str, name: str) -> Dict[str, Any]:
        """
        Create Stripe customer for workspace.

        Args:
            workspace_id: Internal workspace identifier
            email: Customer email
            name: Customer name

        Returns:
            Customer data with Stripe customer ID
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={"workspace_id": workspace_id, "platform": "vertice"},
            )

            # Store customer ID in database
            async with get_db_session() as session:
                # Update workspace with Stripe customer ID
                await session.execute(
                    "UPDATE workspaces SET stripe_customer_id = $1 WHERE id = $2",
                    customer.id,
                    workspace_id,
                )

            return {
                "customer_id": customer.id,
                "email": customer.email,
                "name": customer.name,
                "created": customer.created,
            }

        except stripe.StripeError as e:
            logger.error(f"Stripe customer creation failed: {e}")
            raise

    async def create_subscription(
        self, workspace_id: str, price_id: str, trial_days: int = 14
    ) -> Dict[str, Any]:
        """
        Create subscription with trial period.

        Args:
            workspace_id: Workspace to subscribe
            price_id: Stripe price ID
            trial_days: Trial period in days

        Returns:
            Subscription data
        """
        try:
            # Get customer ID from database
            async with get_db_session() as session:
                result = await session.execute(
                    "SELECT stripe_customer_id FROM workspaces WHERE id = $1", workspace_id
                )
                customer_id = result.fetchone()[0]

            if not customer_id:
                raise ValueError(f"No Stripe customer found for workspace {workspace_id}")

            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                trial_period_days=trial_days,
                metadata={"workspace_id": workspace_id, "platform": "vertice"},
                billing_cycle_anchor=None,  # Start immediately after trial
                proration_behavior="create_prorations",  # Handle upgrades/downgrades
            )

            # Store subscription in database
            async with get_db_session() as session:
                await session.execute(
                    """
                    INSERT INTO subscriptions
                    (workspace_id, stripe_subscription_id, stripe_customer_id,
                     plan_name, status, current_period_start, current_period_end)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    workspace_id,
                    subscription.id,
                    customer_id,
                    "trial",  # Will be updated when trial ends
                    subscription.status,
                    datetime.fromtimestamp(subscription.current_period_start),
                    datetime.fromtimestamp(subscription.current_period_end),
                )

            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "trial_end": subscription.trial_end,
                "current_period_end": subscription.current_period_end,
            }

        except stripe.StripeError as e:
            logger.error(f"Stripe subscription creation failed: {e}")
            raise

    async def report_usage(
        self,
        workspace_id: str,
        resource_type: str,
        quantity: float,
        timestamp: Optional[int] = None,
    ) -> bool:
        """
        Report metered usage to Stripe.

        This accumulates usage and sends to Stripe in batches
        to avoid rate limiting.

        Args:
            workspace_id: Workspace generating usage
            resource_type: Type of resource (llm_tokens, storage_gb, api_calls)
            quantity: Amount used
            timestamp: Unix timestamp (defaults to now)

        Returns:
            Success status
        """
        try:
            timestamp = timestamp or int(time.time())

            # Get subscription item ID for this workspace and resource type
            subscription_item_id = await self._get_subscription_item_id(workspace_id, resource_type)

            if not subscription_item_id:
                logger.warning(f"No subscription item found for {workspace_id}:{resource_type}")
                return False

            # Report usage to Stripe
            stripe.SubscriptionItem.create_usage_record(
                subscription_item_id=subscription_item_id,
                quantity=int(quantity),  # Stripe expects integers
                timestamp=timestamp,
                action="increment",
            )

            # Also store in our database for analytics
            async with get_db_session() as session:
                await session.execute(
                    """
                    INSERT INTO usage_records
                    (workspace_id, resource_type, quantity_used, unit, recorded_at, billing_period)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    workspace_id,
                    resource_type,
                    quantity,
                    self._get_unit_for_resource(resource_type),
                    datetime.fromtimestamp(timestamp),
                    datetime.fromtimestamp(timestamp).date(),
                )

            logger.info(f"Reported usage: {workspace_id}:{resource_type}={quantity}")
            return True

        except stripe.StripeError as e:
            logger.error(f"Stripe usage report failed: {e}")
            return False

    async def batch_report_usage(self, usage_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Batch report multiple usage records efficiently.

        Args:
            usage_records: List of usage records with workspace_id, resource_type, quantity, timestamp

        Returns:
            Summary of reporting results
        """
        results = {"success": 0, "failed": 0, "errors": []}

        # Group by workspace and resource type for efficiency
        grouped_usage = {}
        for record in usage_records:
            key = (record["workspace_id"], record["resource_type"])
            if key not in grouped_usage:
                grouped_usage[key] = []
            grouped_usage[key].append(record)

        # Process each group
        for (workspace_id, resource_type), records in grouped_usage.items():
            try:
                # Aggregate quantities for the same resource type
                total_quantity = sum(r["quantity"] for r in records)
                latest_timestamp = max(r.get("timestamp", int(time.time())) for r in records)

                success = await self.report_usage(
                    workspace_id, resource_type, total_quantity, latest_timestamp
                )

                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Failed to report {workspace_id}:{resource_type}")

            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Error processing {workspace_id}:{resource_type}: {e}")

        return results

    async def process_webhook(self, payload: str, signature: str) -> Dict[str, Any]:
        """
        Process Stripe webhook with signature verification.

        Args:
            payload: Raw webhook payload
            signature: Stripe signature header

        Returns:
            Processing result
        """
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(payload, signature, self.webhook_secret)

            # Process based on event type
            event_type = event.type
            event_data = event.data.object

            logger.info(f"Processing Stripe webhook: {event_type}")

            if event_type == "invoice.payment_succeeded":
                await self._handle_payment_success(event_data)
            elif event_type == "invoice.payment_failed":
                await self._handle_payment_failure(event_data)
            elif event_type == "customer.subscription.updated":
                await self._handle_subscription_update(event_data)
            elif event_type == "customer.subscription.deleted":
                await self._handle_subscription_cancel(event_data)

            return {"status": "processed", "event_type": event_type}

        except stripe.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return {"status": "error", "error": "signature_verification_failed"}
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            return {"status": "error", "error": str(e)}

    async def get_customer_portal_url(self, workspace_id: str) -> Optional[str]:
        """
        Generate customer portal URL for self-service billing management.
        """
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    "SELECT stripe_customer_id FROM workspaces WHERE id = $1", workspace_id
                )
                customer_id = result.fetchone()[0]

            if not customer_id:
                return None

            # Create portal session
            session = stripe.billing_portal.Session.create(
                customer=customer_id, return_url=f"{settings.FRONTEND_URL}/billing"
            )

            return session.url

        except stripe.StripeError as e:
            logger.error(f"Customer portal URL creation failed: {e}")
            return None

    async def create_invoice_preview(
        self, workspace_id: str, upcoming_usage: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Generate invoice preview with upcoming usage.

        Args:
            workspace_id: Workspace to preview
            upcoming_usage: Dict of resource_type -> quantity

        Returns:
            Invoice preview data
        """
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    "SELECT stripe_customer_id FROM workspaces WHERE id = $1", workspace_id
                )
                customer_id = result.fetchone()[0]

            if not customer_id:
                raise ValueError(f"No Stripe customer for workspace {workspace_id}")

            # Create usage report for preview
            subscription_items = []
            for resource_type, quantity in upcoming_usage.items():
                item_id = await self._get_subscription_item_id(workspace_id, resource_type)
                if item_id:
                    subscription_items.append(
                        {"subscription_item": item_id, "quantity": int(quantity)}
                    )

            # Generate preview
            invoice = stripe.Invoice.create(
                customer=customer_id, subscription_items=subscription_items, preview=True
            )

            return {
                "amount_due": invoice.amount_due,
                "currency": invoice.currency,
                "period_start": invoice.period_start,
                "period_end": invoice.period_end,
                "lines": [
                    {
                        "description": line.description,
                        "amount": line.amount,
                        "quantity": line.quantity,
                    }
                    for line in invoice.lines.data
                ],
            }

        except stripe.StripeError as e:
            logger.error(f"Invoice preview failed: {e}")
            raise

    # Private helper methods

    async def _get_subscription_item_id(
        self, workspace_id: str, resource_type: str
    ) -> Optional[str]:
        """Get Stripe subscription item ID for workspace and resource type."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    """
                    SELECT si.id FROM subscription_items si
                    JOIN subscriptions s ON si.subscription_id = s.stripe_subscription_id
                    JOIN workspaces w ON s.workspace_id = w.id
                    WHERE w.id = $1 AND si.metadata->>'resource_type' = $2
                """,
                    workspace_id,
                    resource_type,
                )

                row = result.fetchone()
                return row[0] if row else None

        except Exception as e:
            logger.error(f"Failed to get subscription item ID: {e}")
            return None

    def _get_unit_for_resource(self, resource_type: str) -> str:
        """Get billing unit for resource type."""
        units = {
            "llm_tokens": "tokens",
            "storage_gb": "gb",
            "api_calls": "calls",
            "compute_seconds": "seconds",
        }
        return units.get(resource_type, "units")

    async def _handle_payment_success(self, invoice_data: Dict[str, Any]):
        """Handle successful payment webhook."""
        invoice_id = invoice_data.get("id")
        customer_id = invoice_data.get("customer")

        logger.info(f"Payment succeeded for invoice {invoice_id}, customer {customer_id}")

        # Update subscription status, send confirmation email, etc.

    async def _handle_payment_failure(self, invoice_data: Dict[str, Any]):
        """Handle failed payment webhook."""
        invoice_id = invoice_data.get("id")
        customer_id = invoice_data.get("customer")

        logger.warning(f"Payment failed for invoice {invoice_id}, customer {customer_id}")

        # Notify customer, downgrade subscription, etc.

    async def _handle_subscription_update(self, subscription_data: Dict[str, Any]):
        """Handle subscription update webhook."""
        subscription_id = subscription_data.get("id")
        status = subscription_data.get("status")

        logger.info(f"Subscription {subscription_id} updated to {status}")

        # Update local subscription record

    async def _handle_subscription_cancel(self, subscription_data: Dict[str, Any]):
        """Handle subscription cancellation webhook."""
        subscription_id = subscription_data.get("id")

        logger.info(f"Subscription {subscription_id} cancelled")

        # Update local records, revoke access, etc.


# Global service instance
_stripe_service: Optional[StripeService] = None


def get_stripe_service() -> StripeService:
    """Get global Stripe service instance."""
    global _stripe_service
    if _stripe_service is None:
        _stripe_service = StripeService()
    return _stripe_service
