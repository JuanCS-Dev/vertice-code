"""
Knowledge Vault - Secure Sensitive Data Storage

Based on MIRIX architecture (arXiv:2507.07957).
Stores credentials, bookmarks, API keys, and other sensitive
information with appropriate security levels.

Reference: https://arxiv.org/abs/2507.07957

WARNING: This is NOT a production-grade secrets manager.
For production, use proper secrets management (HashiCorp Vault,
AWS Secrets Manager, etc.). This is for agent memory context only.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
import hashlib
import base64
import logging
import os
from datetime import datetime
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class VaultEntryType(str, Enum):
    """Types of vault entries (MIRIX spec)."""

    CREDENTIAL = "credential"
    BOOKMARK = "bookmark"
    CONTACT_INFO = "contact_info"
    API_KEY = "api_key"  # pragma: allowlist secret  # pragma: allowlist secret
    CONFIG = "config"
    NOTE = "note"


class SensitivityLevel(str, Enum):
    """Sensitivity levels for vault entries."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class VaultEntry:
    """
    A knowledge vault entry.

    Attributes:
        id: Unique identifier.
        name: Entry identifier/name.
        entry_type: Type of entry.
        source: Where this came from.
        sensitivity_level: Security level.
        value: The actual data (may be obfuscated).
        metadata: Additional context.
        created_at: Creation timestamp.
        last_accessed: Last access timestamp.
    """

    id: str
    name: str
    entry_type: VaultEntryType
    source: str
    sensitivity_level: SensitivityLevel
    value: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_accessed: Optional[str] = None

    def to_dict(self, include_value: bool = False) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Args:
            include_value: Whether to include the actual value.

        Returns:
            Dictionary representation.
        """
        result = {
            "id": self.id,
            "name": self.name,
            "entry_type": self.entry_type.value,
            "source": self.source,
            "sensitivity_level": self.sensitivity_level.value,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
        }
        if include_value:
            result["value"] = self.value
        else:
            result["value"] = "[REDACTED]"
        return result


class KnowledgeVault:
    """
    Knowledge Vault - Secure Storage for Sensitive Data.

    Stores credentials, API keys, bookmarks, and other sensitive
    information that agents may need to reference. Uses basic
    obfuscation (NOT encryption - use proper secrets management
    for production).

    Based on MIRIX (arXiv:2507.07957) knowledge vault component.
    """

    def __init__(self, db_path: Path, password: Optional[str] = None):
        """
        Initialize knowledge vault.

        Args:
            db_path: Path to SQLite database file.
            password: Optional encryption key (derivation input).
                      Defaults to VERTICE_VAULT_KEY env var.
        """
        self.db_path = db_path

        # SEC-004: Use strong key derivation with a deterministic salt.
        salt = self._get_machine_salt().encode()
        password = password or os.environ.get("VERTICE_VAULT_KEY", "default-dev-key")

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self._fernet = Fernet(key)
        self._init_db()

    def _get_machine_salt(self) -> str:
        """Get a machine-specific salt for obfuscation."""
        try:
            # Use username and home path as basic salt
            import os

            user = os.getenv("USER", os.getenv("USERNAME", "default"))
            home = str(Path.home())
            return hashlib.sha256(f"{user}:{home}".encode()).hexdigest()[:16]
        except (OSError, RuntimeError):
            return "vertice-default-salt"

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS vault (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    entry_type TEXT NOT NULL,
                    source TEXT,
                    sensitivity_level TEXT NOT NULL,
                    value_obfuscated TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT,
                    last_accessed TEXT
                )
            """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_vault_type ON vault(entry_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_vault_name ON vault(name)")

    def encrypt(self, value: str) -> str:
        """Encrypt value with AES-128-CBC (Fernet)."""
        return self._fernet.encrypt(value.encode()).decode()

    def decrypt(self, token: str) -> str:
        """Decrypt value, with fallback to legacy base64."""
        try:
            # Try new Fernet decryption first
            return self._fernet.decrypt(token.encode()).decode()
        except InvalidToken:
            # Fallback for old base64-encoded data
            logger.warning(
                "Vault entry is using legacy obfuscation. "
                "It will be auto-upgraded to new encryption on next save."
            )
            return self._deobfuscate_legacy(token)

    def _deobfuscate_legacy(self, obfuscated: str) -> str:
        """Deobfuscate a value using the old base64 method."""
        try:
            decoded = base64.b64decode(obfuscated.encode()).decode()
            # Remove salt prefix from old format
            if ":" in decoded:
                return decoded.split(":", 1)[1]
            return decoded
        except Exception as e:
            # If it fails, it's likely not base64. It might be an unencrypted value.
            return obfuscated

    # Keep old method names for backward compat
    _obfuscate = encrypt
    _deobfuscate = decrypt

    def store(
        self,
        name: str,
        value: str,
        entry_type: VaultEntryType,
        source: str = "user_provided",
        sensitivity_level: SensitivityLevel = SensitivityLevel.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store a secret in the vault.

        Args:
            name: Unique name for this entry.
            value: The secret value.
            entry_type: Type of entry.
            source: Where this came from.
            sensitivity_level: Security level.
            metadata: Additional context.

        Returns:
            ID of the stored entry.
        """
        entry_id = str(uuid.uuid4())
        obfuscated = self._obfuscate(value)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO vault
                   (id, name, entry_type, source, sensitivity_level,
                    value_obfuscated, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    entry_id,
                    name,
                    entry_type.value,
                    source,
                    sensitivity_level.value,
                    obfuscated,
                    json.dumps(metadata or {}),
                    datetime.now().isoformat(),
                ),
            )

        logger.info(f"Stored vault entry: {name} ({entry_type.value})")
        return entry_id

    def get(self, name: str) -> Optional[VaultEntry]:
        """
        Get a vault entry by name.

        Args:
            name: Name of the entry.

        Returns:
            VaultEntry if found, None otherwise.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM vault WHERE name = ?", (name,)).fetchone()

            if row:
                # Update access tracking
                conn.execute(
                    """UPDATE vault
                       SET last_accessed = ?
                       WHERE name = ?""",
                    (datetime.now().isoformat(), name),
                )
                return self._row_to_entry(row)
            return None

    def list_entries(
        self,
        entry_type: Optional[VaultEntryType] = None,
        include_values: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        List vault entries (values redacted by default).

        Args:
            entry_type: Optional type filter.
            include_values: Whether to include actual values.

        Returns:
            List of entry dictionaries.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if entry_type:
                rows = conn.execute(
                    "SELECT * FROM vault WHERE entry_type = ? ORDER BY name", (entry_type.value,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM vault ORDER BY name").fetchall()

            entries = [self._row_to_entry(row) for row in rows]
            return [e.to_dict(include_value=include_values) for e in entries]

    def delete(self, name: str) -> bool:
        """
        Delete a vault entry.

        Args:
            name: Name of the entry to delete.

        Returns:
            True if deleted, False if not found.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM vault WHERE name = ?", (name,))
            deleted = cursor.rowcount > 0

        if deleted:
            logger.info(f"Deleted vault entry: {name}")
        return deleted

    def exists(self, name: str) -> bool:
        """Check if an entry exists."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT 1 FROM vault WHERE name = ?", (name,)).fetchone()
            return row is not None

    def _row_to_entry(self, row: sqlite3.Row) -> VaultEntry:
        """Convert database row to VaultEntry object."""
        return VaultEntry(
            id=row["id"],
            name=row["name"],
            entry_type=VaultEntryType(row["entry_type"]),
            source=row["source"] or "unknown",
            sensitivity_level=SensitivityLevel(row["sensitivity_level"]),
            value=self._deobfuscate(row["value_obfuscated"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=row["created_at"],
            last_accessed=row["last_accessed"],
        )
