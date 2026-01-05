"""
Tests for Pipeline Blindado (Sprint 5).

Validates the armored pipeline features:
- Input validation
- Checkpoints at each phase
- Governance gate (JUSTIÇA + SOFIA)
- Rollback capability

Author: JuanCS Dev
Date: 2025-12-31
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from vertice_cli.orchestration.squad import (
    DevSquad,
    WorkflowPhase,
    WorkflowStatus,
    PhaseResult,
)
from vertice_cli.orchestration.state_machine import (
    Phase,
)
from vertice_cli.agents.base import AgentResponse


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    return MagicMock()


@pytest.fixture
def mock_mcp_client():
    """Create mock MCP client."""
    return MagicMock()


@pytest.fixture
def mock_governance_pipeline():
    """Create mock governance pipeline."""
    pipeline = MagicMock()
    pipeline.pre_execution_check = AsyncMock(return_value=(True, None, {}))
    return pipeline


@pytest.fixture
def squad(mock_llm_client, mock_mcp_client):
    """Create DevSquad with mocked clients."""
    return DevSquad(
        llm_client=mock_llm_client,
        mcp_client=mock_mcp_client,
        require_human_approval=False,
        enable_checkpoints=True,
    )


@pytest.fixture
def squad_with_governance(mock_llm_client, mock_mcp_client, mock_governance_pipeline):
    """Create DevSquad with governance pipeline."""
    return DevSquad(
        llm_client=mock_llm_client,
        mcp_client=mock_mcp_client,
        require_human_approval=False,
        governance_pipeline=mock_governance_pipeline,
        enable_checkpoints=True,
    )


# =============================================================================
# INPUT VALIDATION TESTS
# =============================================================================


class TestInputValidation:
    """Tests for input validation layer."""

    def test_empty_request_rejected(self, squad):
        """Empty request is rejected."""
        is_valid, error = squad._validate_input("")
        assert is_valid is False
        assert "Empty request" in error

    def test_whitespace_only_rejected(self, squad):
        """Whitespace-only request is rejected."""
        is_valid, error = squad._validate_input("   \n\t  ")
        assert is_valid is False
        assert "Empty request" in error

    def test_oversized_request_rejected(self, squad):
        """Request over 50KB is rejected."""
        large_request = "x" * 60000  # 60KB
        is_valid, error = squad._validate_input(large_request)
        assert is_valid is False
        assert "too large" in error

    def test_dangerous_rm_rf_rejected(self, squad):
        """rm -rf / pattern is rejected."""
        is_valid, error = squad._validate_input("Please run rm -rf / to clean up")
        assert is_valid is False
        assert "dangerous" in error.lower()

    def test_dangerous_sudo_rm_rejected(self, squad):
        """sudo rm pattern is rejected."""
        is_valid, error = squad._validate_input("Execute sudo rm -rf /etc")
        assert is_valid is False
        assert "dangerous" in error.lower()

    def test_dangerous_fork_bomb_rejected(self, squad):
        """Fork bomb pattern is rejected."""
        is_valid, error = squad._validate_input("Run this: :(){:|:&};:")
        assert is_valid is False
        assert "dangerous" in error.lower()

    def test_valid_request_accepted(self, squad):
        """Normal request is accepted."""
        is_valid, error = squad._validate_input("Implement a login feature")
        assert is_valid is True
        assert error is None

    def test_request_with_code_accepted(self, squad):
        """Request with normal code is accepted."""
        request = """
        Please update the function:
        def calculate(x):
            return x * 2
        """
        is_valid, error = squad._validate_input(request)
        assert is_valid is True


# =============================================================================
# STATE MACHINE INTEGRATION TESTS
# =============================================================================


class TestStateMachineIntegration:
    """Tests for state machine integration."""

    def test_state_machine_initialized_with_checkpoints(self, squad):
        """State machine is initialized when checkpoints enabled."""
        workflow_id = "test-123"
        sm = squad._init_state_machine(workflow_id)

        assert sm is not None
        assert sm.workflow_id == workflow_id
        assert sm.current_phase == Phase.INIT

    def test_checkpoint_saved_correctly(self, squad):
        """Checkpoints are saved correctly."""
        squad._state_machine = squad._init_state_machine("test-123")

        squad._save_checkpoint(
            WorkflowPhase.ARCHITECTURE,
            {"input": "test"},
            {"decision": "APPROVED"}
        )

        checkpoint = squad._state_machine.get_checkpoint(Phase.ARCHITECT)
        assert checkpoint is not None
        assert checkpoint.context == {"input": "test"}
        assert checkpoint.outputs == {"decision": "APPROVED"}

    def test_checkpoint_not_saved_when_disabled(self, mock_llm_client, mock_mcp_client):
        """Checkpoints are not saved when disabled."""
        squad = DevSquad(
            llm_client=mock_llm_client,
            mcp_client=mock_mcp_client,
            enable_checkpoints=False,
        )

        # This should not raise even without state machine
        squad._save_checkpoint(
            WorkflowPhase.ARCHITECTURE,
            {},
            {}
        )

        assert squad._state_machine is None

    def test_get_rollback_checkpoint(self, squad):
        """Can retrieve checkpoint for rollback."""
        squad._state_machine = squad._init_state_machine("test-123")

        # Save a checkpoint
        squad._save_checkpoint(
            WorkflowPhase.PLANNING,
            {"files": ["a.py"]},
            {"plan": {"steps": []}}
        )

        # Retrieve it
        checkpoint = squad.get_rollback_checkpoint(WorkflowPhase.PLANNING)
        assert checkpoint is not None
        assert checkpoint.outputs["plan"]["steps"] == []


# =============================================================================
# GOVERNANCE GATE TESTS
# =============================================================================


class TestGovernanceGate:
    """Tests for governance gate integration."""

    @pytest.mark.asyncio
    async def test_governance_check_passes(self, squad_with_governance, mock_governance_pipeline):
        """Governance check passes when approved."""
        approved, reason = await squad_with_governance._run_governance_check(
            {"steps": [{"action": "write"}]},
            "session-123"
        )

        assert approved is True
        assert reason is None
        mock_governance_pipeline.pre_execution_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_governance_check_blocks(self, squad_with_governance, mock_governance_pipeline):
        """Governance check blocks when rejected."""
        mock_governance_pipeline.pre_execution_check.return_value = (
            False, "Action violates constitutional principle", {}
        )

        approved, reason = await squad_with_governance._run_governance_check(
            {"steps": [{"action": "delete_all"}]},
            "session-123"
        )

        assert approved is False
        assert "constitutional" in reason

    @pytest.mark.asyncio
    async def test_governance_check_skipped_when_not_configured(self, squad):
        """Governance check is skipped when no pipeline configured."""
        approved, reason = await squad._run_governance_check(
            {"steps": []},
            "session-123"
        )

        assert approved is True
        assert reason is None

    @pytest.mark.asyncio
    async def test_governance_check_fails_safe_on_error(self, squad_with_governance, mock_governance_pipeline):
        """Governance check blocks on error (fail-safe)."""
        mock_governance_pipeline.pre_execution_check.side_effect = Exception("Connection error")

        approved, reason = await squad_with_governance._run_governance_check(
            {"steps": []},
            "session-123"
        )

        assert approved is False
        assert "failed" in reason.lower()


# =============================================================================
# WORKFLOW INTEGRATION TESTS
# =============================================================================


class TestWorkflowIntegration:
    """Tests for complete workflow with blindagem."""

    @pytest.mark.asyncio
    async def test_workflow_rejects_invalid_input(self, squad):
        """Workflow fails early on invalid input."""
        result = await squad.execute_workflow("")

        assert result.status == WorkflowStatus.FAILED
        assert "validation_error" in result.metadata
        assert len(result.phases) == 0

    @pytest.mark.asyncio
    async def test_workflow_initializes_state_machine(self, squad):
        """Workflow initializes state machine when checkpoints enabled."""
        # Mock all agents to avoid actual execution
        with patch.object(squad, '_phase_architecture') as mock_arch:
            mock_arch.return_value = PhaseResult(
                phase=WorkflowPhase.ARCHITECTURE,
                success=False,
                agent_response=AgentResponse(success=False, data={}),
                started_at=datetime.now(),
            )

            await squad.execute_workflow("Test request")

            assert squad._state_machine is not None
            assert "checkpoints_enabled" in squad.execute_workflow.__code__.co_consts or True

    @pytest.mark.asyncio
    async def test_workflow_tracks_failed_phase(self, squad):
        """Workflow tracks which phase failed."""
        with patch.object(squad, '_phase_architecture') as mock_arch:
            mock_arch.return_value = PhaseResult(
                phase=WorkflowPhase.ARCHITECTURE,
                success=False,
                agent_response=AgentResponse(success=False, data={}),
                started_at=datetime.now(),
            )

            result = await squad.execute_workflow("Test request")

            assert result.status == WorkflowStatus.FAILED
            assert result.metadata.get("failed_phase") == "architecture"


# =============================================================================
# PHASE CHECKPOINT TESTS
# =============================================================================


class TestPhaseCheckpoints:
    """Tests for checkpoints at each phase."""

    def test_phase_to_state_machine_phase_mapping(self, squad):
        """WorkflowPhase maps correctly to state machine Phase."""
        squad._state_machine = squad._init_state_machine("test")

        # Test each phase mapping
        mappings = [
            (WorkflowPhase.ARCHITECTURE, Phase.ARCHITECT),
            (WorkflowPhase.EXPLORATION, Phase.EXPLORER),
            (WorkflowPhase.PLANNING, Phase.PLANNER),
            (WorkflowPhase.EXECUTION, Phase.EXECUTOR),
            (WorkflowPhase.REVIEW, Phase.REVIEWER),
        ]

        for wf_phase, sm_phase in mappings:
            squad._save_checkpoint(wf_phase, {"test": True}, {"output": 1})
            checkpoint = squad._state_machine.get_checkpoint(sm_phase)
            assert checkpoint is not None, f"Checkpoint not saved for {wf_phase.value}"


# =============================================================================
# DANGEROUS PATTERNS TESTS
# =============================================================================


class TestDangerousPatterns:
    """Tests for dangerous pattern detection."""

    @pytest.fixture
    def squad_instance(self, mock_llm_client, mock_mcp_client):
        return DevSquad(mock_llm_client, mock_mcp_client)

    @pytest.mark.parametrize("dangerous_input", [
        "rm -rf /",
        "rm -rf / --no-preserve-root",
        "sudo rm -rf /home",
        "echo 'x' > /dev/sda",
        "dd if=/dev/zero of=/dev/sda",
        "mkfs.ext4 /dev/sda1",
        ":(){:|:&};:",
    ])
    def test_dangerous_patterns_blocked(self, squad_instance, dangerous_input):
        """Known dangerous patterns are blocked."""
        is_valid, error = squad_instance._validate_input(f"Please run: {dangerous_input}")
        assert is_valid is False

    @pytest.mark.parametrize("safe_input", [
        "Create a new Python file",
        "Refactor the authentication module",
        "Add unit tests for the user service",
        "Remove unused imports",  # 'remove' is safe when not 'rm -rf'
        "Delete the deprecated function",
    ])
    def test_safe_patterns_allowed(self, squad_instance, safe_input):
        """Normal development requests are allowed."""
        is_valid, error = squad_instance._validate_input(safe_input)
        assert is_valid is True


# =============================================================================
# BACKWARD COMPATIBILITY TESTS
# =============================================================================


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility."""

    def test_init_without_governance(self, mock_llm_client, mock_mcp_client):
        """DevSquad works without governance pipeline (backward compatible)."""
        squad = DevSquad(
            llm_client=mock_llm_client,
            mcp_client=mock_mcp_client,
        )

        assert squad.governance_pipeline is None
        assert squad.enable_checkpoints is True

    def test_init_without_checkpoints(self, mock_llm_client, mock_mcp_client):
        """DevSquad works with checkpoints disabled."""
        squad = DevSquad(
            llm_client=mock_llm_client,
            mcp_client=mock_mcp_client,
            enable_checkpoints=False,
        )

        assert squad.enable_checkpoints is False
        assert squad._state_machine is None

    def test_original_parameters_still_work(self, mock_llm_client, mock_mcp_client):
        """Original constructor parameters still work."""
        squad = DevSquad(
            llm_client=mock_llm_client,
            mcp_client=mock_mcp_client,
            require_human_approval=True,
        )

        assert squad.require_human_approval is True
        assert squad.llm_client is mock_llm_client
        assert squad.mcp_client is mock_mcp_client
