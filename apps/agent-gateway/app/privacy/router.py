"""
Privacy REST API Router.

Endpoints for GDPR/LGPD compliance:
- POST /v1/me/erasure - Request data erasure
- GET /v1/me/export - Export user data
- GET /v1/me/privacy - Privacy dashboard data

Part of M9: Data Protection & Privacy.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from privacy.crypto import get_crypto_service
from privacy.erasure import DataErasureService, ErasureStatus
from privacy.export import DataExportService, ExportFormat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/me", tags=["privacy"])

# Global services
_erasure_service: Optional[DataErasureService] = None
_export_service: Optional[DataExportService] = None


def get_erasure_service() -> DataErasureService:
    """Get or create erasure service."""
    global _erasure_service
    if _erasure_service is None:
        _erasure_service = DataErasureService()
    return _erasure_service


def get_export_service() -> DataExportService:
    """Get or create export service."""
    global _export_service
    if _export_service is None:
        _export_service = DataExportService()
    return _export_service


# ============================================================================
# Request/Response Models
# ============================================================================


class ErasureRequestModel(BaseModel):
    """Request to erase user data."""

    confirm: bool = Field(
        ...,
        description="Must be true to confirm erasure request",
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional reason for erasure",
    )


class ErasureResponse(BaseModel):
    """Response from erasure request."""

    request_id: str
    status: str
    soft_deleted_at: Optional[str]
    hard_delete_scheduled: Optional[str]
    documents_affected: int
    message: str


class ExportResponse(BaseModel):
    """Response containing exported data."""

    export_id: str
    user_id: str
    org_id: str
    exported_at: str
    total_documents: int
    file_size_bytes: int
    collections_exported: list
    data: Dict[str, Any]


class PrivacyDashboardResponse(BaseModel):
    """Privacy dashboard data."""

    user_id: str
    org_id: str
    data_summary: Dict[str, Any]
    erasure_requests: list
    encryption_status: Dict[str, Any]


# ============================================================================
# Erasure Endpoints (Right to be Forgotten)
# ============================================================================


@router.post("/erasure", response_model=ErasureResponse)
async def request_erasure(
    request: ErasureRequestModel,
    user_id: str = "anonymous",  # TODO: Get from auth context
    org_id: str = "default",  # TODO: Get from tenant context
) -> ErasureResponse:
    """
    Request erasure of all user data (GDPR Article 17).

    Process:
    1. Immediate soft delete (access removed)
    2. Hard delete scheduled after 30 days

    The request can be cancelled within the 30-day retention period.
    """
    if not request.confirm:
        raise HTTPException(
            status_code=400,
            detail="Must confirm erasure request by setting confirm=true",
        )

    service = get_erasure_service()

    try:
        erasure_request = await service.request_erasure(
            user_id=user_id,
            org_id=org_id,
        )

        if erasure_request.status == ErasureStatus.FAILED:
            raise HTTPException(
                status_code=500,
                detail=f"Erasure failed: {erasure_request.error_message}",
            )

        return ErasureResponse(
            request_id=erasure_request.request_id,
            status=erasure_request.status.value,
            soft_deleted_at=(
                erasure_request.soft_deleted_at.isoformat()
                if erasure_request.soft_deleted_at
                else None
            ),
            hard_delete_scheduled=(
                erasure_request.hard_delete_scheduled.isoformat()
                if erasure_request.hard_delete_scheduled
                else None
            ),
            documents_affected=erasure_request.documents_deleted,
            message=(
                f"Data access removed. Permanent deletion scheduled in "
                f"{service.RETENTION_DAYS} days. You can cancel this request "
                f"before then using request_id: {erasure_request.request_id}"
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erasure request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/erasure/{request_id}")
async def get_erasure_status(request_id: str) -> Dict[str, Any]:
    """Get status of an erasure request."""
    service = get_erasure_service()
    request = await service.get_request(request_id)

    if not request:
        raise HTTPException(status_code=404, detail="Erasure request not found")

    return request.to_dict()


@router.delete("/erasure/{request_id}")
async def cancel_erasure(request_id: str) -> Dict[str, Any]:
    """
    Cancel an erasure request and restore data.

    Only works if hard delete hasn't been executed yet.
    """
    service = get_erasure_service()

    try:
        request = await service.cancel_erasure(request_id)
        return {
            "request_id": request.request_id,
            "status": request.status.value,
            "message": "Erasure cancelled. Your data has been restored.",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to cancel erasure: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Export Endpoints (Right to Data Portability)
# ============================================================================


@router.get("/export", response_model=ExportResponse)
async def export_user_data(
    user_id: str = "anonymous",  # TODO: Get from auth context
    org_id: str = "default",  # TODO: Get from tenant context
) -> ExportResponse:
    """
    Export all user data (GDPR Article 20).

    Returns a JSON file containing all data associated with the user,
    including runs, feedback, memories, and organization data.
    """
    service = get_export_service()

    try:
        export_data = await service.export_user_data(
            user_id=user_id,
            org_id=org_id,
            format=ExportFormat.JSON,
        )

        metadata = export_data["export_metadata"]

        return ExportResponse(
            export_id=metadata["export_id"],
            user_id=metadata["user_id"],
            org_id=metadata["org_id"],
            exported_at=metadata["exported_at"],
            total_documents=metadata["total_documents"],
            file_size_bytes=metadata["file_size_bytes"],
            collections_exported=metadata["collections_exported"],
            data=export_data["data"],
        )

    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/summary")
async def get_export_summary(
    user_id: str = "anonymous",
    org_id: str = "default",
) -> Dict[str, Any]:
    """
    Get summary of data available for export.

    Useful for showing user what data exists before full export.
    """
    service = get_export_service()
    return await service.get_export_summary(user_id=user_id, org_id=org_id)


# ============================================================================
# Privacy Dashboard
# ============================================================================


@router.get("/privacy", response_model=PrivacyDashboardResponse)
async def get_privacy_dashboard(
    user_id: str = "anonymous",
    org_id: str = "default",
) -> PrivacyDashboardResponse:
    """
    Get privacy dashboard data.

    Returns:
    - Summary of stored data
    - Erasure request history
    - Encryption status
    """
    export_service = get_export_service()
    erasure_service = get_erasure_service()
    crypto_service = get_crypto_service()

    # Get data summary
    data_summary = await export_service.get_export_summary(
        user_id=user_id,
        org_id=org_id,
    )

    # Get erasure requests
    erasure_requests = await erasure_service.get_user_requests(user_id)

    return PrivacyDashboardResponse(
        user_id=user_id,
        org_id=org_id,
        data_summary=data_summary,
        erasure_requests=[r.to_dict() for r in erasure_requests],
        encryption_status=crypto_service.get_stats(),
    )


@router.get("/privacy/stats")
async def get_privacy_stats() -> Dict[str, Any]:
    """Get privacy service statistics."""
    return {
        "erasure": get_erasure_service().get_stats(),
        "export": get_export_service().get_stats(),
        "crypto": get_crypto_service().get_stats(),
    }
