"""
Data Export Service (Right to Data Portability).

Implements GDPR Article 20 - Right to Data Portability.

Features:
- Export all user data in JSON format
- Include all collections and metadata
- Secure download generation
"""

from __future__ import annotations

import json
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


class ExportFormat(str, Enum):
    """Export format options."""

    JSON = "json"
    CSV = "csv"  # Future support


@dataclass
class ExportRequest:
    """Request to export user data."""

    export_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    org_id: str = ""
    format: ExportFormat = ExportFormat.JSON
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    collections_exported: List[str] = field(default_factory=list)
    total_documents: int = 0
    file_size_bytes: int = 0
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "export_id": self.export_id,
            "user_id": self.user_id,
            "org_id": self.org_id,
            "format": self.format.value,
            "requested_at": self.requested_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "collections_exported": self.collections_exported,
            "total_documents": self.total_documents,
            "file_size_bytes": self.file_size_bytes,
            "download_url": self.download_url,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "error_message": self.error_message,
        }


class DataExportService:
    """
    Service for exporting user data (GDPR Data Portability).

    Collects all user data from various collections and generates
    a downloadable JSON export.
    """

    # Collections containing user data
    USER_DATA_COLLECTIONS = [
        "runs",
        "feedback",
        "memories",
        "insights",
        "orgs",
        "memberships",
    ]

    def __init__(
        self,
        project_id: str = "vertice-ai",
    ):
        """Initialize export service."""
        self.project_id = project_id
        self._db: Optional[Any] = None

        if FIRESTORE_AVAILABLE:
            try:
                self._db = firestore.AsyncClient(project=project_id)
                logger.info("Data export service connected to Firestore")
            except Exception as e:
                logger.warning(f"Firestore init failed for export: {e}")

    async def export_user_data(
        self,
        user_id: str,
        org_id: str,
        format: ExportFormat = ExportFormat.JSON,
    ) -> Dict[str, Any]:
        """
        Export all user data.

        Args:
            user_id: ID of user requesting export
            org_id: Organization ID
            format: Export format (currently only JSON)

        Returns:
            Dictionary containing all user data
        """
        request = ExportRequest(
            user_id=user_id,
            org_id=org_id,
            format=format,
        )

        export_data: Dict[str, Any] = {
            "export_metadata": {
                "export_id": request.export_id,
                "user_id": user_id,
                "org_id": org_id,
                "exported_at": request.requested_at.isoformat(),
                "format": format.value,
                "vertice_version": "2026.1.0",
            },
            "data": {},
        }

        total_docs = 0

        if self._db:
            for collection_name in self.USER_DATA_COLLECTIONS:
                try:
                    docs = await self._export_collection(collection_name, user_id, org_id)
                    if docs:
                        export_data["data"][collection_name] = docs
                        request.collections_exported.append(collection_name)
                        total_docs += len(docs)
                except Exception as e:
                    logger.error(f"Error exporting {collection_name}: {e}")
                    export_data["data"][collection_name] = {
                        "error": str(e),
                        "documents": [],
                    }

        request.total_documents = total_docs
        request.completed_at = datetime.now(timezone.utc)

        # Calculate size
        export_json = json.dumps(export_data, indent=2, default=str)
        request.file_size_bytes = len(export_json.encode("utf-8"))

        export_data["export_metadata"]["total_documents"] = total_docs
        export_data["export_metadata"]["file_size_bytes"] = request.file_size_bytes
        export_data["export_metadata"]["collections_exported"] = request.collections_exported

        logger.info(f"Exported {total_docs} documents for user {user_id}")

        return export_data

    async def _export_collection(
        self,
        collection_name: str,
        user_id: str,
        org_id: str,
    ) -> List[Dict[str, Any]]:
        """Export documents from a single collection."""
        documents = []

        if not self._db:
            return documents

        collection = self._db.collection(collection_name)

        # Query by user_id or org_id depending on collection
        if collection_name in ["orgs"]:
            # Org-level data
            query = collection.where("owner_uid", "==", user_id)
        elif collection_name in ["memberships"]:
            query = collection.where("user_id", "==", user_id)
        else:
            # User-level data
            query = collection.where("user_id", "==", user_id)

        async for doc in query.stream():
            doc_data = doc.to_dict()
            # Remove internal fields
            doc_data = self._sanitize_document(doc_data)
            doc_data["_document_id"] = doc.id
            documents.append(doc_data)

        return documents

    def _sanitize_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Remove internal/sensitive fields from document."""
        # Fields to exclude from export
        exclude_fields = [
            "_deleted",
            "_deleted_at",
            "_erasure_request_id",
            "_internal",
        ]

        return {k: v for k, v in doc.items() if k not in exclude_fields}

    async def get_export_summary(
        self,
        user_id: str,
        org_id: str,
    ) -> Dict[str, Any]:
        """
        Get summary of data that would be exported.

        Useful for showing user what data exists before full export.
        """
        summary: Dict[str, Any] = {
            "user_id": user_id,
            "org_id": org_id,
            "collections": {},
            "total_documents": 0,
        }

        if self._db:
            for collection_name in self.USER_DATA_COLLECTIONS:
                try:
                    collection = self._db.collection(collection_name)

                    if collection_name in ["orgs"]:
                        query = collection.where("owner_uid", "==", user_id)
                    elif collection_name in ["memberships"]:
                        query = collection.where("user_id", "==", user_id)
                    else:
                        query = collection.where("user_id", "==", user_id)

                    count = 0
                    async for _ in query.stream():
                        count += 1

                    summary["collections"][collection_name] = {
                        "document_count": count,
                    }
                    summary["total_documents"] += count

                except Exception as e:
                    logger.error(f"Error counting {collection_name}: {e}")
                    summary["collections"][collection_name] = {"error": str(e)}

        return summary

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "collections_managed": self.USER_DATA_COLLECTIONS,
            "supported_formats": [f.value for f in ExportFormat],
            "firestore_available": self._db is not None,
        }
