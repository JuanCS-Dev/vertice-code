"""
Checkpoint Manager - State management for workflow rollback.

Implements Cursor AI pattern:
- State snapshots
- File backups
- Rollback support
"""

import copy
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import Checkpoint

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    Checkpoint system for state management (Cursor AI pattern).

    Features:
    - State snapshots
    - File backups
    - Rollback support
    """

    def __init__(self, backup_dir: Optional[Path] = None):
        self.backup_dir = backup_dir or Path.home() / ".vertice_checkpoints"
        self.backup_dir.mkdir(exist_ok=True)

        self.checkpoints: Dict[str, Checkpoint] = {}

    def create_checkpoint(
        self, checkpoint_id: str, context: Dict[str, Any], completed_steps: List[str]
    ) -> Checkpoint:
        """Create checkpoint."""
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            timestamp=__import__("time").time(),
            context=copy.deepcopy(context),
            completed_steps=completed_steps.copy(),
        )

        self.checkpoints[checkpoint_id] = checkpoint

        logger.info(f"Created checkpoint: {checkpoint_id}")
        return checkpoint

    def backup_file(self, checkpoint_id: str, file_path: str) -> None:
        """Backup file before modification."""
        if checkpoint_id not in self.checkpoints:
            logger.warning(f"Checkpoint {checkpoint_id} not found")
            return

        try:
            source = Path(file_path)
            if not source.exists():
                return

            # Create backup
            backup_path = self.backup_dir / f"{checkpoint_id}_{source.name}"
            backup_path.write_text(source.read_text())

            # Record backup
            self.checkpoints[checkpoint_id].file_backups[file_path] = str(backup_path)

            logger.info(f"Backed up: {file_path} → {backup_path}")

        except Exception as e:
            logger.error(f"Backup failed for {file_path}: {e}")

    def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """Restore from checkpoint."""
        if checkpoint_id not in self.checkpoints:
            logger.error(f"Checkpoint {checkpoint_id} not found")
            return False

        checkpoint = self.checkpoints[checkpoint_id]

        try:
            # Restore files
            for original_path, backup_path in checkpoint.file_backups.items():
                backup = Path(backup_path)
                if backup.exists():
                    Path(original_path).write_text(backup.read_text())
                    logger.info(f"Restored: {original_path}")

            logger.info(f"Checkpoint {checkpoint_id} restored successfully")
            return True

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Get checkpoint by ID."""
        return self.checkpoints.get(checkpoint_id)

    def list_checkpoints(self) -> List[str]:
        """List all checkpoint IDs."""
        return list(self.checkpoints.keys())

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete checkpoint and its backups."""
        if checkpoint_id not in self.checkpoints:
            return False

        checkpoint = self.checkpoints[checkpoint_id]

        # Delete backup files
        for backup_path in checkpoint.file_backups.values():
            try:
                Path(backup_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to delete backup {backup_path}: {e}")

        del self.checkpoints[checkpoint_id]
        return True
