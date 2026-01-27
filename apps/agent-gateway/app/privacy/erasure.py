"""
Data Erasure Service (Right to be Forgotten).

Implements GDPR Article 17 - Right to Erasure.

Features:
- Soft delete (immediate access removal)
- Hard delete (scheduled permanent removal)
- Audit trail for compliance
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Firestore integration
try:
    from google.cloud import firestore

    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False


class ErasureStatus(str, Enum):
    """Status of erasure request."""

    PENDING = "pending"
    SOFT_DELETED = "soft_deleted"
    HARD_DELETED = "hard_deleted"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ErasureRequest:
    """Request to erase user data."""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    org_id: str = ""
    status: ErasureStatus = ErasureStatus.PENDING
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    soft_deleted_at: Optional[datetime] = None
    hard_delete_scheduled: Optional[datetime] = None
    hard_deleted_at: Optional[datetime] = None
    collections_affected: List[str] = field(default_factory=list)
    documents_deleted: int = 0
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "org_id": self.org_id,
            "status": self.status.value,
            "requested_at": self.requested_at.isoformat(),
            "soft_deleted_at": self.soft_deleted_at.isoformat() if self.soft_deleted_at else None,
            "hard_delete_scheduled": (
                self.hard_delete_scheduled.isoformat() if self.hard_delete_scheduled else None
            ),
            "hard_deleted_at": self.hard_deleted_at.isoformat() if self.hard_deleted_at else None,
            "collections_affected": self.collections_affected,
            "documents_deleted": self.documents_deleted,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErasureRequest":
        """Create from dictionary."""
        return cls(
            request_id=data.get("request_id", str(uuid.uuid4())),
            user_id=data.get("user_id", ""),
            org_id=data.get("org_id", ""),
            status=ErasureStatus(data.get("status", "pending")),
            requested_at=datetime.fromisoformat(data["requested_at"])
            if "requested_at" in data
            else datetime.now(timezone.utc),
            soft_deleted_at=datetime.fromisoformat(data["soft_deleted_at"])
            if data.get("soft_deleted_at")
            else None,
            hard_delete_scheduled=datetime.fromisoformat(data["hard_delete_scheduled"])
            if data.get("hard_delete_scheduled")
            else None,
            hard_deleted_at=datetime.fromisoformat(data["hard_deleted_at"])
            if data.get("hard_deleted_at")
            else None,
            collections_affected=data.get("collections_affected", []),
            documents_deleted=data.get("documents_deleted", 0),
            error_message=data.get("error_message"),
        )


class DataErasureService:
    """
    Service for handling data erasure requests (GDPR Right to be Forgotten).

    Process:
    1. Soft delete: Immediately mark data as deleted (access removed)
    2. Hard delete: Permanently delete after retention period (default 30 days)
    """

    # Collections containing user data
    USER_DATA_COLLECTIONS = [
        "runs",
        "feedback",
        "memories",
        "insights",
        "healing_records",
        "evolutionary_candidates",
    ]

    # Retention period before hard delete (days)
    RETENTION_DAYS = 30

    def __init__(
        self,
        project_id: str = "vertice-ai",
        erasure_collection: str = "erasure_requests",
    ):
        """Initialize erasure service."""
        self.project_id = project_id
        self.erasure_collection = erasure_collection
        self._db: Optional[Any] = None
        self._collection: Optional[Any] = None
        self._pending_requests: List[ErasureRequest] = []

        if FIRESTORE_AVAILABLE:
            try:
                self._db = firestore.AsyncClient(project=project_id)
                self._collection = self._db.collection(erasure_collection)
                logger.info("Data erasure service connected to Firestore")
            except Exception as e:
                logger.warning(f"Firestore init failed for erasure: {e}")

    async def request_erasure(
        self,
        user_id: str,
        org_id: str,
    ) -> ErasureRequest:
        """
        Request erasure of all user data.

        Args:
            user_id: ID of user requesting erasure
            org_id: Organization ID

        Returns:
            ErasureRequest with status
        """
        request = ErasureRequest(
            user_id=user_id,
            org_id=org_id,
        )

        # Perform soft delete immediately
        try:
            await self._soft_delete_user_data(request)
            request.status = ErasureStatus.SOFT_DELETED
            request.soft_deleted_at = datetime.now(timezone.utc)
            request.hard_delete_scheduled = datetime.now(timezone.utc) + timedelta(
                days=self.RETENTION_DAYS
            )
            logger.info(f"Soft deleted data for user {user_id}")
        except Exception as e:
            request.status = ErasureStatus.FAILED
            request.error_message = str(e)
            logger.error(f"Failed to soft delete user data: {e}")

        # Store request
        if self._collection:
            try:
                await self._collection.document(request.request_id).set(request.to_dict())
            except Exception as e:
                logger.error(f"Failed to store erasure request: {e}")

        self._pending_requests.append(request)
        return request

    async def _soft_delete_user_data(self, request: ErasureRequest) -> None:
        """
        Soft delete user data by marking records as deleted.

        This removes access immediately but keeps data for the retention period.
        """
        if not self._db:
            logger.warning("No database connection for soft delete")
            return

        total_docs = 0

        for collection_name in self.USER_DATA_COLLECTIONS:
            try:
                collection = self._db.collection(collection_name)
                query = collection.where("user_id", "==", request.user_id)

                batch = self._db.batch()
                batch_count = 0

                async for doc in query.stream():
                    # Mark as deleted instead of removing
                    batch.update(
                        doc.reference,
                        {
                            "_deleted": True,
                            "_deleted_at": datetime.now(timezone.utc).isoformat(),
                            "_erasure_request_id": request.request_id,
                        },
                    )
                    batch_count += 1
                    total_docs += 1

                    # Commit in batches of 500
                    if batch_count >= 500:
                        await batch.commit()
                        batch = self._db.batch()
                        batch_count = 0

                if batch_count > 0:
                    await batch.commit()

                if batch_count > 0:
                    request.collections_affected.append(collection_name)

            except Exception as e:
                logger.error(f"Error soft deleting from {collection_name}: {e}")

        request.documents_deleted = total_docs

    async def execute_hard_delete(self, request_id: str) -> ErasureRequest:
        """
        Execute hard delete for a previously soft-deleted request.

        This permanently removes all data.
        """
        # Load request
        request = await self.get_request(request_id)
        if not request:
            raise ValueError(f"Erasure request {request_id} not found")

        if request.status != ErasureStatus.SOFT_DELETED:
            raise ValueError(f"Request not in soft_deleted state: {request.status}")

        if not self._db:
            request.status = ErasureStatus.FAILED
            request.error_message = "No database connection"
            return request

        total_deleted = 0

        for collection_name in self.USER_DATA_COLLECTIONS:
            try:
                collection = self._db.collection(collection_name)
                query = collection.where("_erasure_request_id", "==", request_id)

                async for doc in query.stream():
                    await doc.reference.delete()
                    total_deleted += 1

            except Exception as e:
                logger.error(f"Error hard deleting from {collection_name}: {e}")

        request.status = ErasureStatus.HARD_DELETED
        request.hard_deleted_at = datetime.now(timezone.utc)
        request.documents_deleted = total_deleted

        # Update request record
        if self._collection:
            await self._collection.document(request_id).set(request.to_dict())

        logger.info(f"Hard deleted {total_deleted} documents for request {request_id}")
        return request

    async def cancel_erasure(self, request_id: str) -> ErasureRequest:
        """
        Cancel an erasure request (restore soft-deleted data).

        Only works if hard delete hasn't been executed yet.
        """
        request = await self.get_request(request_id)
        if not request:
            raise ValueError(f"Erasure request {request_id} not found")

        if request.status == ErasureStatus.HARD_DELETED:
            raise ValueError("Cannot cancel - data already permanently deleted")

        if not self._db:
            raise ValueError("No database connection")

        # Restore soft-deleted documents
        for collection_name in self.USER_DATA_COLLECTIONS:
            try:
                collection = self._db.collection(collection_name)
                query = collection.where("_erasure_request_id", "==", request_id)

                batch = self._db.batch()
                batch_count = 0

                async for doc in query.stream():
                    batch.update(
                        doc.reference,
                        {
                            "_deleted": firestore.DELETE_FIELD,
                            "_deleted_at": firestore.DELETE_FIELD,
                            "_erasure_request_id": firestore.DELETE_FIELD,
                        },
                    )
                    batch_count += 1

                    if batch_count >= 500:
                        await batch.commit()
                        batch = self._db.batch()
                        batch_count = 0

                if batch_count > 0:
                    await batch.commit()

            except Exception as e:
                logger.error(f"Error restoring {collection_name}: {e}")

        request.status = ErasureStatus.CANCELLED

        if self._collection:
            await self._collection.document(request_id).set(request.to_dict())

        logger.info(f"Cancelled erasure request {request_id}")
        return request

    async def get_request(self, request_id: str) -> Optional[ErasureRequest]:
        """Get erasure request by ID."""
        if self._collection:
            try:
                doc = await self._collection.document(request_id).get()
                if doc.exists:
                    return ErasureRequest.from_dict(doc.to_dict())
            except Exception as e:
                logger.error(f"Failed to get erasure request: {e}")

        # Check local
        for req in self._pending_requests:
            if req.request_id == request_id:
                return req

        return None

    async def get_user_requests(self, user_id: str) -> List[ErasureRequest]:
        """Get all erasure requests for a user."""
        requests = []

        if self._collection:
            try:
                query = self._collection.where("user_id", "==", user_id)
                async for doc in query.stream():
                    requests.append(ErasureRequest.from_dict(doc.to_dict()))
            except Exception as e:
                logger.error(f"Failed to query erasure requests: {e}")

        return requests

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "pending_requests": len(self._pending_requests),
            "retention_days": self.RETENTION_DAYS,
            "collections_managed": self.USER_DATA_COLLECTIONS,
            "firestore_available": self._db is not None,
        }
