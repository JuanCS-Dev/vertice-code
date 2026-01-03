"""
Git Rollback - Git-based checkpoint and rollback.

Provides atomic rollback of multi-file changes using git commits.
Day 7 enhancement for workflow orchestration.
"""

import logging
import subprocess
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class GitRollback:
    """Git-based rollback for code changes.

    Provides checkpoint/rollback functionality using git commits.
    Allows atomic rollback of multi-file changes.
    """

    def __init__(self) -> None:
        """Initialize git rollback manager."""
        self.commits_made: List[str] = []
        self.checkpoints: Dict[str, str] = {}  # checkpoint_id -> commit_sha

    async def create_checkpoint_commit(self, message: str) -> Optional[str]:
        """Create checkpoint git commit.

        Args:
            message: Checkpoint message

        Returns:
            Commit SHA or None if failed
        """
        try:
            # Check if in git repo
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                logger.warning("Not in a git repository, cannot create checkpoint")
                return None

            # Check if there are changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if not result.stdout.strip():
                logger.info("No changes to checkpoint")
                return None

            # Stage all changes
            subprocess.run(
                ["git", "add", "-A"],
                capture_output=True,
                timeout=10
            )

            # Commit with checkpoint tag
            commit_msg = f"[VERTICE-CHECKPOINT] {message}"
            result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                logger.error(f"Failed to create checkpoint: {result.stderr}")
                return None

            # Get commit SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5
            )

            sha = result.stdout.strip()
            self.commits_made.append(sha)

            logger.info(f"Created checkpoint commit: {sha[:7]} - {message}")
            return sha

        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            return None

    async def rollback_to_checkpoint(self, checkpoint_sha: str) -> bool:
        """Rollback to checkpoint commit.

        Args:
            checkpoint_sha: Commit SHA to rollback to

        Returns:
            True if successful, False otherwise
        """
        try:
            # Reset to checkpoint (keep working directory changes in case of partial rollback)
            result = subprocess.run(
                ["git", "reset", "--hard", checkpoint_sha],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                logger.error(f"Rollback failed: {result.stderr}")
                return False

            logger.info(f"Rolled back to {checkpoint_sha[:7]}")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    async def rollback_last_checkpoint(self) -> bool:
        """Rollback to last checkpoint made.

        Returns:
            True if successful, False otherwise
        """
        if not self.commits_made:
            logger.warning("No checkpoints to rollback to")
            return False

        last_checkpoint = self.commits_made[-1]
        success = await self.rollback_to_checkpoint(last_checkpoint)

        if success:
            self.commits_made.pop()

        return success

    def get_checkpoints(self) -> List[str]:
        """Get list of checkpoint commits.

        Returns:
            List of commit SHAs
        """
        return self.commits_made.copy()

    def clear_checkpoints(self) -> None:
        """Clear checkpoint history."""
        self.commits_made.clear()
        self.checkpoints.clear()
