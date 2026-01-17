"""
Admin API Endpoints
Provides admin-only access to system metrics, user management, and audit logs.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging
from datetime import datetime, timedelta

from app.core.auth import FirebaseUser, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# Admin user emails (should be in environment/config in production)
ADMIN_EMAILS = ["juancs.d3v@gmail.com"]


class AdminStats(BaseModel):
    """System-wide statistics."""

    total_users: int
    active_sessions: int
    total_tokens_today: int
    error_rate: float
    db_size_mb: float
    last_updated: str


class UserSummary(BaseModel):
    """User summary for admin dashboard."""

    user_id: str
    email: str
    plan: str
    tokens_used: int
    last_active: str
    status: str


def require_admin(user: FirebaseUser = Depends(get_current_user)) -> FirebaseUser:
    """Dependency to require admin access."""
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(admin: FirebaseUser = Depends(require_admin)):
    """
    Get system-wide statistics.

    Returns:
        AdminStats with current system metrics
    """
    # MOCK DATA: Replace with Firestore/Cloud Monitoring when integrated
    # See: docs/SAAS_IMPLEMENTATION_PLAN.md for integration roadmap
    return AdminStats(
        total_users=124,
        active_sessions=18,
        total_tokens_today=2_450_000,
        error_rate=0.2,
        db_size_mb=450.0,
        last_updated=datetime.utcnow().isoformat(),
    )


@router.get("/users", response_model=List[UserSummary])
async def list_users(
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    admin: FirebaseUser = Depends(require_admin),
):
    """
    List all users with pagination.

    Args:
        limit: Max number of users to return
        offset: Number of users to skip
        status_filter: Optional filter by status (active, suspended)
    """
    # MOCK DATA: Replace with Firestore query when integrated
    mock_users = [
        UserSummary(
            user_id=f"user_{i}",
            email=f"user{i}@example.com",
            plan="Developer" if i % 3 == 0 else "Free",
            tokens_used=10000 * i,
            last_active=(datetime.utcnow() - timedelta(hours=i)).isoformat(),
            status="active",
        )
        for i in range(1, min(limit + 1, 10))
    ]

    return mock_users


@router.get("/usage")
async def get_aggregate_usage(
    days: int = 7, admin: FirebaseUser = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get aggregate usage data for the last N days.

    Args:
        days: Number of days to aggregate
    """
    # MOCK DATA: Replace with real usage_metering data
    daily_data = []
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        daily_data.append(
            {
                "date": date,
                "tokens": 350000 + (i * 10000),
                "sessions": 45 + i,
                "unique_users": 28 + i,
            }
        )

    return {
        "period_days": days,
        "total_tokens": sum(d["tokens"] for d in daily_data),
        "total_sessions": sum(d["sessions"] for d in daily_data),
        "daily_breakdown": daily_data,
    }


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str, admin: FirebaseUser = Depends(require_admin)
) -> Dict[str, str]:
    """
    Suspend a user account.

    Args:
        user_id: User ID to suspend
    """
    logger.warning(f"Admin {admin.email} suspended user {user_id}")
    # STUB: Firestore/Firebase Auth integration pending
    return {"status": "suspended", "user_id": user_id}


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str, admin: FirebaseUser = Depends(require_admin)
) -> Dict[str, str]:
    """
    Reactivate a suspended user account.

    Args:
        user_id: User ID to activate
    """
    logger.info(f"Admin {admin.email} activated user {user_id}")
    # STUB: Firebase Auth integration pending
    return {"status": "active", "user_id": user_id}
