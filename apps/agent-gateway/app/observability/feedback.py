"""
Feedback Service for RLHF (Reinforcement Learning from Human Feedback).

Allows users to rate agent responses with thumbs up/down,
storing feedback for continuous improvement.

Features:
- Store user feedback on runs
- Aggregate feedback metrics
- Export for model training
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Firestore integration
try:
    from google.cloud import firestore

    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False


class FeedbackType(str, Enum):
    """Type of feedback."""

    POSITIVE = "positive"  # 👍
    NEGATIVE = "negative"  # 👎
    NEUTRAL = "neutral"


@dataclass
class FeedbackRecord:
    """Record of user feedback on a run."""

    feedback_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = ""
    user_id: str = ""
    org_id: str = ""
    feedback_type: FeedbackType = FeedbackType.NEUTRAL
    score: int = 0  # -1, 0, or 1
    comment: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "feedback_id": self.feedback_id,
            "run_id": self.run_id,
            "user_id": self.user_id,
            "org_id": self.org_id,
            "feedback_type": self.feedback_type.value,
            "score": self.score,
            "comment": self.comment,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeedbackRecord":
        """Create from dictionary."""
        return cls(
            feedback_id=data.get("feedback_id", str(uuid.uuid4())),
            run_id=data.get("run_id", ""),
            user_id=data.get("user_id", ""),
            org_id=data.get("org_id", ""),
            feedback_type=FeedbackType(data.get("feedback_type", "neutral")),
            score=data.get("score", 0),
            comment=data.get("comment"),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.now(timezone.utc),
            metadata=data.get("metadata", {}),
        )


class FeedbackService:
    """
    Service for collecting and managing user feedback.

    Stores feedback in Firestore for persistence and aggregation.
    """

    def __init__(
        self,
        project_id: str = "vertice-ai",
        collection_name: str = "feedback",
    ):
        """Initialize feedback service."""
        self.project_id = project_id
        self.collection_name = collection_name
        self._db: Optional[Any] = None
        self._collection: Optional[Any] = None
        self._local_feedback: List[FeedbackRecord] = []

        if FIRESTORE_AVAILABLE:
            try:
                self._db = firestore.AsyncClient(project=project_id)
                self._collection = self._db.collection(collection_name)
                logger.info(f"Feedback service connected to Firestore: {collection_name}")
            except Exception as e:
                logger.warning(f"Firestore init failed for feedback: {e}")

    async def submit_feedback(
        self,
        run_id: str,
        user_id: str,
        org_id: str,
        score: int,
        comment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FeedbackRecord:
        """
        Submit user feedback for a run.

        Args:
            run_id: ID of the run being rated
            user_id: ID of the user submitting feedback
            org_id: Organization ID
            score: -1 (negative), 0 (neutral), or 1 (positive)
            comment: Optional text comment
            metadata: Additional context (model used, prompt type, etc.)

        Returns:
            Created feedback record
        """
        # Validate score
        if score not in (-1, 0, 1):
            raise ValueError("Score must be -1, 0, or 1")

        # Determine feedback type
        if score > 0:
            feedback_type = FeedbackType.POSITIVE
        elif score < 0:
            feedback_type = FeedbackType.NEGATIVE
        else:
            feedback_type = FeedbackType.NEUTRAL

        record = FeedbackRecord(
            run_id=run_id,
            user_id=user_id,
            org_id=org_id,
            feedback_type=feedback_type,
            score=score,
            comment=comment,
            metadata=metadata or {},
        )

        # Store in Firestore
        if self._collection:
            try:
                await self._collection.document(record.feedback_id).set(record.to_dict())
                logger.info(f"Stored feedback {record.feedback_id} for run {run_id}")
            except Exception as e:
                logger.error(f"Failed to store feedback: {e}")

        # Keep local copy
        self._local_feedback.append(record)

        return record

    async def get_feedback_for_run(self, run_id: str) -> List[FeedbackRecord]:
        """Get all feedback for a specific run."""
        records = []

        if self._collection:
            try:
                query = self._collection.where("run_id", "==", run_id)
                async for doc in query.stream():
                    records.append(FeedbackRecord.from_dict(doc.to_dict()))
            except Exception as e:
                logger.error(f"Failed to query feedback: {e}")

        # Include local records
        for record in self._local_feedback:
            if record.run_id == run_id and record not in records:
                records.append(record)

        return records

    async def get_user_feedback(
        self,
        user_id: str,
        limit: int = 100,
    ) -> List[FeedbackRecord]:
        """Get feedback submitted by a user."""
        records = []

        if self._collection:
            try:
                query = (
                    self._collection.where("user_id", "==", user_id)
                    .order_by("timestamp", direction=firestore.Query.DESCENDING)
                    .limit(limit)
                )
                async for doc in query.stream():
                    records.append(FeedbackRecord.from_dict(doc.to_dict()))
            except Exception as e:
                logger.error(f"Failed to query user feedback: {e}")

        return records

    async def get_aggregate_stats(
        self,
        org_id: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get aggregate feedback statistics.

        Args:
            org_id: Filter by organization (optional)
            days: Number of days to include

        Returns:
            Aggregate statistics including:
            - total_feedback: Total number of feedback records
            - positive_count: Number of positive ratings
            - negative_count: Number of negative ratings
            - satisfaction_rate: Percentage of positive feedback
            - avg_score: Average score (-1 to 1)
        """
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        positive = 0
        negative = 0
        neutral = 0
        total_score = 0

        if self._collection:
            try:
                query = self._collection.where("timestamp", ">=", cutoff.isoformat())
                if org_id:
                    query = query.where("org_id", "==", org_id)

                async for doc in query.stream():
                    data = doc.to_dict()
                    score = data.get("score", 0)
                    total_score += score

                    if score > 0:
                        positive += 1
                    elif score < 0:
                        negative += 1
                    else:
                        neutral += 1
            except Exception as e:
                logger.error(f"Failed to aggregate feedback: {e}")

        total = positive + negative + neutral
        satisfaction_rate = (positive / total * 100) if total > 0 else 0.0
        avg_score = (total_score / total) if total > 0 else 0.0

        return {
            "total_feedback": total,
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": neutral,
            "satisfaction_rate": round(satisfaction_rate, 2),
            "avg_score": round(avg_score, 3),
            "period_days": days,
            "org_id": org_id,
        }

    async def export_for_training(
        self,
        min_score: Optional[int] = None,
        limit: int = 10000,
    ) -> List[Dict[str, Any]]:
        """
        Export feedback data for model training (RLHF).

        Args:
            min_score: Minimum score to include (optional)
            limit: Maximum records to export

        Returns:
            List of feedback records with run context
        """
        records = []

        if self._collection:
            try:
                query = self._collection.order_by(
                    "timestamp", direction=firestore.Query.DESCENDING
                ).limit(limit)

                async for doc in query.stream():
                    data = doc.to_dict()
                    if min_score is not None and data.get("score", 0) < min_score:
                        continue
                    records.append(data)
            except Exception as e:
                logger.error(f"Failed to export feedback: {e}")

        return records

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "local_feedback_count": len(self._local_feedback),
            "firestore_available": self._db is not None,
            "collection": self.collection_name,
        }
