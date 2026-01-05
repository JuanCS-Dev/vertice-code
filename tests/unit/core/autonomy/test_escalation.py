"""
Unit tests for the EscalationManager.
"""

import pytest
import asyncio
import sys
from unittest.mock import MagicMock

# WORKAROUND: Mock the problematic protobuf-related modules before they are imported.
# This is a workaround for a known protobuf dependency conflict in the test environment
# that causes a `TypeError` during test collection. The `escalation` module itself
# does not depend on `core.protocols`, but the import chain through `core/__init__.py`
# triggers the issue.
sys.modules['core.protocols'] = MagicMock()


from core.autonomy.escalation import EscalationManager
from core.autonomy.types import AutonomyDecision, EscalationReason

@pytest.fixture
def manager():
    """Provides an EscalationManager instance."""
    return EscalationManager()

@pytest.fixture
def decision():
    """Provides a sample AutonomyDecision."""
    return AutonomyDecision(action="test_action", confidence=0.7, risk_level=0.5, context={})

def test_create_escalation(manager, decision):
    """Test creating a new escalation."""
    request = manager.create_escalation(decision, EscalationReason.LOW_CONFIDENCE)
    assert request is not None
    assert request.reason == EscalationReason.LOW_CONFIDENCE
    assert len(manager.get_pending()) == 1

def test_respond_to_escalation(manager, decision):
    """Test responding to an escalation."""
    request = manager.create_escalation(decision, EscalationReason.LOW_CONFIDENCE)
    assert manager.respond(request.id, "approve") is True
    assert len(manager.get_pending()) == 0
    resolved_request = manager.get_request(request.id)
    assert resolved_request.human_response == "approve"

def test_cancel_escalation(manager, decision):
    """Test cancelling an escalation."""
    request = manager.create_escalation(decision, EscalationReason.LOW_CONFIDENCE)
    assert manager.cancel(request.id) is True
    assert len(manager.get_pending()) == 0
    resolved_request = manager.get_request(request.id)
    assert resolved_request.human_response == "cancelled"

@pytest.mark.asyncio
async def test_wait_for_response(manager, decision):
    """Test waiting for a response to an escalation."""
    request = manager.create_escalation(decision, EscalationReason.LOW_CONFIDENCE)

    async def responder():
        await asyncio.sleep(0.1)
        manager.respond(request.id, "approved")

    asyncio.create_task(responder())
    response = await manager.wait_for_response(request.id)
    assert response == "approved"

@pytest.mark.asyncio
async def test_wait_for_response_timeout(manager, decision):
    """Test that wait_for_response times out correctly."""
    request = manager.create_escalation(decision, EscalationReason.LOW_CONFIDENCE)
    request.timeout_seconds = 0.1
    response = await manager.wait_for_response(request.id)
    assert response is None
    assert len(manager.get_pending()) == 0

def test_get_stats(manager, decision):
    """Test the statistics calculation."""
    req1 = manager.create_escalation(decision, EscalationReason.LOW_CONFIDENCE)
    req2 = manager.create_escalation(decision, EscalationReason.HIGH_RISK)
    manager.respond(req1.id, "approve")
    manager.respond(req2.id, "deny")

    stats = manager.get_stats()
    assert stats["total_escalations"] == 2
    assert stats["approved_count"] == 1
    assert stats["denied_count"] == 1
    assert stats["by_reason"]["low_confidence"] == 1
    assert stats["by_reason"]["high_risk"] == 1

# Clean up the workaround mock
del sys.modules['core.protocols']
