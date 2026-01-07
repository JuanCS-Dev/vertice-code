"""
Usage Metering Service
Real-time usage tracking and reporting to Stripe
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from collections import defaultdict

from app.core.config import settings
from app.core.stripe_service import get_stripe_service
from app.core.database import get_db_session

logger = logging.getLogger(__name__)


class UsageMeteringService:
    """
    Real-time usage metering and batch reporting to Stripe.

    Tracks LLM tokens, storage, API calls, and other billable resources.
    Reports usage to Stripe in optimized batches to avoid rate limiting.
    """

    def __init__(self):
        self.stripe_service = get_stripe_service()

        # In-memory buffers for batching (in production, use Redis)
        self.usage_buffer: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.last_report_time: Dict[str, float] = {}

        # Batch reporting task
        self.reporting_task: Optional[asyncio.Task] = None

    async def start_batch_reporting(self):
        """Start the periodic batch reporting task."""
        if self.reporting_task and not self.reporting_task.done():
            return

        self.reporting_task = asyncio.create_task(self._batch_reporting_loop())

    async def stop_batch_reporting(self):
        """Stop the batch reporting task."""
        if self.reporting_task:
            self.reporting_task.cancel()
            try:
                await self.reporting_task
            except asyncio.CancelledError:
                pass

    async def record_usage(
        self,
        workspace_id: str,
        resource_type: str,
        quantity: float,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> bool:
        """
        Record usage for a workspace.

        Args:
            workspace_id: Workspace generating usage
            resource_type: Type of resource (llm_tokens, storage_gb, api_calls)
            quantity: Amount used
            user_id: User responsible for usage (optional)
            agent_id: Agent responsible for usage (optional)
            session_id: Session identifier (optional)

        Returns:
            Success status
        """
        try:
            # Store in database immediately for audit trail
            async with get_db_session() as session:
                await session.execute(
                    """
                    INSERT INTO usage_records
                    (workspace_id, resource_type, quantity_used, unit, user_id, agent_id, session_id, recorded_at, billing_period)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    workspace_id,
                    resource_type,
                    quantity,
                    self._get_unit_for_resource(resource_type),
                    user_id,
                    agent_id,
                    session_id,
                    datetime.now(),
                    datetime.now().date(),
                )

            # Buffer for batch reporting to Stripe
            self.usage_buffer[workspace_id][resource_type] += quantity

            # Check if we should report immediately for high-volume resources
            if self._should_report_immediately(resource_type, quantity):
                await self._report_workspace_usage(workspace_id)

            logger.debug(f"Recorded usage: {workspace_id}:{resource_type}={quantity}")
            return True

        except Exception as e:
            logger.error(f"Failed to record usage: {e}")
            return False

    async def record_llm_usage(
        self,
        workspace_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cached_input_tokens: int = 0,
        cached_output_tokens: int = 0,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> bool:
        """
        Record LLM-specific usage with token accounting.

        Handles different token types and billing calculations.
        """
        try:
            total_input_tokens = input_tokens + cached_input_tokens
            total_output_tokens = output_tokens + cached_output_tokens

            # Calculate billable tokens (cached tokens are discounted)
            billable_input_tokens = input_tokens + (cached_input_tokens * 0.1)  # 10% of cached
            billable_output_tokens = output_tokens + (cached_output_tokens * 0.1)

            total_billable_tokens = billable_input_tokens + billable_output_tokens

            # Record the usage
            success = await self.record_usage(
                workspace_id=workspace_id,
                resource_type="llm_tokens",
                quantity=total_billable_tokens,
                user_id=user_id,
                agent_id=agent_id,
                session_id=session_id,
            )

            if success:
                # Also record detailed metrics for analytics
                async with get_db_session() as session:
                    await session.execute(
                        """
                        INSERT INTO usage_records
                        (workspace_id, resource_type, quantity_used, unit, user_id, agent_id, session_id,
                         recorded_at, billing_period, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                        workspace_id,
                        "llm_detailed",
                        total_billable_tokens,
                        "tokens",
                        user_id,
                        agent_id,
                        session_id,
                        datetime.now(),
                        datetime.now().date(),
                        {
                            "model": model,
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "cached_input_tokens": cached_input_tokens,
                            "cached_output_tokens": cached_output_tokens,
                            "billable_tokens": total_billable_tokens,
                        },
                    )

            return success

        except Exception as e:
            logger.error(f"Failed to record LLM usage: {e}")
            return False

    async def get_workspace_usage(
        self,
        workspace_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get usage summary for a workspace.

        Args:
            workspace_id: Workspace to query
            start_date: Start of period (defaults to current month)
            end_date: End of period (defaults to now)

        Returns:
            Usage summary with breakdown by resource type
        """
        try:
            if not start_date:
                start_date = datetime.now().replace(day=1)  # First day of current month
            if not end_date:
                end_date = datetime.now()

            async with get_db_session() as session:
                result = await session.execute(
                    """
                    SELECT
                        resource_type,
                        SUM(quantity_used) as total_quantity,
                        unit,
                        COUNT(*) as record_count
                    FROM usage_records
                    WHERE workspace_id = $1
                      AND recorded_at >= $2
                      AND recorded_at <= $3
                    GROUP BY resource_type, unit
                    ORDER BY total_quantity DESC
                """,
                    workspace_id,
                    start_date,
                    end_date,
                )

                rows = result.fetchall()

                usage_summary = {}
                for row in rows:
                    usage_summary[row[0]] = {
                        "total_quantity": float(row[1]),
                        "unit": row[2],
                        "record_count": row[3],
                    }

                # Get current billing period info
                billing_period_result = await session.execute(
                    """
                    SELECT
                        current_period_start,
                        current_period_end,
                        monthly_token_limit
                    FROM workspaces w
                    LEFT JOIN subscriptions s ON w.id = s.workspace_id
                    WHERE w.id = $1
                """,
                    workspace_id,
                )

                billing_info = billing_period_result.fetchone()

                return {
                    "workspace_id": workspace_id,
                    "period_start": billing_info[0] if billing_info else None,
                    "period_end": billing_info[1] if billing_info else None,
                    "monthly_limit": billing_info[2] if billing_info else None,
                    "usage_by_type": usage_summary,
                    "total_types": len(usage_summary),
                }

        except Exception as e:
            logger.error(f"Failed to get workspace usage: {e}")
            return {"workspace_id": workspace_id, "error": str(e), "usage_by_type": {}}

    async def check_workspace_limits(self, workspace_id: str) -> Dict[str, Any]:
        """
        Check if workspace is approaching or exceeding usage limits.

        Returns:
            Dict with limit status and warnings
        """
        try:
            usage = await self.get_workspace_usage(workspace_id)

            limits_check = {"within_limits": True, "warnings": [], "exceeded": []}

            monthly_limit = usage.get("monthly_limit")
            if monthly_limit:
                llm_usage = usage["usage_by_type"].get("llm_tokens", {}).get("total_quantity", 0)

                if llm_usage >= monthly_limit * 0.8:  # 80% warning
                    limits_check["warnings"].append(
                        {
                            "type": "approaching_limit",
                            "resource": "llm_tokens",
                            "current": llm_usage,
                            "limit": monthly_limit,
                            "percentage": (llm_usage / monthly_limit) * 100,
                        }
                    )

                if llm_usage >= monthly_limit:  # 100% exceeded
                    limits_check["within_limits"] = False
                    limits_check["exceeded"].append(
                        {
                            "type": "limit_exceeded",
                            "resource": "llm_tokens",
                            "current": llm_usage,
                            "limit": monthly_limit,
                        }
                    )

            return limits_check

        except Exception as e:
            logger.error(f"Failed to check workspace limits: {e}")
            return {"error": str(e)}

    # Private methods

    async def _batch_reporting_loop(self):
        """Periodic batch reporting to Stripe."""
        while True:
            try:
                await asyncio.sleep(settings.USAGE_REPORT_INTERVAL_MINUTES * 60)

                # Report usage for all workspaces with pending usage
                workspaces_to_report = list(self.usage_buffer.keys())

                for workspace_id in workspaces_to_report:
                    await self._report_workspace_usage(workspace_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Batch reporting error: {e}")

    async def _report_workspace_usage(self, workspace_id: str):
        """Report accumulated usage for a workspace to Stripe."""
        if workspace_id not in self.usage_buffer:
            return

        usage_data = self.usage_buffer[workspace_id]

        # Convert to list format for batch reporting
        usage_records = [
            {"workspace_id": workspace_id, "resource_type": resource_type, "quantity": quantity}
            for resource_type, quantity in usage_data.items()
        ]

        # Report to Stripe
        results = await self.stripe_service.batch_report_usage(usage_records)

        if results["success"] > 0:
            logger.info(f"Reported {results['success']} usage records for workspace {workspace_id}")

            # Clear the buffer for successfully reported items
            for resource_type in usage_data.keys():
                if resource_type in [
                    r["resource_type"] for r in usage_records if "success" in str(results)
                ]:
                    del self.usage_buffer[workspace_id][resource_type]

            # Clean up empty workspace entries
            if not self.usage_buffer[workspace_id]:
                del self.usage_buffer[workspace_id]

        if results["failed"] > 0:
            logger.warning(
                f"Failed to report {results['failed']} usage records for workspace {workspace_id}"
            )

    def _should_report_immediately(self, resource_type: str, quantity: float) -> bool:
        """Determine if usage should be reported immediately."""
        # Report large quantities immediately
        thresholds = {
            "llm_tokens": 10000,  # 10K tokens
            "storage_gb": 1,  # 1GB
            "api_calls": 1000,  # 1K calls
        }

        threshold = thresholds.get(resource_type, float("inf"))
        return quantity >= threshold

    def _get_unit_for_resource(self, resource_type: str) -> str:
        """Get billing unit for resource type."""
        units = {
            "llm_tokens": "tokens",
            "storage_gb": "gb",
            "api_calls": "calls",
            "compute_seconds": "seconds",
            "llm_detailed": "tokens",
        }
        return units.get(resource_type, "units")


# Global service instance
_usage_metering_service: Optional[UsageMeteringService] = None


def get_usage_metering_service() -> UsageMeteringService:
    """Get global usage metering service instance."""
    global _usage_metering_service
    if _usage_metering_service is None:
        _usage_metering_service = UsageMeteringService()
    return _usage_metering_service
