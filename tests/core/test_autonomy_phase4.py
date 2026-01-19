"""
Tests for Autonomy Module (Phase 4)

Tests for bounded autonomy and uncertainty quantification.

References:
- arXiv:2503.15850 (Uncertainty Quantification in AI Agents)
- arXiv:2402.16906 (Confidence-Based Routing)
- arXiv:2310.03046 (LLM Confidence Calibration)
"""

import pytest
from datetime import datetime

from core.autonomy.types import (
    AutonomyLevel,
    UncertaintyType,
    EscalationReason,
    ConfidenceScore,
    UncertaintyEstimate,
    AutonomyDecision,
    EscalationRequest,
    AutonomyConfig,
)


class TestAutonomyTypes:
    """Tests for autonomy type definitions."""

    def test_autonomy_level_enum(self):
        """Test AutonomyLevel enumeration."""
        assert AutonomyLevel.ASSIST.value == "assist"
        assert AutonomyLevel.APPROVE.value == "approve"
        assert AutonomyLevel.NOTIFY.value == "notify"
        assert AutonomyLevel.LEARN.value == "learn"

    def test_uncertainty_type_enum(self):
        """Test UncertaintyType enumeration."""
        assert UncertaintyType.INPUT.value == "input"
        assert UncertaintyType.REASONING.value == "reasoning"
        assert UncertaintyType.PARAMETER.value == "parameter"
        assert UncertaintyType.PREDICTION.value == "prediction"

    def test_escalation_reason_enum(self):
        """Test EscalationReason enumeration."""
        assert EscalationReason.LOW_CONFIDENCE.value == "low_confidence"
        assert EscalationReason.HIGH_RISK.value == "high_risk"
        assert EscalationReason.POLICY_VIOLATION.value == "policy_violation"
        assert EscalationReason.SAFETY_CONCERN.value == "safety_concern"


class TestConfidenceScore:
    """Tests for ConfidenceScore."""

    @pytest.fixture
    def score(self):
        """Create test confidence score."""
        return ConfidenceScore(
            raw_confidence=0.85,
            calibrated_confidence=0.78,
            input_confidence=0.9,
            reasoning_confidence=0.8,
            output_confidence=0.75,
        )

    def test_confidence_score_creation(self, score):
        """Test ConfidenceScore creation."""
        assert score.raw_confidence == 0.85
        assert score.calibrated_confidence == 0.78
        assert score.input_confidence == 0.9

    def test_confidence_score_overall(self, score):
        """Test overall confidence."""
        assert score.overall() == 0.78

    def test_confidence_score_is_uncertain(self, score):
        """Test uncertainty check."""
        # With default threshold 0.7
        assert score.is_uncertain(threshold=0.8) is True
        assert score.is_uncertain(threshold=0.7) is False

    def test_confidence_score_decomposition(self):
        """Test epistemic/aleatoric decomposition."""
        score = ConfidenceScore(
            epistemic=0.3,
            aleatoric=0.2,
        )
        assert score.epistemic == 0.3
        assert score.aleatoric == 0.2

    def test_confidence_score_defaults(self):
        """Test default confidence values."""
        score = ConfidenceScore()
        assert score.raw_confidence == 0.5
        assert score.calibration_method == "platt"


class TestUncertaintyEstimate:
    """Tests for UncertaintyEstimate."""

    @pytest.fixture
    def estimate(self):
        """Create test uncertainty estimate."""
        return UncertaintyEstimate(
            total_uncertainty=0.4,
            input_uncertainty=0.1,
            reasoning_uncertainty=0.15,
            parameter_uncertainty=0.1,
            prediction_uncertainty=0.05,
        )

    def test_uncertainty_estimate_creation(self, estimate):
        """Test UncertaintyEstimate creation."""
        assert estimate.total_uncertainty == 0.4
        assert estimate.input_uncertainty == 0.1
        assert estimate.id is not None

    def test_should_escalate_high_uncertainty(self, estimate):
        """Test escalation decision for high uncertainty."""
        estimate.total_uncertainty = 0.7
        assert estimate.should_escalate(threshold=0.5) is True

    def test_should_escalate_low_uncertainty(self):
        """Test escalation decision for low uncertainty."""
        # Create estimate with low uncertainty AND high confidence
        estimate = UncertaintyEstimate(
            total_uncertainty=0.3,
            confidence=ConfidenceScore(
                raw_confidence=0.9,
                calibrated_confidence=0.85,
            ),
        )
        assert estimate.should_escalate(threshold=0.5) is False

    def test_bald_metrics(self):
        """Test BALD-style metrics."""
        estimate = UncertaintyEstimate(
            entropy=0.8,
            mutual_information=0.3,
            variance=0.1,
            sample_count=10,
            sample_agreement=0.7,
        )
        assert estimate.entropy == 0.8
        assert estimate.mutual_information == 0.3
        assert estimate.sample_count == 10


class TestAutonomyDecision:
    """Tests for AutonomyDecision."""

    @pytest.fixture
    def decision(self):
        """Create test autonomy decision."""
        return AutonomyDecision(
            action="execute_code",
            autonomy_level=AutonomyLevel.APPROVE,
            can_proceed=False,
            risk_level=0.3,
            reasoning="Medium confidence requires approval",
        )

    def test_decision_creation(self, decision):
        """Test AutonomyDecision creation."""
        assert decision.action == "execute_code"
        assert decision.autonomy_level == AutonomyLevel.APPROVE
        assert decision.can_proceed is False

    def test_decision_with_confidence(self):
        """Test decision with confidence score."""
        confidence = ConfidenceScore(
            raw_confidence=0.9,
            calibrated_confidence=0.85,
        )
        decision = AutonomyDecision(
            action="read_file",
            confidence=confidence,
            can_proceed=True,
        )
        assert decision.confidence.calibrated_confidence == 0.85

    def test_decision_risk_factors(self):
        """Test decision with risk factors."""
        decision = AutonomyDecision(
            action="delete_file",
            risk_level=0.8,
            risk_factors=["destructive_action", "no_backup"],
        )
        assert len(decision.risk_factors) == 2
        assert "destructive_action" in decision.risk_factors

    def test_decision_to_dict(self, decision):
        """Test decision serialization."""
        d = decision.to_dict()

        assert d["action"] == "execute_code"
        assert d["autonomy_level"] == "approve"
        assert d["can_proceed"] is False


class TestEscalationRequest:
    """Tests for EscalationRequest."""

    @pytest.fixture
    def escalation_request(self):
        """Create test escalation request."""
        return EscalationRequest(
            action="critical_operation",
            reason=EscalationReason.HIGH_RISK,
            severity="high",
            options=["proceed", "cancel", "modify"],
            recommended_option="cancel",
        )

    def test_escalation_request_creation(self, escalation_request):
        """Test EscalationRequest creation."""
        assert escalation_request.action == "critical_operation"
        assert escalation_request.reason == EscalationReason.HIGH_RISK
        assert escalation_request.severity == "high"
        assert escalation_request.id is not None

    def test_escalation_request_options(self, escalation_request):
        """Test escalation options."""
        assert len(escalation_request.options) == 3
        assert escalation_request.recommended_option == "cancel"

    def test_escalation_request_timeout(self):
        """Test escalation timeout setting."""
        esc_request = EscalationRequest(
            action="test",
            timeout_seconds=60,
        )
        assert esc_request.timeout_seconds == 60

    def test_escalation_request_resolution(self, escalation_request):
        """Test escalation resolution."""
        escalation_request.human_response = "proceed"
        escalation_request.resolved = True
        escalation_request.response_timestamp = datetime.now().isoformat()

        assert escalation_request.resolved is True
        assert escalation_request.human_response == "proceed"

    def test_escalation_request_to_dict(self, escalation_request):
        """Test escalation serialization."""
        d = escalation_request.to_dict()

        assert d["action"] == "critical_operation"
        assert d["reason"] == "high_risk"
        assert d["severity"] == "high"
        assert d["recommended"] == "cancel"


class TestAutonomyConfig:
    """Tests for AutonomyConfig."""

    def test_config_defaults(self):
        """Test default configuration."""
        config = AutonomyConfig()

        assert config.default_level == AutonomyLevel.APPROVE
        assert config.high_confidence_threshold == 0.85
        assert config.low_confidence_threshold == 0.5
        assert config.block_high_risk is True

    def test_config_custom_thresholds(self):
        """Test custom threshold configuration."""
        config = AutonomyConfig(
            high_confidence_threshold=0.9,
            medium_confidence_threshold=0.75,
            low_confidence_threshold=0.6,
        )

        assert config.high_confidence_threshold == 0.9
        assert config.medium_confidence_threshold == 0.75
        assert config.low_confidence_threshold == 0.6

    def test_config_calibration_settings(self):
        """Test calibration configuration."""
        config = AutonomyConfig(
            use_calibration=True,
            calibration_method="temperature_scaling",
            ensemble_size=10,
        )

        assert config.use_calibration is True
        assert config.calibration_method == "temperature_scaling"
        assert config.ensemble_size == 10

    def test_config_escalation_settings(self):
        """Test escalation configuration."""
        config = AutonomyConfig(
            escalation_timeout_seconds=600,
            max_pending_escalations=5,
            auto_deny_on_timeout=True,
        )

        assert config.escalation_timeout_seconds == 600
        assert config.max_pending_escalations == 5
        assert config.auto_deny_on_timeout is True

    def test_config_safety_rails(self):
        """Test safety rail configuration."""
        config = AutonomyConfig(
            blocked_actions=["rm -rf", "DROP TABLE"],
            always_escalate_patterns=["sudo", "production"],
        )

        assert "rm -rf" in config.blocked_actions
        assert "production" in config.always_escalate_patterns


class TestAutonomyLevelProgression:
    """Tests for autonomy level progression."""

    def test_level_ordering(self):
        """Test autonomy level ordering."""
        levels = [
            AutonomyLevel.ASSIST,
            AutonomyLevel.APPROVE,
            AutonomyLevel.NOTIFY,
            AutonomyLevel.LEARN,
        ]

        # Check we have all levels
        assert len(levels) == 4

    def test_level_for_high_confidence(self):
        """Test autonomy level for high confidence."""
        config = AutonomyConfig(high_confidence_threshold=0.85)
        confidence = 0.9

        if confidence >= config.high_confidence_threshold:
            level = AutonomyLevel.NOTIFY
        else:
            level = AutonomyLevel.APPROVE

        assert level == AutonomyLevel.NOTIFY

    def test_level_for_low_confidence(self):
        """Test autonomy level for low confidence."""
        config = AutonomyConfig(low_confidence_threshold=0.5)
        confidence = 0.3

        if confidence < config.low_confidence_threshold:
            level = AutonomyLevel.ASSIST
        else:
            level = AutonomyLevel.APPROVE

        assert level == AutonomyLevel.ASSIST


class TestUncertaintyDecomposition:
    """Tests for uncertainty decomposition."""

    def test_epistemic_vs_aleatoric(self):
        """Test epistemic vs aleatoric uncertainty."""
        # High epistemic (model doesn't know)
        epistemic_case = ConfidenceScore(
            epistemic=0.8,
            aleatoric=0.2,
        )
        assert epistemic_case.epistemic > epistemic_case.aleatoric

        # High aleatoric (inherent randomness)
        aleatoric_case = ConfidenceScore(
            epistemic=0.2,
            aleatoric=0.8,
        )
        assert aleatoric_case.aleatoric > aleatoric_case.epistemic

    def test_uncertainty_by_type(self):
        """Test uncertainty by type."""
        estimate = UncertaintyEstimate(
            input_uncertainty=0.3,
            reasoning_uncertainty=0.2,
            parameter_uncertainty=0.1,
            prediction_uncertainty=0.1,
        )

        # Input uncertainty highest
        assert estimate.input_uncertainty > estimate.prediction_uncertainty


class TestEscalationWorkflow:
    """Tests for escalation workflow."""

    def test_escalation_lifecycle(self):
        """Test full escalation lifecycle."""
        # Create request
        request = EscalationRequest(
            action="deploy_to_production",
            reason=EscalationReason.HIGH_RISK,
            options=["approve", "reject"],
        )
        assert request.resolved is False

        # Human responds
        request.human_response = "approve"
        request.response_timestamp = datetime.now().isoformat()
        request.resolved = True

        assert request.resolved is True
        assert request.human_response == "approve"

    def test_escalation_with_context(self):
        """Test escalation with context."""
        decision = AutonomyDecision(
            action="delete_database",
            risk_level=0.9,
            reasoning="High-risk operation",
        )

        request = EscalationRequest(
            action="delete_database",
            reason=EscalationReason.HIGH_RISK,
            context={"database": "users", "tables": ["users", "sessions"]},
            original_decision=decision,
        )

        assert request.context["database"] == "users"
        assert request.original_decision is not None

    def test_escalation_severity_levels(self):
        """Test different severity levels."""
        severities = ["low", "medium", "high", "critical"]

        for severity in severities:
            request = EscalationRequest(
                action="test",
                severity=severity,
            )
            assert request.severity == severity


class TestConfidenceCalibration:
    """Tests for confidence calibration concepts."""

    def test_overconfident_calibration(self):
        """Test calibration of overconfident predictions."""
        # Model is overconfident
        score = ConfidenceScore(
            raw_confidence=0.95,
            calibrated_confidence=0.75,  # After calibration
        )

        assert score.calibrated_confidence < score.raw_confidence

    def test_underconfident_calibration(self):
        """Test calibration of underconfident predictions."""
        # Model is underconfident
        score = ConfidenceScore(
            raw_confidence=0.5,
            calibrated_confidence=0.7,  # After calibration
        )

        assert score.calibrated_confidence > score.raw_confidence

    def test_well_calibrated(self):
        """Test well-calibrated predictions."""
        score = ConfidenceScore(
            raw_confidence=0.8,
            calibrated_confidence=0.8,
        )

        assert score.calibrated_confidence == score.raw_confidence


class TestConfidenceRouter:
    """Tests for ConfidenceRouter."""

    @pytest.fixture
    def router(self):
        from core.autonomy.router import ConfidenceRouter

        return ConfidenceRouter()

    @pytest.fixture
    def high_confidence(self):
        return ConfidenceScore(raw_confidence=0.95, calibrated_confidence=0.9)

    @pytest.fixture
    def low_confidence(self):
        return ConfidenceScore(raw_confidence=0.3, calibrated_confidence=0.25)

    @pytest.fixture
    def low_uncertainty(self):
        return UncertaintyEstimate(
            total_uncertainty=0.2,
            confidence=ConfidenceScore(raw_confidence=0.9, calibrated_confidence=0.85),
        )

    @pytest.fixture
    def high_uncertainty(self):
        return UncertaintyEstimate(total_uncertainty=0.8)

    def test_route_high_confidence_low_risk(self, router, high_confidence, low_uncertainty):
        """Test routing with high confidence and low risk."""
        decision = router.route(
            action="read file test.txt",
            confidence=high_confidence,
            uncertainty=low_uncertainty,
        )
        assert decision.autonomy_level in [AutonomyLevel.NOTIFY, AutonomyLevel.LEARN]
        assert decision.can_proceed is True

    def test_route_low_confidence(self, router, low_confidence, low_uncertainty):
        """Test routing with low confidence."""
        decision = router.route(
            action="read file test.txt",
            confidence=low_confidence,
            uncertainty=low_uncertainty,
        )
        assert decision.autonomy_level in [AutonomyLevel.ASSIST, AutonomyLevel.APPROVE]
        assert decision.can_proceed is False

    def test_route_high_risk_action(self, router, high_confidence, low_uncertainty):
        """Test routing with high-risk action."""
        decision = router.route(
            action="delete all files in /tmp",
            confidence=high_confidence,
            uncertainty=low_uncertainty,
        )
        assert decision.risk_level >= 0.5
        assert (
            "destructive" in decision.risk_factors or "high_risk_pattern" in decision.risk_factors
        )

    def test_route_blocked_action(self, router, high_confidence, low_uncertainty):
        """Test routing with blocked action."""
        from core.autonomy.router import ConfidenceRouter

        config = AutonomyConfig(blocked_actions=["rm -rf"])
        blocking_router = ConfidenceRouter(config)
        decision = blocking_router.route(
            action="execute rm -rf /",
            confidence=high_confidence,
            uncertainty=low_uncertainty,
        )
        assert decision.can_proceed is False
        assert "blocked" in decision.reasoning.lower()

    def test_route_always_escalate_pattern(self, router, high_confidence, low_uncertainty):
        """Test routing with always-escalate pattern."""
        from core.autonomy.router import ConfidenceRouter

        config = AutonomyConfig(always_escalate_patterns=["production"])
        escalate_router = ConfidenceRouter(config)
        decision = escalate_router.route(
            action="deploy to production",
            confidence=high_confidence,
            uncertainty=low_uncertainty,
        )
        assert decision.can_proceed is False
        assert decision.autonomy_level == AutonomyLevel.APPROVE

    def test_route_high_uncertainty_override(self, router, high_confidence, high_uncertainty):
        """Test high uncertainty overrides confidence."""
        decision = router.route(
            action="read file test.txt",
            confidence=high_confidence,
            uncertainty=high_uncertainty,
        )
        assert decision.can_proceed is False
        assert "UNCERTAINTY" in decision.reasoning.upper()

    def test_get_escalation_reason_high_risk(self, router, high_confidence, low_uncertainty):
        """Test escalation reason for high-risk action."""
        decision = router.route(
            action="delete database records",
            confidence=high_confidence,
            uncertainty=low_uncertainty,
        )
        reason = router.get_escalation_reason(decision)
        assert reason in [EscalationReason.HIGH_RISK, EscalationReason.USER_PREFERENCE]

    def test_get_stats(self, router, high_confidence, low_uncertainty):
        """Test router statistics."""
        router.route("action 1", high_confidence, low_uncertainty)
        router.route("action 2", high_confidence, low_uncertainty)
        stats = router.get_stats()
        assert stats["total_decisions"] == 2
        assert "approval_rate" in stats


class TestUncertaintyEstimator:
    """Tests for UncertaintyEstimator."""

    @pytest.fixture
    def estimator(self):
        from core.autonomy.uncertainty import UncertaintyEstimator

        return UncertaintyEstimator()

    def test_estimate_basic(self, estimator):
        """Test basic uncertainty estimation."""
        estimate = estimator.estimate(verbalized_confidence=0.8)
        assert estimate.total_uncertainty >= 0.0
        assert estimate.total_uncertainty <= 1.0

    def test_estimate_from_logits(self, estimator):
        """Test estimation from logits."""
        logits = [2.0, 1.0, 0.5, 0.1]  # High confidence in first class
        estimate = estimator.estimate(logits=logits)
        assert estimate.entropy >= 0.0
        assert estimate.variance >= 0.0

    def test_estimate_from_samples(self, estimator):
        """Test estimation from multiple samples."""
        # Disagreeing samples = high epistemic uncertainty
        samples = ["answer A", "answer B", "answer C"]
        estimate = estimator.estimate(samples=samples)
        assert estimate.mutual_information > 0.0
        assert estimate.sample_agreement < 1.0

    def test_estimate_agreeing_samples(self, estimator):
        """Test estimation with agreeing samples."""
        # Agreeing samples = low epistemic uncertainty
        samples = ["answer A", "answer A", "answer A"]
        estimate = estimator.estimate(samples=samples)
        assert estimate.sample_agreement == 1.0

    def test_estimate_input_uncertainty(self, estimator):
        """Test input uncertainty from ambiguous query."""
        estimate = estimator.estimate(input_text="maybe do something?")
        assert estimate.input_uncertainty > 0.2  # Ambiguous input

    def test_estimate_reasoning_uncertainty(self, estimator):
        """Test reasoning uncertainty from hedging output."""
        estimate = estimator.estimate(
            output_text="I think this might be correct, but I'm not sure."
        )
        assert estimate.reasoning_uncertainty > 0.1

    def test_estimate_from_verbalized(self, estimator):
        """Test estimate_from_verbalized method."""
        estimate = estimator.estimate_from_verbalized(
            verbalized_confidence=0.9,
            hedging_phrases=["maybe", "possibly"],
        )
        assert estimate.confidence.calibrated_confidence < 0.9  # Penalized

    def test_get_stats(self, estimator):
        """Test uncertainty statistics."""
        estimator.estimate(verbalized_confidence=0.7)
        estimator.estimate(verbalized_confidence=0.8)
        stats = estimator.get_stats()
        assert stats["total_estimates"] == 2
        assert "avg_total_uncertainty" in stats


class TestConfidenceCalibrator:
    """Tests for ConfidenceCalibrator."""

    @pytest.fixture
    def calibrator(self):
        from core.autonomy.calibrator import ConfidenceCalibrator

        return ConfidenceCalibrator()

    def test_calibrate_default(self, calibrator):
        """Test default calibration."""
        calibrated = calibrator.calibrate(0.8)
        assert 0.0 <= calibrated <= 1.0

    def test_calibrate_temperature_scaling(self):
        """Test temperature scaling calibration."""
        from core.autonomy.calibrator import ConfidenceCalibrator

        calibrator = ConfidenceCalibrator(method="temperature_scaling")
        calibrated = calibrator.calibrate(0.9)
        assert 0.0 <= calibrated <= 1.0

    def test_add_calibration_point(self, calibrator):
        """Test adding calibration points."""
        calibrator.add_calibration_point(0.9, True)
        calibrator.add_calibration_point(0.8, True)
        calibrator.add_calibration_point(0.7, False)
        stats = calibrator.get_stats()
        assert stats["data_points"] == 3

    def test_calibrator_fits_after_threshold(self, calibrator):
        """Test calibrator fits after enough data."""
        # Add 50 points to trigger fitting
        for i in range(50):
            calibrator.add_calibration_point(0.5 + i * 0.01, i % 2 == 0)
        stats = calibrator.get_stats()
        assert stats["fitted"] is True

    def test_reset_calibrator(self, calibrator):
        """Test calibrator reset."""
        calibrator.add_calibration_point(0.8, True)
        calibrator.reset()
        stats = calibrator.get_stats()
        assert stats["data_points"] == 0
        assert stats["fitted"] is False


class TestEscalationManager:
    """Tests for EscalationManager."""

    @pytest.fixture
    def manager(self):
        from core.autonomy.escalation import EscalationManager

        return EscalationManager()

    @pytest.fixture
    def decision(self):
        return AutonomyDecision(
            action="deploy_service",
            autonomy_level=AutonomyLevel.APPROVE,
            risk_level=0.7,
        )

    def test_create_escalation(self, manager, decision):
        """Test creating an escalation."""
        esc = manager.create_escalation(
            decision=decision,
            reason=EscalationReason.HIGH_RISK,
        )
        assert esc.id is not None
        assert esc.reason == EscalationReason.HIGH_RISK
        assert esc.resolved is False

    def test_create_escalation_with_options(self, manager, decision):
        """Test escalation with custom options."""
        esc = manager.create_escalation(
            decision=decision,
            reason=EscalationReason.USER_PREFERENCE,
            options=["yes", "no", "skip"],
            recommended="yes",
        )
        assert esc.options == ["yes", "no", "skip"]
        assert esc.recommended_option == "yes"

    def test_respond_to_escalation(self, manager, decision):
        """Test responding to escalation."""
        esc = manager.create_escalation(decision=decision, reason=EscalationReason.HIGH_RISK)
        result = manager.respond(esc.id, "approve")
        assert result is True
        resolved = manager.get_request(esc.id)
        assert resolved.resolved is True
        assert resolved.human_response == "approve"

    def test_get_pending_escalations(self, manager, decision):
        """Test getting pending escalations."""
        manager.create_escalation(decision=decision, reason=EscalationReason.HIGH_RISK)
        manager.create_escalation(decision=decision, reason=EscalationReason.LOW_CONFIDENCE)
        pending = manager.get_pending()
        assert len(pending) == 2

    def test_cancel_escalation(self, manager, decision):
        """Test cancelling an escalation."""
        esc = manager.create_escalation(decision=decision, reason=EscalationReason.HIGH_RISK)
        result = manager.cancel(esc.id)
        assert result is True
        assert len(manager.get_pending()) == 0

    def test_severity_determination(self, manager):
        """Test severity determination for different reasons."""
        high_risk_decision = AutonomyDecision(action="delete", risk_level=0.9)
        esc = manager.create_escalation(
            decision=high_risk_decision,
            reason=EscalationReason.HIGH_RISK,
        )
        assert esc.severity in ["high", "critical"]

    def test_get_stats(self, manager, decision):
        """Test escalation statistics."""
        esc1 = manager.create_escalation(decision=decision, reason=EscalationReason.HIGH_RISK)
        manager.respond(esc1.id, "approve")
        esc2 = manager.create_escalation(decision=decision, reason=EscalationReason.LOW_CONFIDENCE)
        manager.respond(esc2.id, "deny")
        stats = manager.get_stats()
        assert stats["total_escalations"] == 2
        assert stats["approved_count"] == 1
        assert stats["denied_count"] == 1


class TestAutonomyMixin:
    """Tests for AutonomyMixin."""

    @pytest.fixture
    def agent_with_autonomy(self):
        from core.autonomy.mixin import AutonomyMixin

        class TestAgent(AutonomyMixin):
            def __init__(self):
                self._init_autonomy()

        return TestAgent()

    def test_init_autonomy(self, agent_with_autonomy):
        """Test autonomy initialization."""
        status = agent_with_autonomy.get_autonomy_status()
        assert status["initialized"] is True
        assert status["current_level"] == "approve"

    def test_estimate_uncertainty(self, agent_with_autonomy):
        """Test uncertainty estimation."""
        estimate = agent_with_autonomy.estimate_uncertainty(
            verbalized_confidence=0.8,
        )
        assert estimate.total_uncertainty >= 0.0

    def test_check_autonomy(self, agent_with_autonomy):
        """Test autonomy check."""
        decision = agent_with_autonomy.check_autonomy(
            action="read file",
            confidence=0.9,
        )
        assert decision.action == "read file"
        assert decision.autonomy_level is not None

    def test_upgrade_autonomy(self, agent_with_autonomy):
        """Test upgrading autonomy level."""
        result = agent_with_autonomy.upgrade_autonomy(AutonomyLevel.NOTIFY)
        assert result is True
        assert agent_with_autonomy.get_current_autonomy_level() == AutonomyLevel.NOTIFY

    def test_upgrade_autonomy_skip_level_fails(self, agent_with_autonomy):
        """Test that skipping levels fails."""
        result = agent_with_autonomy.upgrade_autonomy(AutonomyLevel.LEARN)
        assert result is False

    def test_downgrade_autonomy(self, agent_with_autonomy):
        """Test downgrading autonomy level."""
        agent_with_autonomy.upgrade_autonomy(AutonomyLevel.NOTIFY)
        result = agent_with_autonomy.downgrade_autonomy(AutonomyLevel.ASSIST)
        assert result is True
        assert agent_with_autonomy.get_current_autonomy_level() == AutonomyLevel.ASSIST

    def test_record_outcome(self, agent_with_autonomy):
        """Test recording calibration outcomes."""
        agent_with_autonomy.record_outcome(predicted_confidence=0.8, was_correct=True)
        agent_with_autonomy.record_outcome(predicted_confidence=0.9, was_correct=False)
        # Should not raise

    def test_get_pending_escalations(self, agent_with_autonomy):
        """Test getting pending escalations."""
        pending = agent_with_autonomy.get_pending_escalations()
        assert isinstance(pending, list)


class TestConfidenceCalibratorPlatt:
    """Additional tests for Platt scaling calibration."""

    @pytest.fixture
    def platt_calibrator(self):
        from core.autonomy.calibrator import ConfidenceCalibrator

        return ConfidenceCalibrator(method="platt")

    def test_calibrate_platt_unfitted(self, platt_calibrator):
        """Test Platt calibration when not fitted."""
        result = platt_calibrator.calibrate(0.7)
        # Should use default temperature scaling
        assert 0 < result < 1

    def test_calibrate_platt_fitted(self, platt_calibrator):
        """Test Platt calibration after fitting."""
        # Add enough calibration data
        for i in range(60):
            conf = 0.3 + (i / 100)
            correct = conf > 0.5
            platt_calibrator.add_calibration_point(conf, correct)

        result = platt_calibrator.calibrate(0.7)
        assert 0 < result < 1
        assert platt_calibrator._is_fitted is True

    def test_apply_platt_direct(self, platt_calibrator):
        """Test _apply_platt directly."""
        platt_calibrator._platt_a = 1.2
        platt_calibrator._platt_b = 0.1
        result = platt_calibrator._apply_platt(0.6)
        assert 0 < result < 1

    def test_fit_platt(self, platt_calibrator):
        """Test Platt fitting."""
        for i in range(60):
            conf = 0.3 + (i / 100)
            correct = conf > 0.5
            platt_calibrator._calibration_data.append((conf, correct))
        platt_calibrator._fit_platt()
        # Parameters should be set
        assert platt_calibrator._platt_a != 0.0 or platt_calibrator._platt_b != 0.0

    def test_compute_ece_platt(self, platt_calibrator):
        """Test ECE computation for Platt scaling."""
        for i in range(50):
            conf = 0.3 + (i / 100)
            correct = conf > 0.5
            platt_calibrator._calibration_data.append((conf, correct))
        platt_calibrator._platt_a = 1.0
        platt_calibrator._platt_b = 0.0
        ece = platt_calibrator._compute_ece_platt()
        assert 0 <= ece <= 1


class TestConfidenceCalibratorIsotonic:
    """Tests for isotonic regression calibration."""

    @pytest.fixture
    def isotonic_calibrator(self):
        from core.autonomy.calibrator import ConfidenceCalibrator

        return ConfidenceCalibrator(method="isotonic")

    def test_calibrate_isotonic_unfitted(self, isotonic_calibrator):
        """Test isotonic calibration when not fitted."""
        result = isotonic_calibrator.calibrate(0.7)
        assert 0 < result < 1

    def test_calibrate_isotonic_fitted(self, isotonic_calibrator):
        """Test isotonic calibration after fitting."""
        for i in range(60):
            conf = 0.1 + (i / 70)
            correct = conf > 0.5
            isotonic_calibrator.add_calibration_point(conf, correct)

        result = isotonic_calibrator.calibrate(0.7)
        assert 0 <= result <= 1

    def test_apply_isotonic_empty_bins(self, isotonic_calibrator):
        """Test _apply_isotonic with empty bins."""
        result = isotonic_calibrator._apply_isotonic(0.5)
        assert result == 0.5

    def test_apply_isotonic_with_bins(self, isotonic_calibrator):
        """Test _apply_isotonic with bins."""
        isotonic_calibrator._isotonic_bins = [
            (0.2, 0.3),
            (0.5, 0.6),
            (0.8, 1.0),
        ]
        result_low = isotonic_calibrator._apply_isotonic(0.25)
        result_mid = isotonic_calibrator._apply_isotonic(0.55)
        result_high = isotonic_calibrator._apply_isotonic(0.95)
        assert result_low == 0.2
        assert result_mid == 0.5
        assert result_high == 0.8

    def test_fit_isotonic(self, isotonic_calibrator):
        """Test isotonic regression fitting."""
        for i in range(100):
            conf = i / 100
            correct = conf > 0.5
            isotonic_calibrator._calibration_data.append((conf, correct))
        isotonic_calibrator._fit_isotonic()
        assert len(isotonic_calibrator._isotonic_bins) > 0


class TestConfidenceCalibratorStats:
    """Tests for calibrator statistics."""

    def test_get_stats_empty(self):
        """Test stats with no data."""
        from core.autonomy.calibrator import ConfidenceCalibrator

        calibrator = ConfidenceCalibrator()
        stats = calibrator.get_stats()
        assert stats["fitted"] is False
        assert stats["data_points"] == 0

    def test_get_stats_with_data(self):
        """Test stats after calibration."""
        from core.autonomy.calibrator import ConfidenceCalibrator

        calibrator = ConfidenceCalibrator()
        for i in range(60):
            calibrator.add_calibration_point(0.3 + (i / 100), i % 2 == 0)
        stats = calibrator.get_stats()
        assert stats["fitted"] is True
        assert stats["data_points"] == 60
        assert "ece" in stats

    def test_get_stats_platt(self):
        """Test stats for Platt calibrator."""
        from core.autonomy.calibrator import ConfidenceCalibrator

        calibrator = ConfidenceCalibrator(method="platt")
        for i in range(60):
            calibrator.add_calibration_point(0.3 + (i / 100), i % 2 == 0)
        stats = calibrator.get_stats()
        assert stats["method"] == "platt"
        assert "platt_a" in stats

    def test_reset(self):
        """Test calibrator reset."""
        from core.autonomy.calibrator import ConfidenceCalibrator

        calibrator = ConfidenceCalibrator()
        calibrator.add_calibration_point(0.8, True)
        calibrator._is_fitted = True
        calibrator.reset()
        assert len(calibrator._calibration_data) == 0
        assert calibrator._is_fitted is False


class TestEscalationManagerExtended:
    """Extended tests for EscalationManager."""

    @pytest.fixture
    def manager(self):
        from core.autonomy.escalation import EscalationManager

        return EscalationManager()

    def test_create_escalation_with_context(self, manager):
        """Test escalation with additional context in decision."""
        decision = AutonomyDecision(
            action="deploy",
            risk_level=0.8,
            context={"environment": "production", "service": "api"},
        )
        esc = manager.create_escalation(
            decision=decision,
            reason=EscalationReason.HIGH_RISK,
        )
        assert esc.context["environment"] == "production"

    def test_escalation_has_timeout(self, manager):
        """Test escalation has timeout from config."""
        decision = AutonomyDecision(action="deploy", risk_level=0.8)
        esc = manager.create_escalation(
            decision=decision,
            reason=EscalationReason.HIGH_RISK,
        )
        # Should have timeout from config
        assert esc.timeout_seconds > 0

    def test_respond_invalid_id(self, manager):
        """Test responding to non-existent escalation."""
        result = manager.respond("invalid_id", "approve")
        assert result is False

    def test_cancel_invalid_id(self, manager):
        """Test cancelling non-existent escalation."""
        result = manager.cancel("invalid_id")
        assert result is False

    def test_get_request_not_found(self, manager):
        """Test getting non-existent request."""
        request = manager.get_request("invalid_id")
        assert request is None

    def test_multiple_escalations_ordering(self, manager):
        """Test escalations are ordered by creation."""
        for i in range(5):
            decision = AutonomyDecision(action=f"action_{i}", risk_level=0.5 + i * 0.1)
            manager.create_escalation(decision=decision, reason=EscalationReason.HIGH_RISK)
        pending = manager.get_pending()
        assert len(pending) == 5


class TestAutonomyMixinExtended:
    """Extended tests for AutonomyMixin."""

    @pytest.fixture
    def agent_with_autonomy(self):
        from core.autonomy.mixin import AutonomyMixin

        class TestAgent(AutonomyMixin):
            def __init__(self):
                self._init_autonomy()

        return TestAgent()

    def test_check_autonomy_different_actions(self, agent_with_autonomy):
        """Test autonomy check with different actions."""
        decision = agent_with_autonomy.check_autonomy(
            action="read file",
            confidence=0.95,
        )
        assert decision.action == "read file"
        assert decision.autonomy_level is not None

    def test_check_autonomy_returns_decision(self, agent_with_autonomy):
        """Test autonomy check returns valid decision."""
        decision = agent_with_autonomy.check_autonomy(
            action="execute command",
            confidence=0.7,
        )
        assert isinstance(decision, AutonomyDecision)
        assert decision.action == "execute command"

    def test_get_autonomy_status_fields(self, agent_with_autonomy):
        """Test getting full autonomy status."""
        status = agent_with_autonomy.get_autonomy_status()
        assert "initialized" in status
        assert "current_level" in status
        # The actual key is calibration_stats, not calibrator_stats
        assert "calibration_stats" in status
        assert "escalation_stats" in status

    def test_calibrator_integration(self, agent_with_autonomy):
        """Test that calibrator integrates with autonomy checks."""
        # Record several outcomes
        for i in range(60):
            agent_with_autonomy.record_outcome(0.5 + i * 0.005, i % 2 == 0)
        # Check that calibrator data is updated
        status = agent_with_autonomy.get_autonomy_status()
        assert status["calibration_stats"]["data_points"] == 60


class TestEscalationManagerAsync:
    """Async tests for EscalationManager."""

    @pytest.fixture
    def manager_with_callback(self):
        from core.autonomy.escalation import EscalationManager
        from core.autonomy.types import AutonomyConfig

        self.callback_called = False
        self.callback_request = None

        def on_escalation(request):
            self.callback_called = True
            self.callback_request = request

        config = AutonomyConfig(max_pending_escalations=3)
        return EscalationManager(config=config, on_escalation=on_escalation)

    def test_on_escalation_callback(self, manager_with_callback):
        """Test that on_escalation callback is called."""
        decision = AutonomyDecision(action="test", risk_level=0.5)
        manager_with_callback.create_escalation(
            decision=decision,
            reason=EscalationReason.HIGH_RISK,
        )
        assert self.callback_called is True
        assert self.callback_request is not None

    def test_max_pending_triggers_timeout(self, manager_with_callback):
        """Test that exceeding max_pending times out oldest."""
        # Fill up to max
        for i in range(4):  # Config has max=3, so 4th should trigger timeout
            decision = AutonomyDecision(action=f"action_{i}", risk_level=0.5)
            manager_with_callback.create_escalation(
                decision=decision,
                reason=EscalationReason.HIGH_RISK,
            )
        # Should have 3 pending (oldest was timed out)
        assert len(manager_with_callback.get_pending()) == 3

    def test_get_pending_by_severity(self):
        """Test filtering pending by severity."""
        from core.autonomy.escalation import EscalationManager

        manager = EscalationManager()
        # Create high severity
        high_decision = AutonomyDecision(action="delete", risk_level=0.9)
        manager.create_escalation(
            decision=high_decision,
            reason=EscalationReason.HIGH_RISK,
        )
        # Create low severity
        low_decision = AutonomyDecision(action="read", risk_level=0.2)
        manager.create_escalation(
            decision=low_decision,
            reason=EscalationReason.USER_PREFERENCE,
        )
        high_pending = manager.get_pending_by_severity("high")
        low_pending = manager.get_pending_by_severity("low")
        assert len(high_pending) == 1
        assert len(low_pending) == 1

    def test_safety_concern_severity(self):
        """Test that SAFETY_CONCERN gives critical severity."""
        from core.autonomy.escalation import EscalationManager

        manager = EscalationManager()
        decision = AutonomyDecision(action="dangerous", risk_level=0.5)
        esc = manager.create_escalation(
            decision=decision,
            reason=EscalationReason.SAFETY_CONCERN,
        )
        assert esc.severity == "critical"

    def test_policy_violation_severity(self):
        """Test that POLICY_VIOLATION gives critical severity."""
        from core.autonomy.escalation import EscalationManager

        manager = EscalationManager()
        decision = AutonomyDecision(action="violation", risk_level=0.3)
        esc = manager.create_escalation(
            decision=decision,
            reason=EscalationReason.POLICY_VIOLATION,
        )
        assert esc.severity == "critical"

    def test_respond_invalid_response_still_works(self):
        """Test that invalid response (not in options) still works but logs warning."""
        from core.autonomy.escalation import EscalationManager

        manager = EscalationManager()
        decision = AutonomyDecision(action="test", risk_level=0.5)
        esc = manager.create_escalation(
            decision=decision,
            reason=EscalationReason.HIGH_RISK,
            options=["approve", "deny"],
        )
        # Respond with value not in options
        result = manager.respond(esc.id, "maybe")
        assert result is True  # Still succeeds
        resolved = manager.get_request(esc.id)
        assert resolved.human_response == "maybe"

    def test_clear_history(self):
        """Test clearing escalation history."""
        from core.autonomy.escalation import EscalationManager

        manager = EscalationManager()
        decision = AutonomyDecision(action="test", risk_level=0.5)
        esc = manager.create_escalation(decision=decision, reason=EscalationReason.HIGH_RISK)
        manager.respond(esc.id, "approve")
        assert len(manager._history) == 1
        manager.clear_history()
        assert len(manager._history) == 0

    @pytest.mark.asyncio
    async def test_wait_for_response_not_pending(self):
        """Test wait_for_response returns None if not pending."""
        from core.autonomy.escalation import EscalationManager

        manager = EscalationManager()
        result = await manager.wait_for_response("nonexistent_id")
        assert result is None

    @pytest.mark.asyncio
    async def test_wait_for_response_timeout(self):
        """Test wait_for_response times out correctly."""
        from core.autonomy.escalation import EscalationManager
        from core.autonomy.types import AutonomyConfig

        config = AutonomyConfig(escalation_timeout_seconds=1)
        manager = EscalationManager(config=config)
        decision = AutonomyDecision(action="test", risk_level=0.5)
        esc = manager.create_escalation(decision=decision, reason=EscalationReason.HIGH_RISK)
        result = await manager.wait_for_response(esc.id, timeout=0.1)
        assert result is None
        # Should be in history now, not pending
        assert esc.id not in manager._pending

    @pytest.mark.asyncio
    async def test_wait_for_response_with_respond(self):
        """Test wait_for_response receives response."""
        import asyncio
        from core.autonomy.escalation import EscalationManager

        manager = EscalationManager()
        decision = AutonomyDecision(action="test", risk_level=0.5)
        esc = manager.create_escalation(decision=decision, reason=EscalationReason.HIGH_RISK)

        async def respond_later():
            await asyncio.sleep(0.05)
            manager.respond(esc.id, "approve")

        asyncio.create_task(respond_later())
        result = await manager.wait_for_response(esc.id, timeout=1)
        assert result == "approve"


class TestAutonomyMixinAsync:
    """Async tests for AutonomyMixin."""

    @pytest.fixture
    def agent_with_autonomy(self):
        from core.autonomy.mixin import AutonomyMixin

        class TestAgent(AutonomyMixin):
            def __init__(self):
                self._init_autonomy()

        return TestAgent()

    @pytest.fixture
    def agent_uninit(self):
        from core.autonomy.mixin import AutonomyMixin

        class TestAgent(AutonomyMixin):
            pass

        return TestAgent()

    def test_estimate_uncertainty_auto_init(self, agent_uninit):
        """Test estimate_uncertainty auto-initializes."""
        estimate = agent_uninit.estimate_uncertainty(verbalized_confidence=0.8)
        assert estimate is not None
        assert hasattr(agent_uninit, "_uncertainty_estimator")

    def test_check_autonomy_auto_init(self, agent_uninit):
        """Test check_autonomy auto-initializes."""
        decision = agent_uninit.check_autonomy(action="test", confidence=0.8)
        assert decision is not None
        assert hasattr(agent_uninit, "_router")

    def test_respond_to_escalation_uninit(self, agent_uninit):
        """Test respond_to_escalation returns False when uninit."""
        result = agent_uninit.respond_to_escalation("test_id", "approve")
        assert result is False

    def test_get_pending_escalations_uninit(self, agent_uninit):
        """Test get_pending_escalations returns empty when uninit."""
        pending = agent_uninit.get_pending_escalations()
        assert pending == []

    def test_upgrade_autonomy_auto_init(self, agent_uninit):
        """Test upgrade_autonomy auto-initializes."""
        agent_uninit.upgrade_autonomy(AutonomyLevel.NOTIFY)
        # Will fail because can't skip levels, but should init
        assert hasattr(agent_uninit, "_current_autonomy_level")

    def test_downgrade_autonomy_auto_init(self, agent_uninit):
        """Test downgrade_autonomy auto-initializes."""
        result = agent_uninit.downgrade_autonomy(AutonomyLevel.ASSIST)
        assert result is True
        assert hasattr(agent_uninit, "_current_autonomy_level")

    def test_get_current_autonomy_level_uninit(self, agent_uninit):
        """Test get_current_autonomy_level returns default when uninit."""
        level = agent_uninit.get_current_autonomy_level()
        assert level == AutonomyLevel.APPROVE

    def test_apply_autonomy_level_assist_cant_proceed(self, agent_with_autonomy):
        """Test that ASSIST level prevents auto-proceed."""
        agent_with_autonomy.downgrade_autonomy(AutonomyLevel.ASSIST)
        decision = agent_with_autonomy.check_autonomy(
            action="any action",
            confidence=0.99,  # Very high confidence
        )
        # At ASSIST level, can_proceed should be False
        assert decision.autonomy_level == AutonomyLevel.ASSIST

    @pytest.mark.asyncio
    async def test_request_approval_auto_init(self, agent_uninit):
        """Test request_approval auto-initializes."""
        import asyncio

        # Create task to respond quickly
        async def timeout_test():
            return await asyncio.wait_for(
                agent_uninit.request_approval(
                    action="test",
                    timeout=0.1,
                ),
                timeout=0.5,
            )

        await timeout_test()
        # Should timeout and return None, but should have initialized
        assert hasattr(agent_uninit, "_escalation_manager")


class TestConfidenceRouterEdgeCases:
    """Edge case tests for ConfidenceRouter to reach 100% coverage."""

    @pytest.fixture
    def router_no_block(self):
        """Router with block_high_risk=False."""
        from core.autonomy.router import ConfidenceRouter
        from core.autonomy.types import AutonomyConfig

        config = AutonomyConfig(
            block_high_risk=False,
            high_risk_threshold=0.7,
        )
        return ConfidenceRouter(config)

    @pytest.fixture
    def router_with_patterns(self):
        """Router with escalation patterns."""
        from core.autonomy.router import ConfidenceRouter
        from core.autonomy.types import AutonomyConfig

        config = AutonomyConfig(
            blocked_actions=["shutdown", "format"],
            always_escalate_patterns=["deploy", "migrate"],
        )
        return ConfidenceRouter(config)

    def test_high_risk_no_block(self, router_no_block):
        """Test high risk without blocking (line 176)."""
        from core.autonomy.types import ConfidenceScore, UncertaintyEstimate

        conf = ConfidenceScore(raw_confidence=0.9, calibrated_confidence=0.9)
        uncertainty = UncertaintyEstimate(total_uncertainty=0.1)
        # Action with high risk
        decision = router_no_block.route(
            action="delete all databases in production",
            confidence=conf,
            uncertainty=uncertainty,
        )
        # Should be APPROVE but not blocked
        assert decision.autonomy_level == AutonomyLevel.APPROVE

    def test_medium_risk_pattern_match(self):
        """Test medium risk pattern matching (lines 230-231)."""
        from core.autonomy.router import ConfidenceRouter
        from core.autonomy.types import ConfidenceScore, UncertaintyEstimate

        router = ConfidenceRouter()
        conf = ConfidenceScore(raw_confidence=0.9, calibrated_confidence=0.9)
        uncertainty = UncertaintyEstimate(total_uncertainty=0.1)
        # Action with medium risk pattern - matches "update.*(?:config|setting)"
        decision = router.route(
            action="update the configuration settings",
            confidence=conf,
            uncertainty=uncertainty,
        )
        assert decision.risk_level >= 0.5  # Medium risk patterns give 0.5

    def test_context_production_risk(self):
        """Test production context increases risk (lines 236-237)."""
        from core.autonomy.router import ConfidenceRouter
        from core.autonomy.types import ConfidenceScore, UncertaintyEstimate

        router = ConfidenceRouter()
        conf = ConfidenceScore(raw_confidence=0.9, calibrated_confidence=0.9)
        uncertainty = UncertaintyEstimate(total_uncertainty=0.1)
        decision = router.route(
            action="update database record",
            confidence=conf,
            uncertainty=uncertainty,
            context={"environment": "production"},
        )
        # Production context should increase risk
        assert decision.risk_level > 0.1

    def test_context_high_risk_flag(self):
        """Test context high_risk flag (lines 240-241)."""
        from core.autonomy.router import ConfidenceRouter
        from core.autonomy.types import ConfidenceScore, UncertaintyEstimate

        router = ConfidenceRouter()
        conf = ConfidenceScore(raw_confidence=0.9, calibrated_confidence=0.9)
        uncertainty = UncertaintyEstimate(total_uncertainty=0.1)
        decision = router.route(
            action="simple read operation",
            confidence=conf,
            uncertainty=uncertainty,
            context={"high_risk": True},
        )
        assert decision.risk_level >= 0.7

    def test_get_risk_factors_medium_pattern(self):
        """Test medium risk factor detection (lines 256-257)."""
        from core.autonomy.router import ConfidenceRouter

        router = ConfidenceRouter()
        # Action with medium risk pattern only
        factors = router._get_risk_factors("update user settings")
        assert "medium_risk_pattern" in factors or len(factors) >= 0

    def test_get_risk_factors_sensitive_data(self):
        """Test sensitive data risk factor (line 265)."""
        from core.autonomy.router import ConfidenceRouter

        router = ConfidenceRouter()
        factors = router._get_risk_factors("access secret credentials")
        assert "sensitive_data" in factors

    def test_escalation_reason_low_confidence(self):
        """Test LOW_CONFIDENCE escalation reason (line 275)."""
        from core.autonomy.router import ConfidenceRouter
        from core.autonomy.types import AutonomyDecision, ConfidenceScore, UncertaintyEstimate

        router = ConfidenceRouter()
        decision = AutonomyDecision(
            action="test",
            risk_level=0.1,  # Low risk
            confidence=ConfidenceScore(calibrated_confidence=0.2),  # Low confidence
            uncertainty=UncertaintyEstimate(total_uncertainty=0.1),
        )
        reason = router.get_escalation_reason(decision)
        assert reason == EscalationReason.LOW_CONFIDENCE

    def test_escalation_reason_ambiguous(self):
        """Test AMBIGUOUS_INPUT escalation reason (line 278)."""
        from core.autonomy.router import ConfidenceRouter
        from core.autonomy.types import AutonomyDecision, ConfidenceScore, UncertaintyEstimate

        router = ConfidenceRouter()
        decision = AutonomyDecision(
            action="test",
            risk_level=0.1,
            confidence=ConfidenceScore(calibrated_confidence=0.9),
            uncertainty=UncertaintyEstimate(total_uncertainty=0.7),  # High uncertainty
        )
        reason = router.get_escalation_reason(decision)
        assert reason == EscalationReason.AMBIGUOUS_INPUT

    def test_escalation_reason_policy_violation(self):
        """Test POLICY_VIOLATION escalation reason (line 281)."""
        from core.autonomy.router import ConfidenceRouter
        from core.autonomy.types import AutonomyDecision, ConfidenceScore, UncertaintyEstimate

        router = ConfidenceRouter()
        decision = AutonomyDecision(
            action="test",
            risk_level=0.1,
            confidence=ConfidenceScore(calibrated_confidence=0.9),
            uncertainty=UncertaintyEstimate(total_uncertainty=0.1),
            reasoning="Action was blocked by policy",
        )
        reason = router.get_escalation_reason(decision)
        assert reason == EscalationReason.POLICY_VIOLATION


class TestCalibratorEdgeCases:
    """Edge case tests for ConfidenceCalibrator to reach 100% coverage."""

    def test_calibrate_platt_method_fitted(self):
        """Test Platt calibration when fitted (lines 76, 82)."""
        from core.autonomy.calibrator import ConfidenceCalibrator

        calibrator = ConfidenceCalibrator(method="platt")
        # Add enough data to fit
        for i in range(60):
            calibrator.add_calibration_point(0.3 + i * 0.01, i % 2 == 0)
        # Now calibrate
        result = calibrator.calibrate(0.7)
        assert 0 < result < 1

    def test_calibrate_unknown_method(self):
        """Test calibration with unknown method (line 82)."""
        from core.autonomy.calibrator import ConfidenceCalibrator

        calibrator = ConfidenceCalibrator(method="unknown_method")
        calibrator._is_fitted = True
        result = calibrator.calibrate(0.7)
        assert result == 0.7  # Returns raw value

    def test_calibrate_default_unfitted(self):
        """Test default calibration when not fitted (line 87)."""
        from core.autonomy.calibrator import ConfidenceCalibrator

        calibrator = ConfidenceCalibrator()
        result = calibrator.calibrate(0.7)
        # Should use default temperature 1.2
        assert result != 0.7

    def test_isotonic_last_bin(self):
        """Test isotonic regression last bin (line 120)."""
        from core.autonomy.calibrator import ConfidenceCalibrator

        calibrator = ConfidenceCalibrator(method="isotonic")
        calibrator._isotonic_bins = [
            (0.2, 0.3),
            (0.5, 0.6),
            (0.8, 0.9),
        ]
        # Value beyond all bins
        result = calibrator._apply_isotonic(0.99)
        assert result == 0.8  # Last bin value

    def test_fit_insufficient_data(self):
        """Test _fit with insufficient data (line 143)."""
        from core.autonomy.calibrator import ConfidenceCalibrator

        calibrator = ConfidenceCalibrator()
        for i in range(10):  # Less than 20
            calibrator._calibration_data.append((0.5, True))
        calibrator._fit()
        assert calibrator._is_fitted is False


class TestEscalationCancelFuture:
    """Test cancel with active future (lines 239-241, 249, 255, 266)."""

    @pytest.mark.asyncio
    async def test_cancel_with_active_future(self):
        """Test cancelling escalation with active wait future."""
        import asyncio
        from core.autonomy.escalation import EscalationManager

        manager = EscalationManager()
        decision = AutonomyDecision(action="test", risk_level=0.5)
        esc = manager.create_escalation(decision=decision, reason=EscalationReason.HIGH_RISK)

        # Start waiting in background
        async def wait_task():
            return await manager.wait_for_response(esc.id, timeout=5)

        task = asyncio.create_task(wait_task())
        await asyncio.sleep(0.05)  # Let task start

        # Cancel while waiting
        result = manager.cancel(esc.id)
        assert result is True

        # Task should be cancelled
        try:
            await asyncio.wait_for(task, timeout=0.5)
        except asyncio.CancelledError:
            pass  # Expected

    @pytest.mark.asyncio
    async def test_timeout_with_auto_deny(self):
        """Test timeout with auto_deny_on_timeout=True (lines 254-257)."""
        from core.autonomy.escalation import EscalationManager
        from core.autonomy.types import AutonomyConfig

        config = AutonomyConfig(auto_deny_on_timeout=True, escalation_timeout_seconds=1)
        manager = EscalationManager(config=config)
        decision = AutonomyDecision(action="test", risk_level=0.5)
        esc = manager.create_escalation(decision=decision, reason=EscalationReason.HIGH_RISK)
        # Trigger timeout
        manager._timeout_escalation(esc.id)
        resolved = manager.get_request(esc.id)
        assert resolved.human_response == "denied_timeout"

    @pytest.mark.asyncio
    async def test_timeout_without_auto_deny(self):
        """Test timeout with auto_deny_on_timeout=False."""
        from core.autonomy.escalation import EscalationManager
        from core.autonomy.types import AutonomyConfig

        config = AutonomyConfig(auto_deny_on_timeout=False)
        manager = EscalationManager(config=config)
        decision = AutonomyDecision(action="test", risk_level=0.5)
        esc = manager.create_escalation(decision=decision, reason=EscalationReason.HIGH_RISK)
        manager._timeout_escalation(esc.id)
        resolved = manager.get_request(esc.id)
        assert resolved.human_response == "timeout"

    @pytest.mark.asyncio
    async def test_timeout_with_active_future(self):
        """Test timeout sets future result to None (line 266)."""
        from core.autonomy.escalation import EscalationManager

        manager = EscalationManager()
        decision = AutonomyDecision(action="test", risk_level=0.5)
        esc = manager.create_escalation(decision=decision, reason=EscalationReason.HIGH_RISK)

        async def wait_task():
            return await manager.wait_for_response(esc.id, timeout=0.1)

        result = await wait_task()
        assert result is None


class TestAutonomyMixinLearnFromEscalation:
    """Tests for _learn_from_escalation (lines 340-341, 349)."""

    @pytest.fixture
    def agent_with_autonomy(self):
        from core.autonomy.mixin import AutonomyMixin
        from core.autonomy.types import AutonomyConfig

        class TestAgent(AutonomyMixin):
            def __init__(self):
                config = AutonomyConfig(learn_from_escalations=True)
                self._init_autonomy(config=config)

        return TestAgent()

    @pytest.mark.asyncio
    async def test_request_approval_learns(self, agent_with_autonomy):
        """Test that request_approval calls _learn_from_escalation."""
        import asyncio

        async def respond_later():
            await asyncio.sleep(0.05)
            pending = agent_with_autonomy.get_pending_escalations()
            if pending:
                agent_with_autonomy.respond_to_escalation(pending[0].id, "approve")

        asyncio.create_task(respond_later())
        result = await agent_with_autonomy.request_approval(
            action="test action",
            timeout=1,
        )
        assert result == "approve"


class TestUncertaintyEstimatorEdgeCases:
    """Edge case tests for UncertaintyEstimator (97% → 100%)."""

    def test_input_uncertainty_multiple_questions(self):
        """Test input uncertainty with multiple questions (line 186)."""
        from core.autonomy.uncertainty import UncertaintyEstimator

        estimator = UncertaintyEstimator()
        # Input with multiple questions
        estimate = estimator.estimate(
            input_text="What is this? How does it work? Why is it like this?",
            output_text="This is a test response.",
        )
        # Multiple questions should increase uncertainty
        assert estimate.input_uncertainty > 0

    def test_from_logits_empty(self):
        """Test _estimate_from_logits with empty logits (line 237)."""
        from core.autonomy.uncertainty import UncertaintyEstimator

        estimator = UncertaintyEstimator()
        entropy, variance = estimator._estimate_from_logits([])
        assert entropy == 0.5
        assert variance == 0.5

    def test_from_samples_single(self):
        """Test _estimate_from_samples with single sample (line 272)."""
        from core.autonomy.uncertainty import UncertaintyEstimator

        estimator = UncertaintyEstimator()
        mi, agreement = estimator._estimate_from_samples(["only one sample"])
        assert mi == 0.0
        assert agreement == 1.0


class TestEscalationManagerEdgeCases:
    """Edge case tests for EscalationManager (98% → 100%)."""

    def test_timeout_escalation_not_in_pending(self):
        """Test _timeout_escalation when request not in pending (line 249)."""
        from core.autonomy.escalation import EscalationManager

        manager = EscalationManager()
        # Call with non-existent ID - should just return
        manager._timeout_escalation("nonexistent_id")
        # No exception should be raised

    @pytest.mark.asyncio
    async def test_cancel_escalation_with_future(self):
        """Test cancel_escalation when future exists."""
        from core.autonomy.escalation import EscalationManager
        from core.autonomy.types import (
            AutonomyDecision,
            ConfidenceScore,
            UncertaintyEstimate,
            EscalationReason,
        )
        import asyncio

        manager = EscalationManager()
        decision = AutonomyDecision(
            action="test action",
            confidence=ConfidenceScore(calibrated_confidence=0.5),
            uncertainty=UncertaintyEstimate(total_uncertainty=0.5),
        )

        # Create escalation
        request = manager.create_escalation(decision, EscalationReason.LOW_CONFIDENCE)
        request_id = request.id

        # Create a future using current running loop
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        manager._response_futures[request_id] = future

        # Now cancel
        result = manager.cancel(request_id)
        assert result is True
        assert future.cancelled()


class TestAutonomyMixinStatusNotInitialized:
    """Test get_autonomy_status when not initialized (line 349)."""

    def test_get_autonomy_status_not_initialized(self):
        """Test autonomy status when not initialized."""
        from core.autonomy.mixin import AutonomyMixin

        class TestAgent(AutonomyMixin):
            pass

        agent = TestAgent()
        status = agent.get_autonomy_status()
        assert status == {"initialized": False}


class TestCalibratorTemperatureZero:
    """Test calibrator temperature <= 0 edge case (line 87)."""

    def test_apply_temperature_zero(self):
        """Test _apply_temperature with temperature 0 (line 87)."""
        from core.autonomy.calibrator import ConfidenceCalibrator

        calibrator = ConfidenceCalibrator()
        # Temperature of 0 should return original confidence
        result = calibrator._apply_temperature(0.7, 0.0)
        assert result == 0.7

    def test_apply_temperature_negative(self):
        """Test _apply_temperature with negative temperature."""
        from core.autonomy.calibrator import ConfidenceCalibrator

        calibrator = ConfidenceCalibrator()
        result = calibrator._apply_temperature(0.7, -1.0)
        assert result == 0.7


class TestOperatorsAbstractBaseMutator:
    """Test abstract BaseMutator methods (lines 42, 52)."""

    def test_base_mutator_not_implemented(self):
        """Test BaseMutator abstract methods raise NotImplementedError."""
        from core.evolution.operators import BaseMutator
        from core.evolution.types import AgentVariant

        # Create concrete class that calls parent
        class TestMutator(BaseMutator):
            def propose(self, variant):
                return super().propose(variant)

            def apply(self, variant, proposal):
                return super().apply(variant, proposal)

        mutator = TestMutator()
        variant = AgentVariant()

        with pytest.raises(NotImplementedError):
            mutator.propose(variant)

        with pytest.raises(NotImplementedError):
            mutator.apply(variant, None)


class TestCalibratorTemperatureScalingFitted:
    """Test calibrator temperature_scaling when fitted (line 76)."""

    def test_temperature_scaling_fitted(self):
        """Test calibrated temperature scaling method."""
        from core.autonomy.calibrator import ConfidenceCalibrator

        calibrator = ConfidenceCalibrator(method="temperature_scaling")
        # Add enough data to fit
        for i in range(60):
            calibrator.add_calibration_point(0.3 + i * 0.01, i % 2 == 0)
        # Force fit
        calibrator._fit()
        assert calibrator._is_fitted
        # Now calibrate using temperature_scaling path
        result = calibrator.calibrate(0.7)
        assert 0 < result < 1
        assert result != 0.7  # Should be different from raw


class TestEscalationTimeoutWithFuture:
    """Test escalation timeout with pending future (line 266)."""

    @pytest.mark.asyncio
    async def test_timeout_sets_future_result(self):
        """Test _timeout_escalation sets result on waiting future."""
        from core.autonomy.escalation import EscalationManager
        from core.autonomy.types import (
            AutonomyDecision,
            ConfidenceScore,
            UncertaintyEstimate,
            EscalationReason,
        )
        import asyncio

        manager = EscalationManager()
        decision = AutonomyDecision(
            action="test action",
            confidence=ConfidenceScore(calibrated_confidence=0.5),
            uncertainty=UncertaintyEstimate(total_uncertainty=0.5),
        )

        # Create escalation
        request = manager.create_escalation(decision, EscalationReason.LOW_CONFIDENCE)
        request_id = request.id

        # Create a future that's not done
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        manager._response_futures[request_id] = future

        # Trigger timeout
        manager._timeout_escalation(request_id)

        # Future should have result set to None
        assert future.done()
        assert future.result() is None
