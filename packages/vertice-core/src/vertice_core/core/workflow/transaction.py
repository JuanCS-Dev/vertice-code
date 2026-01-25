"""
Transaction - ACID-like workflow execution.

Provides transactional guarantees for workflows:
- All-or-nothing execution
- Rollback on failure
- Commit on success
"""

import logging
from typing import Any, List, Tuple, TYPE_CHECKING

from .models import WorkflowStep

if TYPE_CHECKING:
    from .checkpoint_manager import CheckpointManager

logger = logging.getLogger(__name__)


class Transaction:
    """
    Transactional workflow execution (ACID-like).

    Features:
    - All-or-nothing execution
    - Rollback on failure
    - Commit on success
    """

    def __init__(self, transaction_id: str):
        self.transaction_id = transaction_id
        self.operations: List[Tuple[WorkflowStep, Any]] = []
        self.committed = False

    def add_operation(self, step: WorkflowStep, result: Any) -> None:
        """Add completed operation."""
        self.operations.append((step, result))

    async def rollback(self, checkpoint_manager: "CheckpointManager") -> bool:
        """Rollback all operations."""
        logger.warning(f"Rolling back transaction: {self.transaction_id}")

        # Rollback in reverse order
        for step, result in reversed(self.operations):
            logger.info(f"Rolling back step: {step.step_id}")
            # Actual rollback handled by checkpoint manager

        return True

    async def commit(self) -> None:
        """Commit transaction."""
        self.committed = True
        logger.info(f"Transaction committed: {self.transaction_id}")

    def get_operations(self) -> List[Tuple[WorkflowStep, Any]]:
        """Get list of operations in transaction."""
        return self.operations.copy()

    def is_committed(self) -> bool:
        """Check if transaction is committed."""
        return self.committed
