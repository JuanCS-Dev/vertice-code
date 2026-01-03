"""
Partial Rollback - Granular operation rollback.

Maintains a stack of reversible operations for fine-grained
error recovery. Day 7 enhancement for workflow orchestration.
"""

import logging
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class PartialRollback:
    """Granular rollback of individual operations.

    Maintains a stack of reversible operations that can be undone
    individually or in groups. Useful for fine-grained error recovery.
    """

    def __init__(self) -> None:
        """Initialize partial rollback manager."""
        self.operations: List[Dict[str, Any]] = []

    def add_operation(
        self,
        op_type: str,
        data: Dict[str, Any],
        reversible: bool = True
    ) -> None:
        """Add reversible operation to stack.

        Args:
            op_type: Type of operation (file_write, file_delete, etc)
            data: Operation data needed for rollback
            reversible: Whether operation can be reversed
        """
        self.operations.append({
            'type': op_type,
            'data': data,
            'timestamp': time.time(),
            'reversible': reversible
        })

        logger.debug(f"Added operation to rollback stack: {op_type}")

    async def rollback_last_n(self, n: int) -> Tuple[int, int]:
        """Rollback last N operations.

        Args:
            n: Number of operations to rollback

        Returns:
            (successful_rollbacks, failed_rollbacks)
        """
        successful = 0
        failed = 0

        for _ in range(min(n, len(self.operations))):
            op = self.operations.pop()

            if not op['reversible']:
                logger.warning(f"Operation {op['type']} is not reversible")
                failed += 1
                continue

            try:
                await self._rollback_operation(op)
                successful += 1
            except Exception as e:
                logger.error(f"Failed to rollback {op['type']}: {e}")
                failed += 1

        logger.info(f"Rolled back {successful}/{successful+failed} operations")
        return successful, failed

    async def rollback_until(self, target_timestamp: float) -> Tuple[int, int]:
        """Rollback operations until target timestamp.

        Args:
            target_timestamp: Rollback operations after this time

        Returns:
            (successful_rollbacks, failed_rollbacks)
        """
        count = 0
        for op in reversed(self.operations):
            if op['timestamp'] <= target_timestamp:
                break
            count += 1

        return await self.rollback_last_n(count)

    async def _rollback_operation(self, op: Dict[str, Any]) -> None:
        """Rollback single operation.

        Args:
            op: Operation to rollback
        """
        op_type = op['type']
        data = op['data']

        if op_type == 'file_write':
            # Restore from backup
            if 'backup_path' in data:
                shutil.copy(data['backup_path'], data['file_path'])
                logger.debug(f"Restored {data['file_path']} from backup")

        elif op_type == 'file_delete':
            # Restore deleted file
            if 'backup_content' in data:
                Path(data['file_path']).write_text(data['backup_content'])
                logger.debug(f"Restored deleted file {data['file_path']}")

        elif op_type == 'file_edit':
            # Restore previous content
            if 'original_content' in data:
                Path(data['file_path']).write_text(data['original_content'])
                logger.debug(f"Restored original content of {data['file_path']}")

        elif op_type == 'command_execute':
            # Most commands are irreversible
            logger.warning(
                f"Cannot rollback command execution: {data.get('command', 'unknown')}"
            )

        else:
            logger.warning(f"Unknown operation type: {op_type}")

    def get_operations(self) -> List[Dict[str, Any]]:
        """Get list of tracked operations.

        Returns:
            List of operation dictionaries
        """
        return self.operations.copy()

    def clear_operations(self) -> None:
        """Clear operations stack."""
        self.operations.clear()

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of operations.

        Returns:
            Summary dictionary
        """
        return {
            'total_operations': len(self.operations),
            'reversible': sum(1 for op in self.operations if op['reversible']),
            'irreversible': sum(1 for op in self.operations if not op['reversible']),
            'types': list(set(op['type'] for op in self.operations)),
            'oldest': self.operations[0]['timestamp'] if self.operations else None,
            'newest': self.operations[-1]['timestamp'] if self.operations else None
        }
