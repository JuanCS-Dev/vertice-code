"""
Billing API Endpoints
Stripe integration for subscriptions, invoices, and customer portal
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Optional
from pydantic import BaseModel
import logging

from app.core.auth import FirebaseUser, get_current_user
from app.core.stripe_service import get_stripe_service
from app.core.usage_metering import get_usage_metering_service
from app.core.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)


class CreateSubscriptionRequest(BaseModel):
    price_id: str
    trial_days: Optional[int] = 14


class UsageReportRequest(BaseModel):
    resource_type: str
    quantity: float
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/subscriptions")
async def create_subscription(
    request: CreateSubscriptionRequest,
    background_tasks: BackgroundTasks,
    user: FirebaseUser = Depends(get_current_user),
):
    """
    Create a new subscription for the user's workspace.

    This endpoint:
    1. Creates or retrieves Stripe customer
    2. Creates subscription with trial period
    3. Stores subscription info in database
    4. Starts usage metering
    """
    try:
        settings = get_settings()
        allowed_prices = [
            settings.STRIPE_PRICE_FREEMIUM,
            settings.STRIPE_PRICE_PRO,
            settings.STRIPE_PRICE_ENTERPRISE,
        ]

        if request.price_id not in allowed_prices:
            logger.warning(
                f"Unauthorized price ID attempt: {request.price_id} by user {user.user_id}"
            )
            raise HTTPException(status_code=400, detail="Invalid or unauthorized plan selected")

        stripe_service = get_stripe_service()

        # Create subscription
        subscription_data = await stripe_service.create_subscription(
            workspace_id=user.workspace_id or user.user_id,  # Fallback for single-user workspaces
            price_id=request.price_id,
            trial_days=request.trial_days or 14,
        )

        # Start usage metering for this workspace
        metering_service = get_usage_metering_service()
        await metering_service.start_batch_reporting()

        return {
            "message": "Subscription created successfully",
            "subscription": subscription_data,
            "trial_ends_at": subscription_data.get("trial_end"),
            "next_billing_date": subscription_data.get("current_period_end"),
        }

    except Exception as e:
        logger.error(f"Subscription creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create subscription: {str(e)}")


@router.get("/subscriptions")
async def get_subscription_status(user: FirebaseUser = Depends(get_current_user)):
    """
    Get current subscription status for the user's workspace.
    """
    try:
        from app.core.database import get_db_session
        from app.models.database import Subscription
        from sqlalchemy import select

        workspace_id = user.workspace_id or user.user_id

        async with get_db_session() as session:
            # Query the subscription table directly
            result = await session.execute(
                select(Subscription).where(Subscription.workspace_id == workspace_id)
            )
            subscription = result.scalars().first()

            if subscription:
                return {
                    "status": subscription.status,
                    "plan": subscription.plan_name,
                    "current_period_start": subscription.current_period_start,
                    "current_period_end": subscription.current_period_end,
                    "trial_end": subscription.trial_end,
                    "cancel_at_period_end": subscription.cancel_at_period_end,
                }
            else:
                # No subscription found = Free Tier
                return {
                    "status": "active",
                    "plan": "free",
                    "current_period_start": None,
                    "current_period_end": None,
                    "trial_end": None,
                    "cancel_at_period_end": False,
                }

    except Exception as e:
        logger.error(f"Failed to get subscription status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve subscription status")


@router.post("/usage")
async def report_usage(request: UsageReportRequest, user: FirebaseUser = Depends(get_current_user)):
    """
    Report usage for billing purposes.

    This endpoint allows manual usage reporting, typically used for:
    - API calls from external systems
    - Bulk operations
    - Testing and debugging
    """
    try:
        metering_service = get_usage_metering_service()

        success = await metering_service.record_usage(
            workspace_id=user.workspace_id or user.user_id,
            resource_type=request.resource_type,
            quantity=request.quantity,
            user_id=user.user_id,
            agent_id=request.agent_id,
            session_id=request.session_id,
        )

        if success:
            return {"message": "Usage recorded successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to record usage")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Usage reporting failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to report usage: {str(e)}")


@router.get("/usage")
async def get_usage_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: FirebaseUser = Depends(get_current_user),
):
    """
    Get usage summary for the current billing period.

    Query parameters:
    - start_date: ISO date string (optional)
    - end_date: ISO date string (optional)
    """
    try:
        from datetime import datetime

        # Parse dates if provided
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        metering_service = get_usage_metering_service()
        usage_data = await metering_service.get_workspace_usage(
            workspace_id=user.workspace_id or user.user_id, start_date=start, end_date=end
        )

        return usage_data

    except Exception as e:
        logger.error(f"Failed to get usage summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve usage data: {str(e)}")


@router.get("/limits")
async def check_usage_limits(user: FirebaseUser = Depends(get_current_user)):
    """
    Check if workspace is approaching or exceeding usage limits.
    """
    try:
        metering_service = get_usage_metering_service()
        limits_check = await metering_service.check_workspace_limits(
            workspace_id=user.workspace_id or user.user_id
        )

        return limits_check

    except Exception as e:
        logger.error(f"Failed to check usage limits: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check limits: {str(e)}")


@router.get("/portal")
async def get_customer_portal_url(user: FirebaseUser = Depends(get_current_user)):
    """
    Get Stripe Customer Portal URL for self-service billing management.

    Returns:
        {"url": "https://billing.stripe.com/..."}
    """
    try:
        stripe_service = get_stripe_service()
        portal_url = await stripe_service.get_customer_portal_url(
            workspace_id=user.workspace_id or user.user_id
        )

        if portal_url:
            return {"url": portal_url}
        else:
            raise HTTPException(status_code=404, detail="Customer portal not available")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get customer portal URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate portal URL: {str(e)}")


@router.get("/preview")
async def get_invoice_preview(
    upcoming_usage: Optional[Dict[str, float]] = None,
    user: FirebaseUser = Depends(get_current_user),
):
    """
    Generate invoice preview for next billing cycle.

    Query parameter:
    - upcoming_usage: JSON object with resource_type -> quantity mappings
    """
    try:
        stripe_service = get_stripe_service()
        preview = await stripe_service.create_invoice_preview(
            workspace_id=user.workspace_id or user.user_id, upcoming_usage=upcoming_usage or {}
        )

        return preview

    except Exception as e:
        logger.error(f"Failed to generate invoice preview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")


@router.post("/webhooks/stripe")
async def stripe_webhook(raw_body: bytes, stripe_signature: str = None):
    """
    Stripe webhook endpoint for payment events.

    Headers required:
    - Stripe-Signature: Webhook signature for verification

    This endpoint handles:
    - invoice.payment_succeeded
    - invoice.payment_failed
    - customer.subscription.updated
    - customer.subscription.deleted
    """
    try:
        if not stripe_signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")

        stripe_service = get_stripe_service()
        result = await stripe_service.process_webhook(raw_body.decode(), stripe_signature)

        if result.get("status") == "error":
            raise HTTPException(
                status_code=400, detail=result.get("error", "Webhook processing failed")
            )

        return {"status": "processed", "event_type": result.get("event_type")}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stripe webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
