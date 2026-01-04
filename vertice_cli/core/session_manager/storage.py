"""
Session Storage - I/O operations for session persistence.

Handles saving, loading, and indexing of session files.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from .types import SessionSnapshot, SessionInfo, SessionState

logger = logging.getLogger(__name__)


def compute_checksum(data: Dict[str, Any]) -> str:
    """Compute checksum for data integrity verification."""
    # Exclude checksum field itself
    data_copy = {k: v for k, v in data.items() if k != "checksum"}
    content = json.dumps(data_copy, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def get_session_path(session_dir: Path, session_id: str, enable_compression: bool) -> Path:
    """Get path for session file."""
    ext = ".json.gz" if enable_compression else ".json"
    return session_dir / f"{session_id}{ext}"


def save_session(
    snapshot: SessionSnapshot,
    path: Path,
    enable_compression: bool = True,
    compression_threshold: int = 10 * 1024,
) -> bool:
    """
    Save session snapshot to file with ATOMIC WRITE.

    P0 FIX: Uses write-to-temp-then-rename pattern to prevent
    corrupted files on crash or power loss.

    Args:
        snapshot: Session snapshot to save.
        path: Base path for the file.
        enable_compression: Whether to enable gzip compression.
        compression_threshold: Compress if content exceeds this size.

    Returns:
        True if save was successful.
    """
    try:
        data = snapshot.to_dict()
        data["checksum"] = compute_checksum(data)

        content = json.dumps(data, indent=2)

        # Determine final path with correct extension
        if enable_compression and len(content) > compression_threshold:
            final_path = path.with_suffix(".json.gz")
            use_compression = True
        else:
            final_path = path.with_suffix(".json")
            use_compression = False

        # P0 FIX: Atomic write using temp file + rename
        # Write to temp file in same directory (ensures same filesystem for rename)
        fd, temp_path = tempfile.mkstemp(
            suffix=".tmp", dir=str(final_path.parent), prefix=".session_"
        )

        try:
            if use_compression:
                # Close fd first, gzip.open will open fresh
                os.close(fd)
                with gzip.open(temp_path, "wt", encoding="utf-8") as f:
                    f.write(content)
            else:
                # Write directly to fd
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(content)
                # fd is now closed by context manager

            # Ensure data is flushed to disk before rename
            # (rename is atomic on POSIX, this ensures the temp file is complete)
            if hasattr(os, "sync"):
                os.sync()

            # Atomic rename (overwrites existing file atomically on POSIX)
            os.replace(temp_path, str(final_path))

            return True

        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    except (OSError, IOError, ValueError, TypeError) as e:
        logger.error(f"Failed to save session: {e}")
        return False


def load_session(path: Path) -> Optional[SessionSnapshot]:
    """
    Load session snapshot from file.

    Args:
        path: Path to session file.

    Returns:
        Session snapshot if found and valid, None otherwise.
    """
    try:
        # Try compressed first
        if path.with_suffix(".json.gz").exists():
            path = path.with_suffix(".json.gz")
            with gzip.open(str(path), "rt", encoding="utf-8") as f:
                content = f.read()
        elif path.with_suffix(".json").exists():
            path = path.with_suffix(".json")
            content = path.read_text()
        else:
            return None

        data = json.loads(content)

        # P1 FIX: Proper checksum validation with recovery options
        expected_checksum = data.get("checksum", "")
        actual_checksum = compute_checksum(data)

        if expected_checksum and expected_checksum != actual_checksum:
            logger.warning(
                f"Session checksum mismatch: {path}. "
                f"Expected: {expected_checksum[:8]}..., Got: {actual_checksum[:8]}..."
            )
            # Ensure metadata exists before marking
            if "metadata" not in data:
                data["metadata"] = {}
            data["metadata"]["checksum_mismatch"] = True
            data["metadata"]["expected_checksum"] = expected_checksum
            data["metadata"]["actual_checksum"] = actual_checksum
            data["metadata"][
                "corruption_warning"
            ] = "Session data may be corrupted. Consider creating a new session."

        return SessionSnapshot.from_dict(data)

    except Exception as e:
        logger.error(f"Failed to load session: {e}")
        return None


def update_index(
    session_dir: Path,
    index_file: str,
    session_info: SessionInfo,
    max_sessions: int = 50,
) -> None:
    """
    Update session index file.

    Args:
        session_dir: Directory containing sessions.
        index_file: Name of the index file.
        session_info: Session info to add/update.
        max_sessions: Maximum number of sessions to keep.
    """
    index_path = session_dir / index_file
    index: Dict[str, Dict[str, Any]] = {}

    if index_path.exists():
        try:
            index = json.loads(index_path.read_text())
        except (json.JSONDecodeError, FileNotFoundError, PermissionError):
            pass

    index[session_info.session_id] = {
        "state": session_info.state.value,
        "created_at": session_info.created_at,
        "updated_at": session_info.updated_at,
        "message_count": session_info.message_count,
        "working_directory": session_info.working_directory,
        "summary": session_info.summary,
    }

    # Prune old sessions
    if len(index) > max_sessions:
        sorted_sessions = sorted(index.items(), key=lambda x: x[1]["updated_at"], reverse=True)
        index = dict(sorted_sessions[:max_sessions])

        # Delete old session files
        for session_id, _ in sorted_sessions[max_sessions:]:
            for ext in [".json", ".json.gz"]:
                path = session_dir / f"{session_id}{ext}"
                if path.exists():
                    try:
                        path.unlink()
                    except (OSError, PermissionError):
                        pass

    index_path.write_text(json.dumps(index, indent=2))


def load_index(session_dir: Path, index_file: str) -> Dict[str, Dict[str, Any]]:
    """
    Load session index.

    Args:
        session_dir: Directory containing sessions.
        index_file: Name of the index file.

    Returns:
        Index dictionary.
    """
    index_path = session_dir / index_file

    if not index_path.exists():
        return {}

    try:
        return json.loads(index_path.read_text())
    except Exception as e:
        logger.error(f"Failed to load session index: {e}")
        return {}


__all__ = [
    "compute_checksum",
    "get_session_path",
    "save_session",
    "load_session",
    "update_index",
    "load_index",
]
