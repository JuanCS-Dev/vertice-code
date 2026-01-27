"""
Jules REST API Router.

Endpoints for:
- Triggering scans
- Requesting fixes
- Managing tasks
- GitHub webhooks

Part of M11: Autonomous Maintenance with Google Jules.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from jules.service import get_jules_service
from jules.scanner import CodeScanner, ScanType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/jules", tags=["jules"])

# Global scanner instance
_scanner: Optional[CodeScanner] = None


def get_scanner() -> CodeScanner:
    """Get global scanner instance."""
    global _scanner
    if _scanner is None:
        _scanner = CodeScanner()
    return _scanner


# ============================================================================
# Request/Response Models
# ============================================================================


class ScanRequest(BaseModel):
    """Request to trigger a scan."""

    scan_types: List[str] = Field(
        default=["security", "dependencies", "todos"],
        description="Types of scans to run",
    )


class FixRequest(BaseModel):
    """Request to fix an issue."""

    description: str = Field(..., description="Description of the issue to fix")
    target_files: Optional[List[str]] = Field(None, description="Files to focus on")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class RefactorRequest(BaseModel):
    """Request to refactor code."""

    description: str = Field(..., description="Refactoring description")
    target_files: List[str] = Field(..., description="Files to refactor")
    goals: Optional[List[str]] = Field(None, description="Refactoring goals")


class DependencyUpdateRequest(BaseModel):
    """Request to update dependencies."""

    update_type: str = Field(
        default="minor",
        description="Type of updates: minor, major, security",
    )


class TaskResponse(BaseModel):
    """Task response."""

    task_id: str
    task_type: str
    description: str
    status: str
    created_at: str


# ============================================================================
# Scan Endpoints
# ============================================================================


@router.post("/scan", response_model=TaskResponse)
async def trigger_scan(request: ScanRequest) -> TaskResponse:
    """
    Trigger a code scan.

    Scans available:
    - security: Vulnerability detection
    - dependencies: Outdated/vulnerable dependencies
    - todos: TODO/FIXME tracking
    - deprecations: Deprecated API usage
    """
    service = get_jules_service()

    if not service.is_available:
        raise HTTPException(
            status_code=503,
            detail="Jules service not configured",
        )

    try:
        task = await service.trigger_scan(request.scan_types)

        return TaskResponse(
            task_id=task["task_id"],
            task_type=task["task_type"],
            description=task["description"],
            status=task["status"],
            created_at=task["created_at"],
        )

    except Exception as e:
        logger.error(f"Scan trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan/run")
async def run_scan_now(request: ScanRequest) -> Dict[str, Any]:
    """
    Run a scan immediately and return results.

    Unlike /scan which queues a task, this runs synchronously.
    """
    scanner = get_scanner()

    # Convert string scan types to enum
    scan_types = []
    for st in request.scan_types:
        try:
            scan_types.append(ScanType(st))
        except ValueError:
            pass

    result = await scanner.scan(scan_types)
    return result.to_dict()


@router.get("/scan/latest")
async def get_latest_scan() -> Dict[str, Any]:
    """Get the most recent scan result."""
    scanner = get_scanner()
    result = scanner.get_latest_scan()

    if not result:
        raise HTTPException(status_code=404, detail="No scans found")

    return result.to_dict()


@router.get("/scan/history")
async def get_scan_history(limit: int = 10) -> List[Dict[str, Any]]:
    """Get scan history."""
    scanner = get_scanner()
    return scanner.get_scan_history(limit)


# ============================================================================
# Fix/Refactor Endpoints
# ============================================================================


@router.post("/fix", response_model=TaskResponse)
async def request_fix(request: FixRequest) -> TaskResponse:
    """
    Request Jules to fix an issue.

    Jules will analyze the issue and create a PR with the fix.
    """
    service = get_jules_service()

    if not service.is_available:
        raise HTTPException(
            status_code=503,
            detail="Jules service not configured",
        )

    try:
        task = await service.request_fix(
            issue_description=request.description,
            target_files=request.target_files,
            context=request.context,
        )

        return TaskResponse(
            task_id=task["task_id"],
            task_type=task["task_type"],
            description=task["description"],
            status=task["status"],
            created_at=task["created_at"],
        )

    except Exception as e:
        logger.error(f"Fix request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refactor", response_model=TaskResponse)
async def request_refactor(request: RefactorRequest) -> TaskResponse:
    """
    Request Jules to refactor code.

    Specify files and goals for the refactoring.
    """
    service = get_jules_service()

    if not service.is_available:
        raise HTTPException(
            status_code=503,
            detail="Jules service not configured",
        )

    try:
        task = await service.request_refactor(
            description=request.description,
            target_files=request.target_files,
            goals=request.goals,
        )

        return TaskResponse(
            task_id=task["task_id"],
            task_type=task["task_type"],
            description=task["description"],
            status=task["status"],
            created_at=task["created_at"],
        )

    except Exception as e:
        logger.error(f"Refactor request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dependencies/update", response_model=TaskResponse)
async def update_dependencies(request: DependencyUpdateRequest) -> TaskResponse:
    """
    Request dependency updates.

    Types:
    - minor: Update to latest minor versions
    - major: Update to latest major versions
    - security: Only security patches
    """
    service = get_jules_service()

    if not service.is_available:
        raise HTTPException(
            status_code=503,
            detail="Jules service not configured",
        )

    try:
        task = await service.update_dependencies(request.update_type)

        return TaskResponse(
            task_id=task["task_id"],
            task_type=task["task_type"],
            description=task["description"],
            status=task["status"],
            created_at=task["created_at"],
        )

    except Exception as e:
        logger.error(f"Dependency update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Task Management
# ============================================================================


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """List Jules tasks."""
    service = get_jules_service()
    return await service.list_tasks(status=status, limit=limit)


@router.get("/tasks/{task_id}")
async def get_task(task_id: str) -> Dict[str, Any]:
    """Get task status by ID."""
    service = get_jules_service()
    task = await service.get_task_status(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


# ============================================================================
# GitHub Webhook
# ============================================================================


@router.post("/webhooks/github")
async def handle_github_webhook(request: Request) -> Dict[str, Any]:
    """
    Handle GitHub webhook events.

    Events handled:
    - issues (labeled with 'jules')
    - check_run (build failures)
    - pull_request_review
    """
    service = get_jules_service()

    # Get event type
    event_type = request.headers.get("X-GitHub-Event", "")

    # Parse payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # TODO: Verify webhook signature using X-Hub-Signature-256

    try:
        result = await service.handle_github_webhook(event_type, payload)
        return result

    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Stats & Health
# ============================================================================


@router.get("/stats")
async def get_jules_stats() -> Dict[str, Any]:
    """Get Jules service statistics."""
    service = get_jules_service()
    scanner = get_scanner()

    return {
        "service": service.get_stats(),
        "scanner": scanner.get_stats(),
    }


@router.get("/health")
async def jules_health() -> Dict[str, Any]:
    """Check Jules service health."""
    service = get_jules_service()

    return {
        "status": "ok" if service.is_available else "degraded",
        "available": service.is_available,
        "message": (
            "Jules ready for autonomous maintenance"
            if service.is_available
            else "Jules not configured - set JULES_GITHUB_* environment variables"
        ),
    }
