"""
Tests for Trust Engine with Authorization Context.

Sprint 5: Test coverage for governance module.
Tests the Anthropic two-party authorization pattern implementation.
"""

import pytest
from datetime import datetime, timezone

from vertice_governance.justica.trust import (
    TrustEngine,
    TrustLevel,
    TrustFactor,
    TrustEvent,
    AuthorizationContext,
    AuthorizationLevel,
)
from vertice_governance.justica.constitution import (
    Severity,
    ViolationType,
)


class TestAuthorizationContext:
    """Tests for AuthorizationContext dataclass."""

    def test_create_basic_context(self):
        """Test creating a basic authorization context."""
        ctx = AuthorizationContext(
            principal="admin@example.com",
            level=AuthorizationLevel.ADMIN,
            reason="Testing",
        )

        assert ctx.principal == "admin@example.com"
        assert ctx.level == AuthorizationLevel.ADMIN
        assert ctx.reason == "Testing"
        assert ctx.ticket_id is None
        assert ctx.second_party is None

    def test_two_party_auth_detection(self):
        """Test two-party authorization detection."""
        # Without second party
        ctx1 = AuthorizationContext(
            principal="admin@example.com",
            level=AuthorizationLevel.ADMIN,
            reason="Testing",
        )
        assert not ctx1.has_two_party_auth()

        # With second party (different person)
        ctx2 = AuthorizationContext(
            principal="admin@example.com",
            level=AuthorizationLevel.RSO,
            reason="Critical operation",
            second_party="supervisor@example.com",
        )
        assert ctx2.has_two_party_auth()

        # Same person (not valid two-party)
        ctx3 = AuthorizationContext(
            principal="admin@example.com",
            level=AuthorizationLevel.RSO,
            reason="Testing",
            second_party="admin@example.com",
        )
        assert not ctx3.has_two_party_auth()

    def test_to_dict(self):
        """Test serialization to dictionary."""
        ctx = AuthorizationContext(
            principal="user@example.com",
            level=AuthorizationLevel.OPERATOR,
            reason="Routine maintenance",
            ticket_id="INC-12345",
        )

        data = ctx.to_dict()
        assert data["principal"] == "user@example.com"
        assert data["level"] == "OPERATOR"
        assert data["reason"] == "Routine maintenance"
        assert data["ticket_id"] == "INC-12345"
        assert "timestamp" in data


class TestTrustLevel:
    """Tests for TrustLevel enum."""

    def test_from_factor_maximum(self):
        """Test MAXIMUM level threshold."""
        assert TrustLevel.from_factor(0.96) == TrustLevel.MAXIMUM
        assert TrustLevel.from_factor(1.0) == TrustLevel.MAXIMUM

    def test_from_factor_high(self):
        """Test HIGH level threshold."""
        assert TrustLevel.from_factor(0.81) == TrustLevel.HIGH
        assert TrustLevel.from_factor(0.95) == TrustLevel.HIGH

    def test_from_factor_standard(self):
        """Test STANDARD level threshold."""
        assert TrustLevel.from_factor(0.61) == TrustLevel.STANDARD
        assert TrustLevel.from_factor(0.80) == TrustLevel.STANDARD

    def test_from_factor_reduced(self):
        """Test REDUCED level threshold."""
        assert TrustLevel.from_factor(0.41) == TrustLevel.REDUCED
        assert TrustLevel.from_factor(0.60) == TrustLevel.REDUCED

    def test_from_factor_minimal(self):
        """Test MINIMAL level threshold."""
        assert TrustLevel.from_factor(0.21) == TrustLevel.MINIMAL
        assert TrustLevel.from_factor(0.40) == TrustLevel.MINIMAL

    def test_from_factor_suspended(self):
        """Test SUSPENDED level threshold."""
        assert TrustLevel.from_factor(0.19) == TrustLevel.SUSPENDED
        assert TrustLevel.from_factor(0.0) == TrustLevel.SUSPENDED


class TestTrustEngine:
    """Tests for TrustEngine with authorization."""

    @pytest.fixture
    def engine(self):
        """Create a fresh TrustEngine for each test."""
        return TrustEngine()

    @pytest.fixture
    def admin_context(self):
        """Create an ADMIN authorization context."""
        return AuthorizationContext(
            principal="admin@example.com",
            level=AuthorizationLevel.ADMIN,
            reason="Test operation",
        )

    @pytest.fixture
    def operator_context(self):
        """Create an OPERATOR authorization context."""
        return AuthorizationContext(
            principal="operator@example.com",
            level=AuthorizationLevel.OPERATOR,
            reason="Test operation",
        )

    @pytest.fixture
    def rso_context(self):
        """Create an RSO (Responsible Scaling Officer) context."""
        return AuthorizationContext(
            principal="rso@example.com",
            level=AuthorizationLevel.RSO,
            reason="Critical review",
            ticket_id="INC-99999",
        )

    def test_get_or_create_trust_factor(self, engine):
        """Test creating and retrieving trust factors."""
        tf = engine.get_or_create_trust_factor("agent-001")

        assert tf.agent_id == "agent-001"
        assert tf.current_factor == 1.0
        assert tf.level == TrustLevel.MAXIMUM
        assert not tf.is_suspended

    def test_record_violation_reduces_trust(self, engine):
        """Test that violations reduce trust factor."""
        engine.record_violation(
            agent_id="agent-001",
            violation_type=ViolationType.SCOPE_VIOLATION,
            severity=Severity.MEDIUM,
            description="Agent accessed data outside scope",
        )

        tf = engine.get_trust_factor("agent-001")
        assert tf.current_factor < 1.0
        assert tf.total_violations == 1

    def test_critical_violation_suspends_agent(self, engine):
        """Test that critical violations cause suspension."""
        engine.record_violation(
            agent_id="agent-002",
            violation_type=ViolationType.DATA_EXFILTRATION,
            severity=Severity.CRITICAL,
            description="Attempted data exfiltration",
        )

        tf = engine.get_trust_factor("agent-002")
        assert tf.is_suspended
        assert tf.suspension_reason is not None
        assert "crítica" in tf.suspension_reason.lower()

    def test_good_actions_increase_trust(self, engine):
        """Test that good actions increase trust."""
        # First reduce trust
        engine.record_violation(
            agent_id="agent-003",
            violation_type=ViolationType.SCOPE_VIOLATION,
            severity=Severity.LOW,
        )

        initial_factor = engine.get_trust_factor("agent-003").current_factor

        # Then do good actions
        for _ in range(10):
            engine.record_good_action("agent-003", "Successful operation")

        final_factor = engine.get_trust_factor("agent-003").current_factor
        assert final_factor > initial_factor

    def test_lift_suspension_requires_authorization(self, engine):
        """Test that lift_suspension requires AuthorizationContext."""
        # Suspend an agent
        engine.record_violation(
            agent_id="agent-004",
            violation_type=ViolationType.DATA_EXFILTRATION,
            severity=Severity.CRITICAL,
        )

        # Try to lift without authorization
        with pytest.raises(ValueError, match="AuthorizationContext required"):
            engine.lift_suspension("agent-004", None)

    def test_lift_suspension_requires_admin_level(self, engine, operator_context):
        """Test that lift_suspension requires ADMIN level."""
        # Suspend an agent (non-critical)
        tf = engine.get_or_create_trust_factor("agent-005")
        tf.is_suspended = True
        tf.suspension_reason = "Manual suspension for testing"

        # Try with OPERATOR level (should fail)
        with pytest.raises(PermissionError, match="Insufficient authorization"):
            engine.lift_suspension("agent-005", operator_context)

    def test_lift_suspension_success_with_admin(self, engine, admin_context):
        """Test successful lift with ADMIN authorization."""
        # Suspend an agent (non-critical)
        tf = engine.get_or_create_trust_factor("agent-006")
        tf.is_suspended = True
        tf.suspension_reason = "Manual suspension for testing"

        # Lift with ADMIN level
        result = engine.lift_suspension("agent-006", admin_context)

        assert result is True
        assert not tf.is_suspended
        assert tf.suspension_reason is None

    def test_critical_suspension_requires_rso(self, engine, admin_context, rso_context):
        """Test that critical suspensions require RSO level to lift."""
        # Create critical suspension
        engine.record_violation(
            agent_id="agent-007",
            violation_type=ViolationType.MALICIOUS_CODE,
            severity=Severity.CRITICAL,
        )

        tf = engine.get_trust_factor("agent-007")
        assert tf.is_suspended
        assert "crítica" in tf.suspension_reason.lower()

        # Try with ADMIN level (should fail for critical)
        with pytest.raises(PermissionError, match="Insufficient authorization"):
            engine.lift_suspension("agent-007", admin_context)

        # Try with RSO level (should succeed)
        result = engine.lift_suspension("agent-007", rso_context)
        assert result is True
        assert not tf.is_suspended

    def test_lift_nonexistent_agent_returns_false(self, engine, admin_context):
        """Test lifting suspension for non-existent agent."""
        result = engine.lift_suspension("nonexistent-agent", admin_context)
        assert result is False

    def test_lift_unsuspended_agent_returns_false(self, engine, admin_context):
        """Test lifting suspension for agent that's not suspended."""
        engine.get_or_create_trust_factor("agent-008")
        result = engine.lift_suspension("agent-008", admin_context)
        assert result is False

    def test_authorization_audit_trail(self, engine, admin_context):
        """Test that authorization is recorded in audit trail."""
        # Suspend an agent
        tf = engine.get_or_create_trust_factor("agent-009")
        tf.is_suspended = True
        tf.suspension_reason = "Test suspension"

        # Lift with authorization
        engine.lift_suspension("agent-009", admin_context)

        # Check last event has authorization context
        last_event = tf.events[-1]
        assert last_event.event_type == "suspension_lifted"
        assert "authorization" in last_event.context
        assert last_event.context["authorization"]["principal"] == "admin@example.com"

    def test_global_metrics(self, engine):
        """Test global metrics collection."""
        # Create some activity
        engine.record_good_action("agent-001")
        engine.record_violation(
            "agent-002",
            ViolationType.SCOPE_VIOLATION,
            Severity.LOW,
        )

        metrics = engine.get_global_metrics()

        assert metrics["total_agents"] == 2
        assert metrics["total_events"] >= 2
        assert "average_trust_factor" in metrics
        assert "agents_by_level" in metrics


class TestTrustEngineLegacy:
    """Tests for deprecated lift_suspension_unsafe method."""

    def test_lift_suspension_unsafe_deprecated(self):
        """Test that lift_suspension_unsafe emits deprecation warning."""
        engine = TrustEngine()
        tf = engine.get_or_create_trust_factor("agent-legacy")
        tf.is_suspended = True
        tf.suspension_reason = "Test"

        with pytest.warns(DeprecationWarning, match="lift_suspension_unsafe"):
            result = engine.lift_suspension_unsafe("agent-legacy", "Migration test")

        assert result is True
        assert not tf.is_suspended
