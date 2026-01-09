"""File backup and rollback functionality."""

from __future__ import annotations
import logging
import hashlib
from pathlib import Path
from typing import Dict, Optional
from .types import FileBackup

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages file backups for safe editing."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self._backups: Dict[str, FileBackup] = {}

    def _hash_content(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def backup_file(self, filepath: str, content: str) -> FileBackup:
        backup = FileBackup(
            filepath=filepath,
            content=content,
            content_hash=self._hash_content(content),
        )
        self._backups[filepath] = backup
        return backup

    def get_backup(self, filepath: str) -> Optional[FileBackup]:
        return self._backups.get(filepath)

    async def rollback(self, filepath: str) -> bool:
        backup = self._backups.get(filepath)
        if not backup:
            logger.warning(f"No backup found for {filepath}")
            return False
        try:
            path = Path(filepath)
            if not path.is_absolute():
                path = self.workspace_root / path
            path.write_text(backup.content, encoding="utf-8")
            logger.info(f"Rolled back {filepath}")
            return True
        except Exception as e:
            logger.error(f"Rollback failed for {filepath}: {e}")
            return False

    def clear_backup(self, filepath: str) -> bool:
        if filepath in self._backups:
            del self._backups[filepath]
            return True
        return False

    def clear_all_backups(self) -> int:
        count = len(self._backups)
        self._backups.clear()
        return count
