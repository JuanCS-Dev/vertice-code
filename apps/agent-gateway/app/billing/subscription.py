"""
Subscription Management.

Handles subscription state persistence and usage tracking.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from billing.stripe_service import SubscriptionStatus, PricingTier

logger = logging.getLogger(__name__)

# Firestore
try:
    from google.cloud import firestore

    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False


@dataclass
class Subscription:
    """Subscription record."""

    subscription_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    org_id: str = ""
    user_id: str = ""
    stripe_customer_id: str = ""
    stripe_subscription_id: str = ""
    status: SubscriptionStatus = SubscriptionStatus.NONE
    tier: PricingTier = PricingTier.FREE
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "subscription_id": self.subscription_id,
            "org_id": self.org_id,
            "user_id": self.user_id,
            "stripe_customer_id": self.stripe_customer_id,
            "stripe_subscription_id": self.stripe_subscription_id,
            "status": self.status.value,
            "tier": self.tier.value,
            "current_period_start": (
                self.current_period_start.isoformat() if self.current_period_start else None
            ),
            "current_period_end": (
                self.current_period_end.isoformat() if self.current_period_end else None
            ),
            "cancel_at_period_end": self.cancel_at_period_end,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Subscription":
        """Create from dictionary."""
        return cls(
            subscription_id=data.get("subscription_id", str(uuid.uuid4())),
            org_id=data.get("org_id", ""),
            user_id=data.get("user_id", ""),
            stripe_customer_id=data.get("stripe_customer_id", ""),
            stripe_subscription_id=data.get("stripe_subscription_id", ""),
            status=SubscriptionStatus(data.get("status", "none")),
            tier=PricingTier(data.get("tier", "free")),
            current_period_start=(
                datetime.fromisoformat(data["current_period_start"])
                if data.get("current_period_start")
                else None
            ),
            current_period_end=(
                datetime.fromisoformat(data["current_period_end"])
                if data.get("current_period_end")
                else None
            ),
            cancel_at_period_end=data.get("cancel_at_period_end", False),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else datetime.now(timezone.utc)
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if data.get("updated_at")
                else datetime.now(timezone.utc)
            ),
        )

    @property
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING)

    @property
    def is_pro(self) -> bool:
        """Check if subscription is Pro tier."""
        return self.tier == PricingTier.PRO and self.is_active


@dataclass
class UsageRecord:
    """Usage record for metered billing."""

    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    org_id: str = ""
    user_id: str = ""
    metric: str = ""  # e.g., "tokens", "requests", "compute_minutes"
    quantity: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "record_id": self.record_id,
            "org_id": self.org_id,
            "user_id": self.user_id,
            "metric": self.metric,
            "quantity": self.quantity,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class SubscriptionManager:
    """
    Manages subscription state and usage.

    Persists to Firestore for durability.
    """

    # Usage limits by tier
    TIER_LIMITS = {
        PricingTier.FREE: {
            "requests_per_day": 50,
            "tokens_per_month": 100_000,
            "models": ["gemini-3-flash"],
        },
        PricingTier.PRO: {
            "requests_per_day": 1000,
            "tokens_per_month": 10_000_000,
            "models": ["gemini-3-flash", "gemini-3-pro"],
        },
        PricingTier.ENTERPRISE: {
            "requests_per_day": -1,  # Unlimited
            "tokens_per_month": -1,
            "models": ["gemini-3-flash", "gemini-3-pro", "gemini-3-ultra"],
        },
    }

    def __init__(
        self,
        project_id: str = "vertice-ai",
        subscriptions_collection: str = "subscriptions",
        usage_collection: str = "usage",
    ):
        """Initialize subscription manager."""
        self.project_id = project_id
        self.subscriptions_collection = subscriptions_collection
        self.usage_collection = usage_collection
        self._db: Optional[Any] = None
        self._subs_coll: Optional[Any] = None
        self._usage_coll: Optional[Any] = None
        self._local_cache: Dict[str, Subscription] = {}

        if FIRESTORE_AVAILABLE:
            try:
                self._db = firestore.AsyncClient(project=project_id)
                self._subs_coll = self._db.collection(subscriptions_collection)
                self._usage_coll = self._db.collection(usage_collection)
                logger.info("Subscription manager connected to Firestore")
            except Exception as e:
                logger.warning(f"Firestore init failed: {e}")

    async def get_subscription(self, org_id: str) -> Subscription:
        """Get subscription for an organization."""
        # Check cache
        if org_id in self._local_cache:
            return self._local_cache[org_id]

        # Check Firestore
        if self._subs_coll:
            try:
                query = self._subs_coll.where("org_id", "==", org_id).limit(1)
                async for doc in query.stream():
                    sub = Subscription.from_dict(doc.to_dict())
                    self._local_cache[org_id] = sub
                    return sub
            except Exception as e:
                logger.error(f"Failed to get subscription: {e}")

        # Default to free tier
        return Subscription(org_id=org_id, tier=PricingTier.FREE)

    async def upsert_subscription(self, subscription: Subscription) -> bool:
        """Create or update a subscription."""
        subscription.updated_at = datetime.now(timezone.utc)
        self._local_cache[subscription.org_id] = subscription

        if self._subs_coll:
            try:
                await self._subs_coll.document(subscription.subscription_id).set(
                    subscription.to_dict()
                )
                logger.info(f"Saved subscription for org {subscription.org_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to save subscription: {e}")
                return False

        return True

    async def record_usage(
        self,
        org_id: str,
        user_id: str,
        metric: str,
        quantity: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UsageRecord:
        """Record usage for billing."""
        record = UsageRecord(
            org_id=org_id,
            user_id=user_id,
            metric=metric,
            quantity=quantity,
            metadata=metadata or {},
        )

        if self._usage_coll:
            try:
                await self._usage_coll.document(record.record_id).set(record.to_dict())
            except Exception as e:
                logger.error(f"Failed to record usage: {e}")

        return record

    async def get_usage_summary(
        self,
        org_id: str,
        metric: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get usage summary for an organization."""
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        total = 0

        if self._usage_coll:
            try:
                query = (
                    self._usage_coll.where("org_id", "==", org_id)
                    .where("metric", "==", metric)
                    .where("timestamp", ">=", cutoff.isoformat())
                )
                async for doc in query.stream():
                    data = doc.to_dict()
                    total += data.get("quantity", 0)
            except Exception as e:
                logger.error(f"Failed to get usage: {e}")

        # Get limits for org's tier
        sub = await self.get_subscription(org_id)
        limits = self.TIER_LIMITS.get(sub.tier, self.TIER_LIMITS[PricingTier.FREE])

        return {
            "org_id": org_id,
            "metric": metric,
            "total": total,
            "period_days": days,
            "tier": sub.tier.value,
            "limit": limits.get(f"{metric}_per_month", -1),
        }

    async def check_limit(
        self,
        org_id: str,
        metric: str,
        quantity: int = 1,
    ) -> Dict[str, Any]:
        """
        Check if usage would exceed limit.

        Returns dict with allowed (bool) and remaining quota.
        """
        sub = await self.get_subscription(org_id)
        limits = self.TIER_LIMITS.get(sub.tier, self.TIER_LIMITS[PricingTier.FREE])

        limit_key = f"{metric}_per_month"
        if metric == "requests":
            limit_key = "requests_per_day"

        limit = limits.get(limit_key, 0)

        if limit < 0:  # Unlimited
            return {"allowed": True, "remaining": -1, "limit": -1}

        # Get current usage
        days = 30 if "month" in limit_key else 1
        usage = await self.get_usage_summary(org_id, metric, days=days)
        current = usage["total"]
        remaining = max(0, limit - current)

        return {
            "allowed": current + quantity <= limit,
            "remaining": remaining,
            "limit": limit,
            "current": current,
            "tier": sub.tier.value,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        return {
            "cached_subscriptions": len(self._local_cache),
            "firestore_available": self._db is not None,
            "tier_limits": {tier.value: limits for tier, limits in self.TIER_LIMITS.items()},
        }
