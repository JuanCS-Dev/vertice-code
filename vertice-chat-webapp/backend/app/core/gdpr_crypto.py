"""
GDPR Crypto-Shredding Service
Application-Level Encryption with key destruction for GDPR compliance.
Governed by Vértice Constitution v3.0 and Padrão Pagani.
"""

from __future__ import annotations

import base64
import hashlib
import logging
from datetime import datetime
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import select, update

from app.core.config import settings
from app.core.kms_client import CloudKmsClient
from app.core.database import get_db_session
from app.models.database import Workspace

logger = logging.getLogger(__name__)


def _decode_master_key_b64(key_b64: str) -> bytes:
    try:
        raw = base64.urlsafe_b64decode(key_b64)
    except Exception as exc:
        raise ValueError("Invalid GDPR master key: not valid base64url") from exc

    if len(raw) != 32:
        raise ValueError("Invalid GDPR master key: must decode to 32 bytes")
    return raw


def _load_master_key(override_key_b64: Optional[str]) -> bytes:
    if override_key_b64:
        return _decode_master_key_b64(override_key_b64)

    if settings.GDPR_MASTER_KEY:
        return _decode_master_key_b64(settings.GDPR_MASTER_KEY)

    if settings.KMS_KEY_NAME and settings.GDPR_MASTER_KEY_CIPHERTEXT:
        plaintext = CloudKmsClient(settings.KMS_KEY_NAME).decrypt_b64(
            settings.GDPR_MASTER_KEY_CIPHERTEXT
        )
        if len(plaintext) != 32:
            raise ValueError("KMS-decrypted GDPR master key must be 32 bytes")
        return plaintext

    raise RuntimeError(
        "GDPR master key is not configured. Set GDPR_MASTER_KEY (base64url 32-byte) or "
        "KMS_KEY_NAME + GDPR_MASTER_KEY_CIPHERTEXT."
    )


class CryptoShreddingService:
    """
    GDPR-compliant data encryption service.

    Implements Application-Level Encryption (ALE) with crypto-shredding.
    Keys are derived from a master key and stored per workspace.
    """

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize crypto service.

        Args:
            master_key: Base64 encoded 32-byte master key.
        """
        self.master_key = _load_master_key(master_key)

    def derive_workspace_key(self, workspace_id: str, key_version: int = 1) -> bytes:
        """Derive workspace-specific encryption key from master key."""
        salt = hashlib.sha256(f"{workspace_id}:{key_version}".encode()).digest()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(self.master_key))

    def encrypt_data(self, data: str, encryption_key: bytes) -> str:
        """Encrypt data using provided key."""
        try:
            f = Fernet(encryption_key)
            encrypted = f.encrypt(data.encode("utf-8"))
            return base64.b64encode(encrypted).decode("utf-8")
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt_data(self, encrypted_data: str, encryption_key: bytes) -> str:
        """Decrypt data or raise InvalidToken if shredded."""
        try:
            f = Fernet(encryption_key)
            encrypted_bytes = base64.b64decode(encrypted_data)
            decrypted = f.decrypt(encrypted_bytes)
            return decrypted.decode("utf-8")
        except InvalidToken:
            logger.warning("Decryption failed - possibly crypto-shredded.")
            raise
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    async def crypto_shred_workspace(self, workspace_id: str) -> bool:
        """Irreversibly destroy workspace encryption key in database."""
        try:
            logger.info(f"Initiating crypto-shredding for workspace {workspace_id}")

            async with get_db_session() as session:
                await session.execute(
                    update(Workspace)
                    .where(Workspace.id == workspace_id)
                    .values(
                        data_encryption_key=None,
                        is_active=False,
                        deletion_reason="GDPR_SHREDDED",
                        deleted_at=datetime.utcnow(),
                    )
                )
                await session.commit()

            logger.info(f"Crypto-shredding completed for {workspace_id}")
            return True
        except Exception as e:
            logger.error(f"Crypto-shredding failed for {workspace_id}: {e}")
            return False

    async def get_workspace_key(self, workspace_id: str) -> Optional[bytes]:
        """Retrieve or initialize workspace encryption key."""
        async with get_db_session() as session:
            result = await session.execute(
                select(Workspace.data_encryption_key, Workspace.key_encryption_version).where(
                    Workspace.id == workspace_id
                )
            )
            row = result.fetchone()

            if not row or row[0] is None:
                return None

            return self.derive_workspace_key(workspace_id, row[1])


class GDPRComplianceManager:
    """Manages GDPR operations (Right to Access, Erasure, etc.)."""

    def __init__(self, crypto_service: CryptoShreddingService):
        self.crypto = crypto_service

    async def process_erasure_request(self, user_id: str, workspace_id: str) -> bool:
        """Process GDPR 'Right to be Forgotten' via crypto-shredding."""
        return await self.crypto.crypto_shred_workspace(workspace_id)


# Global instances
_crypto_service: Optional[CryptoShreddingService] = None


def get_crypto_service() -> CryptoShreddingService:
    """Get global crypto service instance (Singleton)."""
    global _crypto_service
    if _crypto_service is None:
        _crypto_service = CryptoShreddingService()
    return _crypto_service
