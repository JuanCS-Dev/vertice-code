"""
User Consent Flow Implementation.
==================================

Implements MCP 2025-11-25 consent requirements for tool execution:
- Dangerous operations require explicit user approval
- Consent is logged for audit trail
- Consent can be revoked or have expiry

Security Requirements:
- File write/delete operations MUST request consent
- Network operations SHOULD request consent
- System commands MUST request consent
- Credentials access MUST request consent

References:
- MCP Security: https://modelcontextprotocol.io/specification/draft/basic/authorization
- OAuth 2.1 Consent: https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-12

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Awaitable

logger = logging.getLogger(__name__)


# =============================================================================
# CONSENT TYPES
# =============================================================================


class ConsentLevel(Enum):
    """Level of consent required for operations."""

    NONE = "none"  # No consent needed
    NOTIFY = "notify"  # Notify user, but proceed
    CONFIRM = "confirm"  # Require explicit confirmation
    ELEVATED = "elevated"  # Elevated privileges required


class OperationCategory(Enum):
    """Categories of operations requiring consent."""

    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    NETWORK_REQUEST = "network_request"
    SYSTEM_COMMAND = "system_command"
    CREDENTIAL_ACCESS = "credential_access"
    DATA_EXPORT = "data_export"
    CONFIGURATION_CHANGE = "configuration_change"


# Default consent levels per category
DEFAULT_CONSENT_LEVELS: Dict[OperationCategory, ConsentLevel] = {
    OperationCategory.FILE_READ: ConsentLevel.NONE,
    OperationCategory.FILE_WRITE: ConsentLevel.CONFIRM,
    OperationCategory.FILE_DELETE: ConsentLevel.ELEVATED,
    OperationCategory.NETWORK_REQUEST: ConsentLevel.NOTIFY,
    OperationCategory.SYSTEM_COMMAND: ConsentLevel.ELEVATED,
    OperationCategory.CREDENTIAL_ACCESS: ConsentLevel.ELEVATED,
    OperationCategory.DATA_EXPORT: ConsentLevel.CONFIRM,
    OperationCategory.CONFIGURATION_CHANGE: ConsentLevel.CONFIRM,
}


@dataclass
class ConsentRequest:
    """Request for user consent.

    Attributes:
        operation: Description of the operation
        category: Operation category
        tool_name: Name of tool requesting consent
        details: Additional details about the operation
        resources: Resources that will be accessed/modified
        timeout: How long to wait for consent (seconds)
    """

    operation: str
    category: OperationCategory
    tool_name: str
    details: Optional[str] = None
    resources: List[str] = field(default_factory=list)
    timeout: int = 60  # 1 minute default

    def to_display_dict(self) -> Dict[str, Any]:
        """Convert to display format for UI."""
        return {
            "operation": self.operation,
            "category": self.category.value,
            "tool": self.tool_name,
            "details": self.details,
            "resources": self.resources,
            "consent_level": DEFAULT_CONSENT_LEVELS.get(self.category, ConsentLevel.CONFIRM).value,
        }

    @property
    def consent_level(self) -> ConsentLevel:
        """Get required consent level."""
        return DEFAULT_CONSENT_LEVELS.get(self.category, ConsentLevel.CONFIRM)

    def request_id(self) -> str:
        """Generate unique ID for this request."""
        content = f"{self.tool_name}:{self.category.value}:{self.operation}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class ConsentRecord:
    """Record of granted consent.

    Attributes:
        request_id: ID of the consent request
        granted: Whether consent was granted
        granted_at: Timestamp when granted
        expires_at: Timestamp when consent expires (None = no expiry)
        user_id: User who granted consent
        scope: Scope of consent (one-time, session, persistent)
    """

    request_id: str
    granted: bool
    granted_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    user_id: Optional[str] = None
    scope: str = "one-time"  # one-time, session, persistent

    def is_valid(self) -> bool:
        """Check if consent is still valid."""
        if not self.granted:
            return False
        if self.expires_at and time.time() > self.expires_at:
            return False
        return True

    def to_audit_dict(self) -> Dict[str, Any]:
        """Convert to audit log format."""
        return {
            "request_id": self.request_id,
            "granted": self.granted,
            "granted_at": self.granted_at,
            "expires_at": self.expires_at,
            "user_id": self.user_id,
            "scope": self.scope,
        }


# =============================================================================
# CONSENT MANAGER
# =============================================================================


# Type for consent callback function
ConsentCallback = Callable[[ConsentRequest], Awaitable[bool]]


class ConsentManager:
    """Manages consent requests and records.

    Provides a centralized system for requesting and tracking
    user consent for sensitive operations.

    Example:
        >>> manager = ConsentManager()
        >>> manager.set_consent_callback(ui_consent_handler)
        >>> # Request consent for file write
        >>> granted = await manager.request_consent(
        ...     operation="Write to config.json",
        ...     category=OperationCategory.FILE_WRITE,
        ...     tool_name="edit_file",
        ...     resources=["/etc/config.json"],
        ... )
        >>> if granted:
        ...     # Proceed with operation
    """

    def __init__(self) -> None:
        """Initialize consent manager."""
        self._records: Dict[str, ConsentRecord] = {}
        self._consent_callback: Optional[ConsentCallback] = None
        self._audit_log: List[Dict[str, Any]] = []
        self._custom_levels: Dict[OperationCategory, ConsentLevel] = {}

    def set_consent_callback(self, callback: ConsentCallback) -> None:
        """Set callback for requesting consent from user.

        Args:
            callback: Async function that presents consent UI
        """
        self._consent_callback = callback

    def set_consent_level(self, category: OperationCategory, level: ConsentLevel) -> None:
        """Override consent level for a category.

        Args:
            category: Operation category
            level: New consent level
        """
        self._custom_levels[category] = level

    def get_consent_level(self, category: OperationCategory) -> ConsentLevel:
        """Get consent level for a category.

        Args:
            category: Operation category

        Returns:
            Required consent level
        """
        return self._custom_levels.get(
            category, DEFAULT_CONSENT_LEVELS.get(category, ConsentLevel.CONFIRM)
        )

    async def request_consent(
        self,
        operation: str,
        category: OperationCategory,
        tool_name: str,
        details: Optional[str] = None,
        resources: Optional[List[str]] = None,
        scope: str = "one-time",
        expires_in: Optional[int] = None,
    ) -> bool:
        """Request user consent for an operation.

        Args:
            operation: Description of operation
            category: Operation category
            tool_name: Name of requesting tool
            details: Additional details
            resources: Resources to be accessed
            scope: Consent scope (one-time, session, persistent)
            expires_in: Seconds until consent expires

        Returns:
            True if consent granted, False otherwise
        """
        request = ConsentRequest(
            operation=operation,
            category=category,
            tool_name=tool_name,
            details=details,
            resources=resources or [],
        )

        level = self.get_consent_level(category)

        # Check if consent level requires no action
        if level == ConsentLevel.NONE:
            self._log_audit(request, True, "auto-approved")
            return True

        # Check for existing valid consent (for persistent/session scopes)
        request_id = request.request_id()
        existing = self._records.get(request_id)
        if existing and existing.is_valid() and existing.scope != "one-time":
            self._log_audit(request, True, "existing-consent")
            return True

        # For NOTIFY level, log but proceed
        if level == ConsentLevel.NOTIFY:
            logger.info(f"Consent notification: {tool_name} - {operation}")
            self._log_audit(request, True, "notify-proceed")
            return True

        # Request consent via callback
        if not self._consent_callback:
            logger.warning(f"No consent callback set, denying: {tool_name} - {operation}")
            self._log_audit(request, False, "no-callback")
            return False

        try:
            granted = await self._consent_callback(request)
        except Exception as e:
            logger.error(f"Consent callback error: {e}")
            self._log_audit(request, False, f"error: {e}")
            return False

        # Record consent decision
        expires_at = None
        if expires_in:
            expires_at = time.time() + expires_in

        record = ConsentRecord(
            request_id=request_id,
            granted=granted,
            scope=scope,
            expires_at=expires_at,
        )
        self._records[request_id] = record

        self._log_audit(request, granted, "user-decision")
        return granted

    def revoke_consent(self, request_id: str) -> bool:
        """Revoke previously granted consent.

        Args:
            request_id: ID of consent to revoke

        Returns:
            True if consent was found and revoked
        """
        if request_id in self._records:
            self._records[request_id].granted = False
            self._audit_log.append(
                {
                    "action": "revoke",
                    "request_id": request_id,
                    "timestamp": time.time(),
                }
            )
            return True
        return False

    def clear_expired(self) -> int:
        """Clear expired consent records.

        Returns:
            Number of records cleared
        """
        expired = [rid for rid, record in self._records.items() if not record.is_valid()]
        for rid in expired:
            del self._records[rid]
        return len(expired)

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Get audit log of consent decisions.

        Returns:
            List of audit entries
        """
        return self._audit_log.copy()

    def _log_audit(
        self,
        request: ConsentRequest,
        granted: bool,
        reason: str,
    ) -> None:
        """Add entry to audit log."""
        entry = {
            "timestamp": time.time(),
            "tool_name": request.tool_name,
            "operation": request.operation,
            "category": request.category.value,
            "resources": request.resources,
            "granted": granted,
            "reason": reason,
        }
        self._audit_log.append(entry)
        logger.debug(f"Consent audit: {entry}")


# =============================================================================
# TOOL DECORATORS
# =============================================================================


def requires_consent(
    category: OperationCategory,
    description: Optional[str] = None,
) -> Callable:
    """Decorator to require consent before tool execution.

    Args:
        category: Operation category
        description: Operation description

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(
            *args: Any,
            consent_manager: Optional[ConsentManager] = None,
            **kwargs: Any,
        ) -> Any:
            if consent_manager:
                operation = description or f"Execute {func.__name__}"
                granted = await consent_manager.request_consent(
                    operation=operation,
                    category=category,
                    tool_name=func.__name__,
                )
                if not granted:
                    raise PermissionError(f"Consent denied for {func.__name__}: {operation}")
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ConsentLevel",
    "OperationCategory",
    "ConsentRequest",
    "ConsentRecord",
    "ConsentManager",
    "ConsentCallback",
    "requires_consent",
    "DEFAULT_CONSENT_LEVELS",
]
