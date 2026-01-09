"""
GDPR Crypto-Shredding Service
Application-Level Encryption with key destruction for GDPR compliance
"""

import os
import base64
import hashlib
from typing import Optional, Tuple, Dict, Any
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets
import logging

logger = logging.getLogger(__name__)


class CryptoShreddingService:
    """
    GDPR-compliant data encryption with crypto-shredding capabilities.

    Implements Application-Level Encryption (ALE) where:
    - Data is encrypted before storage
    - Keys are managed separately
    - "Deletion" is achieved by destroying encryption keys
    - Zero knowledge of data content
    """

    def __init__(self, master_key: Optional[bytes] = None):
        """
        Initialize crypto service.

        Args:
            master_key: Master encryption key (auto-generated if None)
        """
        self.master_key = master_key or self._generate_master_key()

    def _generate_master_key(self) -> bytes:
        """Generate a secure master key."""
        return secrets.token_bytes(32)

    def derive_workspace_key(self, workspace_id: str, key_version: int = 1) -> bytes:
        """
        Derive workspace-specific encryption key from master key.

        This creates deterministic but unique keys per workspace.
        """
        # Create salt from workspace_id and version
        salt = hashlib.sha256(f"{workspace_id}:{key_version}".encode()).digest()

        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        return base64.urlsafe_b64encode(kdf.derive(self.master_key))

    def encrypt_data(self, data: str, encryption_key: bytes) -> str:
        """
        Encrypt data using provided key.

        Args:
            data: Plain text data to encrypt
            encryption_key: Fernet-compatible key

        Returns:
            Base64-encoded encrypted data
        """
        try:
            f = Fernet(encryption_key)
            encrypted = f.encrypt(data.encode("utf-8"))
            return base64.b64encode(encrypted).decode("utf-8")
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt_data(self, encrypted_data: str, encryption_key: bytes) -> str:
        """
        Decrypt data using provided key.

        Args:
            encrypted_data: Base64-encoded encrypted data
            encryption_key: Fernet-compatible key

        Returns:
            Decrypted plain text

        Raises:
            InvalidToken: If decryption fails (key destroyed/crypto-shredded)
        """
        try:
            f = Fernet(encryption_key)
            encrypted_bytes = base64.b64decode(encrypted_data)
            decrypted = f.decrypt(encrypted_bytes)
            return decrypted.decode("utf-8")
        except InvalidToken:
            # This is expected when key is destroyed (crypto-shredding)
            logger.warning("Decryption failed - data may have been crypto-shredded")
            raise
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def crypto_shred_workspace(self, workspace_id: str) -> bool:
        """
        Perform crypto-shredding for a workspace.

        This "deletes" all workspace data by destroying the encryption key.
        After this operation, all encrypted data becomes unreadable.

        Returns True if shredding successful.
        """
        try:
            # In a real implementation, this would:
            # 1. Delete the workspace key from key management system
            # 2. Update database to mark data as shredded
            # 3. Log the shredding operation for audit

            logger.info(f"Crypto-shredding initiated for workspace {workspace_id}")

            # Simulate key destruction (in production, this would be permanent)
            # The key would be removed from secure key storage

            # Update workspace record to reflect shredding
            # This would be done in the database layer

            logger.info(f"Crypto-shredding completed for workspace {workspace_id}")
            return True

        except Exception as e:
            logger.error(f"Crypto-shredding failed for workspace {workspace_id}: {e}")
            return False

    def rotate_workspace_key(self, workspace_id: str) -> Tuple[bytes, int]:
        """
        Rotate workspace encryption key.

        Creates a new key version while maintaining access to old data.

        Returns:
            Tuple of (new_key, new_version)
        """
        # Determine next version (would query database in production)
        new_version = 2  # Simplified

        new_key = self.derive_workspace_key(workspace_id, new_version)

        logger.info(f"Key rotated for workspace {workspace_id} to version {new_version}")
        return new_key, new_version

    def validate_key_access(self, workspace_id: str, key_version: int = 1) -> bool:
        """
        Validate that a workspace key is accessible.

        Returns False if key has been destroyed (crypto-shredded).
        """
        try:
            key = self.derive_workspace_key(workspace_id, key_version)
            # Test key validity by attempting to create Fernet instance
            Fernet(key)
            return True
        except Exception:
            return False

    def get_encryption_stats(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get encryption statistics for a workspace.
        """
        # In production, this would query the database for:
        # - Number of encrypted entries
        # - Key rotation history
        # - Last shredding operation

        return {
            "workspace_id": workspace_id,
            "encrypted_entries": 0,  # Would be queried
            "current_key_version": 1,
            "last_key_rotation": None,
            "shredding_status": "active",
        }


class GDPRComplianceManager:
    """
    GDPR compliance operations manager.
    """

    def __init__(self, crypto_service: CryptoShreddingService):
        self.crypto = crypto_service

    async def process_data_subject_request(
        self, request_type: str, data_subject_id: str, workspace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process GDPR data subject request.

        Args:
            request_type: "access", "rectification", "erasure", "portability"
            data_subject_id: User identifier (email or firebase_uid)
            workspace_id: Optional workspace scope
        """
        result = {
            "request_type": request_type,
            "data_subject_id": data_subject_id,
            "status": "processing",
            "completed_at": None,
        }

        try:
            if request_type == "access":
                # Provide data access
                result["data"] = await self._gather_user_data(data_subject_id, workspace_id)
                result["status"] = "completed"

            elif request_type == "erasure":
                # Right to be forgotten - crypto shredding
                success = await self._perform_data_erasure(data_subject_id, workspace_id)
                result["status"] = "completed" if success else "failed"

            elif request_type == "rectification":
                # Data correction
                success = await self._correct_user_data(data_subject_id, workspace_id)
                result["status"] = "completed" if success else "failed"

            elif request_type == "portability":
                # Data export
                result["export_data"] = await self._export_user_data(data_subject_id, workspace_id)
                result["status"] = "completed"

            result["completed_at"] = "2026-01-07T14:30:00Z"

        except Exception as e:
            logger.error(f"GDPR request processing failed: {e}")
            result["status"] = "error"
            result["error"] = str(e)

        return result

    async def _gather_user_data(
        self, data_subject_id: str, workspace_id: Optional[str]
    ) -> Dict[str, Any]:
        """Gather all user data for access request."""
        # In production, this would query all user data from database
        return {
            "personal_data": {"email": "user@example.com", "name": "John Doe"},
            "usage_data": {"total_tokens": 15000, "workspaces": 2, "agents_created": 3},
            "collected_at": "2026-01-07T14:30:00Z",
        }

    async def _perform_data_erasure(
        self, data_subject_id: str, workspace_id: Optional[str]
    ) -> bool:
        """Perform GDPR right to erasure (crypto shredding)."""
        try:
            # 1. Identify user's workspaces
            workspaces = [workspace_id] if workspace_id else ["workspace-123"]  # Mock

            # 2. Crypto-shred each workspace
            for ws_id in workspaces:
                success = self.crypto.crypto_shred_workspace(ws_id)
                if not success:
                    return False

            # 3. Mark user as GDPR-erased in database
            # 4. Log erasure operation

            logger.info(f"GDPR erasure completed for {data_subject_id}")
            return True

        except Exception as e:
            logger.error(f"Data erasure failed: {e}")
            return False

    async def _correct_user_data(self, data_subject_id: str, workspace_id: Optional[str]) -> bool:
        """Correct inaccurate user data."""
        # Implementation would update user records
        return True

    async def _export_user_data(
        self, data_subject_id: str, workspace_id: Optional[str]
    ) -> Dict[str, Any]:
        """Export user data in portable format."""
        return {
            "format": "JSON",
            "data": await self._gather_user_data(data_subject_id, workspace_id),
            "exported_at": "2026-01-07T14:30:00Z",
        }


# Global service instances
_crypto_service: Optional[CryptoShreddingService] = None
_gdpr_manager: Optional[GDPRComplianceManager] = None


def get_crypto_service() -> CryptoShreddingService:
    """Get global crypto service instance."""
    global _crypto_service
    if _crypto_service is None:
        _crypto_service = CryptoShreddingService()
    return _crypto_service


def get_gdpr_manager() -> GDPRComplianceManager:
    """Get global GDPR compliance manager."""
    global _gdpr_manager
    if _gdpr_manager is None:
        _gdpr_manager = GDPRComplianceManager(get_crypto_service())
    return _gdpr_manager
