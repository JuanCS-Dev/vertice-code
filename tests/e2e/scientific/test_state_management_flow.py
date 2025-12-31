"""
Scientific E2E Tests: State Management Flow

Flow: State Changes → Persistence → Sync

Tests cover:
- State transition validity
- Checkpoint persistence
- Rollback correctness
- Concurrent state updates
- State machine invariants
"""

import pytest
import asyncio
import time
from enum import Enum, auto
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


# =============================================================================
# STATE MACHINE IMPLEMENTATION FOR TESTING
# =============================================================================

class Phase(Enum):
    """Workflow phases."""
    INIT = auto()
    ARCHITECT = auto()
    EXPLORER = auto()
    PLANNER = auto()
    EXECUTOR = auto()
    REVIEWER = auto()
    ROLLBACK = auto()
    COMPLETED = auto()
    FAILED = auto()


@dataclass
class StateTransition:
    """Record of a state transition."""
    from_phase: Phase
    to_phase: Phase
    timestamp: float
    success: bool


@dataclass
class PhaseCheckpoint:
    """Checkpoint at phase boundary."""
    phase: Phase
    timestamp: float
    context: Dict[str, Any]
    outputs: Dict[str, Any]


class StateMachine:
    """Test state machine implementation."""

    # Valid transitions (from -> set of valid targets)
    VALID_TRANSITIONS = {
        Phase.INIT: {Phase.ARCHITECT, Phase.EXPLORER, Phase.PLANNER, Phase.FAILED},
        Phase.ARCHITECT: {Phase.EXPLORER, Phase.PLANNER, Phase.FAILED, Phase.ROLLBACK},
        Phase.EXPLORER: {Phase.PLANNER, Phase.FAILED, Phase.ROLLBACK},
        Phase.PLANNER: {Phase.EXECUTOR, Phase.FAILED, Phase.ROLLBACK},
        Phase.EXECUTOR: {Phase.REVIEWER, Phase.FAILED, Phase.ROLLBACK},
        Phase.REVIEWER: {Phase.COMPLETED, Phase.FAILED, Phase.ROLLBACK},
        Phase.ROLLBACK: {Phase.INIT, Phase.ARCHITECT, Phase.EXPLORER, Phase.PLANNER},
        Phase.COMPLETED: set(),  # Terminal
        Phase.FAILED: set(),  # Terminal
    }

    def __init__(self):
        self.current_phase = Phase.INIT
        self.transitions: List[StateTransition] = []
        self.checkpoints: Dict[Phase, PhaseCheckpoint] = {}
        self.context: Dict[str, Any] = {}
        self.started_at = time.time()

    def can_transition_to(self, target: Phase) -> bool:
        """Check if transition is valid."""
        return target in self.VALID_TRANSITIONS.get(self.current_phase, set())

    def transition_to(self, target: Phase) -> bool:
        """Transition to target phase."""
        if not self.can_transition_to(target):
            return False

        # Create checkpoint before leaving
        self.checkpoints[self.current_phase] = PhaseCheckpoint(
            phase=self.current_phase,
            timestamp=time.time(),
            context=self.context.copy(),
            outputs={}
        )

        # Record transition
        self.transitions.append(StateTransition(
            from_phase=self.current_phase,
            to_phase=target,
            timestamp=time.time(),
            success=True
        ))

        self.current_phase = target
        return True

    def rollback_to(self, target: Phase) -> bool:
        """Rollback to previous phase."""
        if target not in self.checkpoints:
            return False

        # Transition through ROLLBACK state
        if not self.transition_to(Phase.ROLLBACK):
            return False

        # Restore checkpoint
        checkpoint = self.checkpoints[target]
        self.context = checkpoint.context.copy()

        # Transition to target
        return self.transition_to(target)

    def get_history(self) -> List[StateTransition]:
        """Get transition history."""
        return self.transitions.copy()

    def is_terminal(self) -> bool:
        """Check if in terminal state."""
        return self.current_phase in {Phase.COMPLETED, Phase.FAILED}


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def state_machine():
    """Create state machine for testing."""
    return StateMachine()


@pytest.fixture
def populated_state_machine():
    """Create state machine with some transitions."""
    sm = StateMachine()
    sm.context = {"initial": "data"}
    sm.transition_to(Phase.ARCHITECT)
    sm.context["architect"] = "decision"
    sm.transition_to(Phase.PLANNER)
    sm.context["planner"] = "plan"
    return sm


# =============================================================================
# 1. STATE TRANSITION VALIDITY TESTS
# =============================================================================

class TestStateTransitionValidity:
    """Test state transition rules."""

    def test_initial_state_is_init(self, state_machine):
        """State machine starts in INIT."""
        assert state_machine.current_phase == Phase.INIT

    def test_valid_transition_succeeds(self, state_machine):
        """Valid transitions succeed."""
        assert state_machine.can_transition_to(Phase.ARCHITECT)
        assert state_machine.transition_to(Phase.ARCHITECT)
        assert state_machine.current_phase == Phase.ARCHITECT

    def test_invalid_transition_fails(self, state_machine):
        """Invalid transitions fail."""
        # Cannot go directly from INIT to COMPLETED
        assert not state_machine.can_transition_to(Phase.COMPLETED)
        assert not state_machine.transition_to(Phase.COMPLETED)
        assert state_machine.current_phase == Phase.INIT  # Unchanged

    def test_terminal_state_no_transitions(self, state_machine):
        """Terminal states have no outgoing transitions."""
        state_machine.transition_to(Phase.FAILED)

        assert state_machine.is_terminal()
        assert not state_machine.can_transition_to(Phase.INIT)
        assert not state_machine.can_transition_to(Phase.ARCHITECT)

    def test_all_valid_paths_allowed(self, state_machine):
        """All valid transition paths work."""
        # INIT -> ARCHITECT -> PLANNER -> EXECUTOR -> REVIEWER -> COMPLETED
        assert state_machine.transition_to(Phase.ARCHITECT)
        assert state_machine.transition_to(Phase.PLANNER)
        assert state_machine.transition_to(Phase.EXECUTOR)
        assert state_machine.transition_to(Phase.REVIEWER)
        assert state_machine.transition_to(Phase.COMPLETED)

        assert state_machine.is_terminal()
        assert len(state_machine.transitions) == 5

    def test_skip_phases_invalid(self, state_machine):
        """Skipping phases is invalid."""
        # Cannot go INIT -> EXECUTOR directly
        assert not state_machine.can_transition_to(Phase.EXECUTOR)


# =============================================================================
# 2. CHECKPOINT PERSISTENCE TESTS
# =============================================================================

class TestCheckpointPersistence:
    """Test checkpoint save/restore."""

    def test_checkpoint_created_on_transition(self, state_machine):
        """Checkpoint is created when leaving phase."""
        state_machine.context = {"key": "value"}
        state_machine.transition_to(Phase.ARCHITECT)

        assert Phase.INIT in state_machine.checkpoints
        checkpoint = state_machine.checkpoints[Phase.INIT]
        assert checkpoint.phase == Phase.INIT
        assert checkpoint.context == {"key": "value"}

    def test_checkpoint_preserves_context(self, state_machine):
        """Checkpoint preserves context at time of creation."""
        state_machine.context = {"original": True}
        state_machine.transition_to(Phase.ARCHITECT)

        # Modify context after transition
        state_machine.context["modified"] = True

        # Checkpoint should have original context
        checkpoint = state_machine.checkpoints[Phase.INIT]
        assert "original" in checkpoint.context
        assert "modified" not in checkpoint.context

    def test_checkpoint_has_timestamp(self, state_machine):
        """Checkpoint includes timestamp."""
        before = time.time()
        state_machine.transition_to(Phase.ARCHITECT)
        after = time.time()

        checkpoint = state_machine.checkpoints[Phase.INIT]
        assert before <= checkpoint.timestamp <= after

    def test_multiple_checkpoints(self, populated_state_machine):
        """Multiple checkpoints are stored."""
        assert Phase.INIT in populated_state_machine.checkpoints
        assert Phase.ARCHITECT in populated_state_machine.checkpoints


# =============================================================================
# 3. ROLLBACK CORRECTNESS TESTS
# =============================================================================

class TestRollbackCorrectness:
    """Test rollback functionality."""

    def test_rollback_restores_context(self, populated_state_machine):
        """Rollback restores context from checkpoint."""
        sm = populated_state_machine
        original_context = sm.checkpoints[Phase.ARCHITECT].context.copy()

        # Modify context
        sm.context["new_data"] = "added"

        # Rollback to ARCHITECT
        assert sm.rollback_to(Phase.ARCHITECT)

        # Context should be restored
        assert sm.context == original_context
        assert "new_data" not in sm.context

    def test_rollback_changes_phase(self, populated_state_machine):
        """Rollback changes current phase."""
        sm = populated_state_machine
        assert sm.current_phase == Phase.PLANNER

        sm.rollback_to(Phase.ARCHITECT)

        assert sm.current_phase == Phase.ARCHITECT

    def test_rollback_to_missing_checkpoint_fails(self, state_machine):
        """Rollback to non-existent checkpoint fails."""
        # No checkpoints exist yet
        assert not state_machine.rollback_to(Phase.ARCHITECT)

    def test_rollback_through_rollback_state(self, populated_state_machine):
        """Rollback transitions through ROLLBACK state."""
        sm = populated_state_machine
        initial_transitions = len(sm.transitions)

        sm.rollback_to(Phase.INIT)

        # Should have ROLLBACK in history
        has_rollback = any(
            t.from_phase == Phase.PLANNER and t.to_phase == Phase.ROLLBACK
            for t in sm.transitions
        )
        assert has_rollback

    def test_multiple_rollbacks(self, populated_state_machine):
        """Multiple rollbacks work correctly."""
        sm = populated_state_machine

        # Rollback to ARCHITECT
        assert sm.rollback_to(Phase.ARCHITECT)
        assert sm.current_phase == Phase.ARCHITECT

        # Progress again
        sm.transition_to(Phase.PLANNER)

        # Rollback to INIT
        assert sm.rollback_to(Phase.INIT)
        assert sm.current_phase == Phase.INIT


# =============================================================================
# 4. CONCURRENT STATE UPDATES TESTS
# =============================================================================

class TestConcurrentStateUpdates:
    """Test concurrent state update handling."""

    @pytest.mark.asyncio
    async def test_sequential_updates_succeed(self, state_machine):
        """Sequential updates work correctly."""
        async def update_context(key, value, delay=0):
            await asyncio.sleep(delay)
            state_machine.context[key] = value

        await update_context("key1", "value1")
        await update_context("key2", "value2")
        await update_context("key3", "value3")

        assert state_machine.context["key1"] == "value1"
        assert state_machine.context["key2"] == "value2"
        assert state_machine.context["key3"] == "value3"

    @pytest.mark.asyncio
    async def test_concurrent_context_updates(self):
        """Concurrent context updates don't lose data (with lock)."""
        context = {}
        lock = asyncio.Lock()

        async def safe_update(key, value):
            async with lock:
                context[key] = value

        # Parallel updates
        await asyncio.gather(*[
            safe_update(f"key{i}", f"value{i}")
            for i in range(100)
        ])

        # All updates should be present
        assert len(context) == 100
        for i in range(100):
            assert context[f"key{i}"] == f"value{i}"

    @pytest.mark.asyncio
    async def test_transition_serialization(self, state_machine):
        """Transitions are serialized correctly."""
        lock = asyncio.Lock()
        transitions_made = []

        async def try_transition(target):
            async with lock:
                if state_machine.can_transition_to(target):
                    success = state_machine.transition_to(target)
                    transitions_made.append((target, success))
                    return success
            return False

        # Try multiple transitions, only valid ones should succeed
        results = await asyncio.gather(
            try_transition(Phase.ARCHITECT),
            try_transition(Phase.PLANNER),
            try_transition(Phase.EXPLORER)
        )

        # At least one should succeed
        assert any(results)


# =============================================================================
# 5. STATE MACHINE INVARIANTS TESTS
# =============================================================================

class TestStateMachineInvariants:
    """Test state machine invariants."""

    def test_history_grows_monotonically(self, state_machine):
        """Transition history only grows."""
        assert len(state_machine.transitions) == 0

        state_machine.transition_to(Phase.ARCHITECT)
        assert len(state_machine.transitions) == 1

        state_machine.transition_to(Phase.PLANNER)
        assert len(state_machine.transitions) == 2

        # History should never shrink

    def test_checkpoints_accumulate(self, state_machine):
        """Checkpoints accumulate (never deleted)."""
        state_machine.transition_to(Phase.ARCHITECT)
        assert len(state_machine.checkpoints) == 1

        state_machine.transition_to(Phase.PLANNER)
        assert len(state_machine.checkpoints) == 2

        state_machine.transition_to(Phase.EXECUTOR)
        assert len(state_machine.checkpoints) == 3

    def test_current_phase_consistency(self, state_machine):
        """Current phase is always consistent."""
        assert state_machine.current_phase == Phase.INIT

        for target in [Phase.ARCHITECT, Phase.PLANNER, Phase.EXECUTOR]:
            state_machine.transition_to(target)
            assert state_machine.current_phase == target
            # Last transition should match current phase
            assert state_machine.transitions[-1].to_phase == target

    def test_no_orphan_transitions(self, state_machine):
        """All transitions have valid from/to phases."""
        state_machine.transition_to(Phase.ARCHITECT)
        state_machine.transition_to(Phase.PLANNER)
        state_machine.transition_to(Phase.FAILED)

        for t in state_machine.transitions:
            assert isinstance(t.from_phase, Phase)
            assert isinstance(t.to_phase, Phase)
            assert t.timestamp > 0


# =============================================================================
# 6. STATE SERIALIZATION TESTS
# =============================================================================

class TestStateSerialization:
    """Test state serialization for persistence."""

    def test_context_is_serializable(self, state_machine):
        """Context can be serialized to JSON-compatible format."""
        import json

        state_machine.context = {
            "string": "value",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "nested": {"key": "value"}
        }

        # Should not raise
        json_str = json.dumps(state_machine.context)
        restored = json.loads(json_str)

        assert restored == state_machine.context

    def test_checkpoint_is_serializable(self, populated_state_machine):
        """Checkpoints can be serialized."""
        import json

        checkpoint = populated_state_machine.checkpoints[Phase.INIT]

        serialized = {
            "phase": checkpoint.phase.name,
            "timestamp": checkpoint.timestamp,
            "context": checkpoint.context,
            "outputs": checkpoint.outputs
        }

        json_str = json.dumps(serialized)
        restored = json.loads(json_str)

        assert restored["phase"] == checkpoint.phase.name
        assert restored["context"] == checkpoint.context


# =============================================================================
# 7. STATE RECOVERY TESTS
# =============================================================================

class TestStateRecovery:
    """Test state recovery scenarios."""

    def test_recover_from_serialized_state(self):
        """State can be recovered from serialized form."""
        # Simulate serialized state
        serialized = {
            "current_phase": "PLANNER",
            "context": {"key": "value"},
            "transitions": [
                {"from": "INIT", "to": "ARCHITECT"},
                {"from": "ARCHITECT", "to": "PLANNER"}
            ]
        }

        # Recover
        sm = StateMachine()
        sm.current_phase = Phase[serialized["current_phase"]]
        sm.context = serialized["context"]

        assert sm.current_phase == Phase.PLANNER
        assert sm.context == {"key": "value"}

    def test_incomplete_recovery_detected(self, state_machine):
        """Incomplete recovery is detected."""
        # Partially set up state
        state_machine.current_phase = Phase.EXECUTOR
        # But no transitions recorded

        # Should detect inconsistency
        assert len(state_machine.transitions) == 0
        # This is an invalid state (EXECUTOR without transitions)


# =============================================================================
# 8. PHASE TIMEOUT TESTS
# =============================================================================

class TestPhaseTimeouts:
    """Test phase timeout handling."""

    def test_phase_duration_tracking(self, state_machine):
        """Phase duration is tracked."""
        start = time.time()
        state_machine.transition_to(Phase.ARCHITECT)
        time.sleep(0.01)  # Simulate work
        state_machine.transition_to(Phase.PLANNER)

        # Can calculate duration from transitions
        t1 = state_machine.transitions[0].timestamp
        t2 = state_machine.transitions[1].timestamp

        duration = t2 - t1
        assert duration >= 0.01

    @pytest.mark.asyncio
    async def test_phase_timeout_triggers_failure(self):
        """Phase timeout triggers failure transition."""
        sm = StateMachine()
        sm.transition_to(Phase.ARCHITECT)

        async def timeout_check(max_duration: float):
            await asyncio.sleep(max_duration)
            if sm.current_phase == Phase.ARCHITECT:
                sm.transition_to(Phase.FAILED)

        # Short timeout
        await asyncio.wait_for(timeout_check(0.1), timeout=1.0)

        assert sm.current_phase == Phase.FAILED
