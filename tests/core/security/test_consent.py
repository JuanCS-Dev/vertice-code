"""
Tests for User Consent Flow Implementation.

Tests MCP 2025-11-25 consent requirements.

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock

import pytest

from core.security.consent import (
    ConsentLevel,
    OperationCategory,
    ConsentRequest,
    ConsentRecord,
    ConsentManager,
    requires_consent,
    DEFAULT_CONSENT_LEVELS,
)


# =============================================================================
# CONSENT LEVEL TESTS
# =============================================================================


class TestConsentLevels:
    """Tests for consent level configuration."""

    def test_default_levels_exist(self) -> None:
        """All categories have default levels."""
        for category in OperationCategory:
            assert category in DEFAULT_CONSENT_LEVELS

    def test_dangerous_operations_elevated(self) -> None:
        """Dangerous operations require elevated consent."""
        assert DEFAULT_CONSENT_LEVELS[OperationCategory.FILE_DELETE] == ConsentLevel.ELEVATED
        assert DEFAULT_CONSENT_LEVELS[OperationCategory.SYSTEM_COMMAND] == ConsentLevel.ELEVATED
        assert DEFAULT_CONSENT_LEVELS[OperationCategory.CREDENTIAL_ACCESS] == ConsentLevel.ELEVATED

    def test_read_operations_minimal(self) -> None:
        """Read operations require no consent."""
        assert DEFAULT_CONSENT_LEVELS[OperationCategory.FILE_READ] == ConsentLevel.NONE

    def test_write_operations_confirm(self) -> None:
        """Write operations require confirmation."""
        assert DEFAULT_CONSENT_LEVELS[OperationCategory.FILE_WRITE] == ConsentLevel.CONFIRM


# =============================================================================
# CONSENT REQUEST TESTS
# =============================================================================


class TestConsentRequest:
    """Tests for ConsentRequest."""

    def test_minimal_request(self) -> None:
        """Minimal consent request."""
        request = ConsentRequest(
            operation="Read file",
            category=OperationCategory.FILE_READ,
            tool_name="read_file",
        )

        assert request.operation == "Read file"
        assert request.category == OperationCategory.FILE_READ
        assert request.tool_name == "read_file"
        assert request.resources == []

    def test_full_request(self) -> None:
        """Full consent request with all fields."""
        request = ConsentRequest(
            operation="Delete user data",
            category=OperationCategory.FILE_DELETE,
            tool_name="delete_files",
            details="This will permanently remove the specified files",
            resources=["/tmp/data.json", "/tmp/cache/"],
            timeout=120,
        )

        assert request.details is not None
        assert len(request.resources) == 2
        assert request.timeout == 120

    def test_to_display_dict(self) -> None:
        """Convert to display format."""
        request = ConsentRequest(
            operation="Execute command",
            category=OperationCategory.SYSTEM_COMMAND,
            tool_name="bash",
            details="Run: ls -la",
            resources=["/home/user"],
        )
        display = request.to_display_dict()

        assert display["operation"] == "Execute command"
        assert display["category"] == "system_command"
        assert display["tool"] == "bash"
        assert display["consent_level"] == "elevated"

    def test_consent_level_property(self) -> None:
        """Consent level derived from category."""
        request = ConsentRequest(
            operation="Write config",
            category=OperationCategory.FILE_WRITE,
            tool_name="write_file",
        )

        assert request.consent_level == ConsentLevel.CONFIRM

    def test_request_id_unique(self) -> None:
        """Request IDs are deterministic and unique."""
        request1 = ConsentRequest(
            operation="op1",
            category=OperationCategory.FILE_WRITE,
            tool_name="tool1",
        )
        request2 = ConsentRequest(
            operation="op2",
            category=OperationCategory.FILE_WRITE,
            tool_name="tool1",
        )
        request3 = ConsentRequest(
            operation="op1",
            category=OperationCategory.FILE_WRITE,
            tool_name="tool1",
        )

        assert request1.request_id() != request2.request_id()
        assert request1.request_id() == request3.request_id()  # Same params = same ID


# =============================================================================
# CONSENT RECORD TESTS
# =============================================================================


class TestConsentRecord:
    """Tests for ConsentRecord."""

    def test_granted_record(self) -> None:
        """Record of granted consent."""
        record = ConsentRecord(
            request_id="abc123",
            granted=True,
            scope="session",
        )

        assert record.granted is True
        assert record.is_valid() is True

    def test_denied_record(self) -> None:
        """Record of denied consent."""
        record = ConsentRecord(
            request_id="abc123",
            granted=False,
        )

        assert record.granted is False
        assert record.is_valid() is False

    def test_expired_record(self) -> None:
        """Expired consent record."""
        record = ConsentRecord(
            request_id="abc123",
            granted=True,
            expires_at=time.time() - 100,  # Expired 100s ago
        )

        assert record.is_valid() is False

    def test_valid_with_future_expiry(self) -> None:
        """Consent valid with future expiry."""
        record = ConsentRecord(
            request_id="abc123",
            granted=True,
            expires_at=time.time() + 3600,  # Expires in 1 hour
        )

        assert record.is_valid() is True

    def test_to_audit_dict(self) -> None:
        """Convert to audit format."""
        record = ConsentRecord(
            request_id="abc123",
            granted=True,
            user_id="user@example.com",
            scope="persistent",
        )
        audit = record.to_audit_dict()

        assert audit["request_id"] == "abc123"
        assert audit["granted"] is True
        assert audit["user_id"] == "user@example.com"
        assert audit["scope"] == "persistent"


# =============================================================================
# CONSENT MANAGER TESTS
# =============================================================================


class TestConsentManager:
    """Tests for ConsentManager."""

    @pytest.fixture
    def manager(self) -> ConsentManager:
        """Create test manager."""
        return ConsentManager()

    @pytest.mark.asyncio
    async def test_auto_approve_none_level(self, manager: ConsentManager) -> None:
        """NONE level auto-approves."""
        result = await manager.request_consent(
            operation="Read file",
            category=OperationCategory.FILE_READ,
            tool_name="read_file",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_notify_level_proceeds(self, manager: ConsentManager) -> None:
        """NOTIFY level proceeds with logging."""
        result = await manager.request_consent(
            operation="Fetch URL",
            category=OperationCategory.NETWORK_REQUEST,
            tool_name="http_get",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_no_callback_denies(self, manager: ConsentManager) -> None:
        """Without callback, CONFIRM level denies."""
        result = await manager.request_consent(
            operation="Write config",
            category=OperationCategory.FILE_WRITE,
            tool_name="write_file",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_callback_grants(self, manager: ConsentManager) -> None:
        """Callback that grants consent."""
        callback = AsyncMock(return_value=True)
        manager.set_consent_callback(callback)

        result = await manager.request_consent(
            operation="Write config",
            category=OperationCategory.FILE_WRITE,
            tool_name="write_file",
        )

        assert result is True
        callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_denies(self, manager: ConsentManager) -> None:
        """Callback that denies consent."""
        callback = AsyncMock(return_value=False)
        manager.set_consent_callback(callback)

        result = await manager.request_consent(
            operation="Delete files",
            category=OperationCategory.FILE_DELETE,
            tool_name="delete_file",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_callback_error_denies(self, manager: ConsentManager) -> None:
        """Callback error results in denial."""
        callback = AsyncMock(side_effect=RuntimeError("UI crashed"))
        manager.set_consent_callback(callback)

        result = await manager.request_consent(
            operation="Write file",
            category=OperationCategory.FILE_WRITE,
            tool_name="write_file",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_session_consent_reused(self, manager: ConsentManager) -> None:
        """Session scope consent is reused."""
        callback = AsyncMock(return_value=True)
        manager.set_consent_callback(callback)

        # First request
        await manager.request_consent(
            operation="Write config",
            category=OperationCategory.FILE_WRITE,
            tool_name="write_file",
            scope="session",
        )

        # Second identical request
        result = await manager.request_consent(
            operation="Write config",
            category=OperationCategory.FILE_WRITE,
            tool_name="write_file",
            scope="session",
        )

        assert result is True
        # Callback only called once (first time)
        assert callback.call_count == 1

    @pytest.mark.asyncio
    async def test_one_time_consent_not_reused(self, manager: ConsentManager) -> None:
        """One-time scope consent requires new approval."""
        callback = AsyncMock(return_value=True)
        manager.set_consent_callback(callback)

        # First request
        await manager.request_consent(
            operation="Write config",
            category=OperationCategory.FILE_WRITE,
            tool_name="write_file",
            scope="one-time",
        )

        # Second identical request
        await manager.request_consent(
            operation="Write config",
            category=OperationCategory.FILE_WRITE,
            tool_name="write_file",
            scope="one-time",
        )

        # Callback called both times
        assert callback.call_count == 2

    def test_custom_consent_level(self, manager: ConsentManager) -> None:
        """Override consent level for category."""
        manager.set_consent_level(
            OperationCategory.FILE_WRITE, ConsentLevel.NONE
        )

        level = manager.get_consent_level(OperationCategory.FILE_WRITE)
        assert level == ConsentLevel.NONE

    @pytest.mark.asyncio
    async def test_revoke_consent(self, manager: ConsentManager) -> None:
        """Revoke previously granted consent."""
        callback = AsyncMock(return_value=True)
        manager.set_consent_callback(callback)

        await manager.request_consent(
            operation="Write config",
            category=OperationCategory.FILE_WRITE,
            tool_name="write_file",
            scope="session",
        )

        # Get request ID
        request = ConsentRequest(
            operation="Write config",
            category=OperationCategory.FILE_WRITE,
            tool_name="write_file",
        )
        request_id = request.request_id()

        # Revoke
        revoked = manager.revoke_consent(request_id)
        assert revoked is True

        # Now consent is not valid
        callback.return_value = False
        await manager.request_consent(
            operation="Write config",
            category=OperationCategory.FILE_WRITE,
            tool_name="write_file",
            scope="session",
        )
        # Callback should be called again since consent was revoked
        assert callback.call_count == 2

    def test_revoke_nonexistent(self, manager: ConsentManager) -> None:
        """Revoking nonexistent consent returns False."""
        result = manager.revoke_consent("nonexistent_id")
        assert result is False

    def test_clear_expired(self, manager: ConsentManager) -> None:
        """Clear expired records."""
        # Add expired record directly
        manager._records["expired"] = ConsentRecord(
            request_id="expired",
            granted=True,
            expires_at=time.time() - 100,
        )
        manager._records["valid"] = ConsentRecord(
            request_id="valid",
            granted=True,
            expires_at=time.time() + 3600,
        )

        cleared = manager.clear_expired()

        assert cleared == 1
        assert "expired" not in manager._records
        assert "valid" in manager._records

    @pytest.mark.asyncio
    async def test_audit_log(self, manager: ConsentManager) -> None:
        """Audit log records decisions."""
        callback = AsyncMock(return_value=True)
        manager.set_consent_callback(callback)

        await manager.request_consent(
            operation="Write config",
            category=OperationCategory.FILE_WRITE,
            tool_name="write_file",
        )

        audit = manager.get_audit_log()
        assert len(audit) == 1
        assert audit[0]["tool_name"] == "write_file"
        assert audit[0]["granted"] is True


# =============================================================================
# DECORATOR TESTS
# =============================================================================


class TestRequiresConsentDecorator:
    """Tests for @requires_consent decorator."""

    @pytest.mark.asyncio
    async def test_decorator_grants(self) -> None:
        """Decorator allows execution when granted."""
        @requires_consent(OperationCategory.FILE_WRITE, "Write test file")
        async def write_file(path: str) -> str:
            return f"wrote to {path}"

        manager = ConsentManager()
        callback = AsyncMock(return_value=True)
        manager.set_consent_callback(callback)

        result = await write_file("/tmp/test", consent_manager=manager)
        assert result == "wrote to /tmp/test"

    @pytest.mark.asyncio
    async def test_decorator_denies(self) -> None:
        """Decorator raises when denied."""
        @requires_consent(OperationCategory.FILE_DELETE, "Delete file")
        async def delete_file(path: str) -> str:
            return f"deleted {path}"

        manager = ConsentManager()
        callback = AsyncMock(return_value=False)
        manager.set_consent_callback(callback)

        with pytest.raises(PermissionError, match="Consent denied"):
            await delete_file("/tmp/test", consent_manager=manager)

    @pytest.mark.asyncio
    async def test_decorator_without_manager(self) -> None:
        """Decorator allows execution without manager."""
        @requires_consent(OperationCategory.FILE_WRITE)
        async def write_file(path: str) -> str:
            return f"wrote to {path}"

        # No consent_manager passed = no consent check
        result = await write_file("/tmp/test")
        assert result == "wrote to /tmp/test"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestConsentIntegration:
    """Integration tests for consent flows."""

    @pytest.mark.asyncio
    async def test_dangerous_operation_flow(self) -> None:
        """Full flow for dangerous operation."""
        manager = ConsentManager()
        consent_granted = False

        async def ui_consent_handler(request: ConsentRequest) -> bool:
            nonlocal consent_granted
            # Simulate UI showing request and user approving
            assert request.consent_level == ConsentLevel.ELEVATED
            consent_granted = True
            return True

        manager.set_consent_callback(ui_consent_handler)

        result = await manager.request_consent(
            operation="Execute: rm -rf /tmp/cache",
            category=OperationCategory.SYSTEM_COMMAND,
            tool_name="bash",
            details="This will delete all cache files",
            resources=["/tmp/cache"],
        )

        assert result is True
        assert consent_granted is True

        # Verify audit
        audit = manager.get_audit_log()
        assert len(audit) == 1
        assert audit[0]["category"] == "system_command"
        assert audit[0]["granted"] is True
