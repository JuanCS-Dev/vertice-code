"""
Privacy Crypto Service for Field-Level Encryption.

Integrates with existing DataProtectionService from vertice_core
and adds Google Cloud KMS support for key management.

Features:
- AES-256-GCM encryption for sensitive fields
- Key derivation with PBKDF2
- Optional Cloud KMS integration
- Field-level encryption/decryption helpers
"""

from __future__ import annotations

import base64
import logging
import os
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

# Try to import from vertice_core
try:
    from vertice_core.tui.core.data_protection import (
        get_data_protection,
    )

    VERTICE_CRYPTO_AVAILABLE = True
except ImportError:
    VERTICE_CRYPTO_AVAILABLE = False
    logger.warning("vertice_core.data_protection not available")

# Cloud KMS integration
try:
    from google.cloud import kms

    KMS_AVAILABLE = True
except ImportError:
    KMS_AVAILABLE = False


class PrivacyCryptoService:
    """
    Privacy-focused encryption service.

    Extends DataProtectionService with:
    - Cloud KMS key management (optional)
    - Field-specific encryption
    - Audit logging for crypto operations
    """

    SENSITIVE_FIELDS = [
        "prompt",
        "final_text",
        "artifacts",
        "api_key",
        "password",
        "secret",
        "token",
        "email",
        "phone",
        "address",
    ]

    def __init__(
        self,
        project_id: str = "vertice-ai",
        location: str = "global",
        keyring: str = "vertice-keys",
        key_name: str = "data-encryption-key",
        use_kms: bool = False,
    ):
        """
        Initialize privacy crypto service.

        Args:
            project_id: GCP project ID
            location: KMS location
            keyring: KMS keyring name
            key_name: KMS key name
            use_kms: Whether to use Cloud KMS (requires setup)
        """
        self.project_id = project_id
        self.location = location
        self.keyring = keyring
        self.key_name = key_name
        self.use_kms = use_kms and KMS_AVAILABLE

        # Initialize base crypto service
        if VERTICE_CRYPTO_AVAILABLE:
            self._base_service = get_data_protection()
        else:
            self._base_service = None
            logger.warning("Using fallback encryption (no vertice_core)")

        # Initialize KMS client if needed
        self._kms_client: Optional[Any] = None
        if self.use_kms:
            try:
                self._kms_client = kms.KeyManagementServiceClient()
                self._key_path = self._kms_client.crypto_key_path(
                    project_id, location, keyring, key_name
                )
                logger.info(f"Cloud KMS initialized: {self._key_path}")
            except Exception as e:
                logger.error(f"Failed to initialize Cloud KMS: {e}")
                self.use_kms = False

        self._operations_count = 0

    def encrypt(self, data: Union[str, bytes, Dict[str, Any]]) -> str:
        """
        Encrypt data.

        Args:
            data: Data to encrypt (string, bytes, or dict)

        Returns:
            Base64-encoded encrypted data
        """
        self._operations_count += 1

        if self.use_kms and self._kms_client:
            return self._encrypt_with_kms(data)
        elif self._base_service:
            return self._base_service.encrypt_sensitive_data(data)
        else:
            return self._fallback_encrypt(data)

    def decrypt(self, encrypted_data: str) -> Any:
        """
        Decrypt data.

        Args:
            encrypted_data: Base64-encoded encrypted data

        Returns:
            Decrypted data
        """
        self._operations_count += 1

        if self.use_kms and self._kms_client:
            return self._decrypt_with_kms(encrypted_data)
        elif self._base_service:
            return self._base_service.decrypt_sensitive_data(encrypted_data)
        else:
            return self._fallback_decrypt(encrypted_data)

    def encrypt_fields(
        self,
        data: Dict[str, Any],
        fields: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Encrypt specific fields in a dictionary.

        Args:
            data: Dictionary with fields to encrypt
            fields: List of field names to encrypt (defaults to SENSITIVE_FIELDS)

        Returns:
            Dictionary with specified fields encrypted
        """
        fields = fields or self.SENSITIVE_FIELDS
        result = data.copy()

        for key, value in data.items():
            if any(field in key.lower() for field in fields):
                if value is not None and value != "":
                    result[key] = self.encrypt(value)
                    result[f"{key}_encrypted"] = True

        return result

    def decrypt_fields(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Decrypt fields that were encrypted by encrypt_fields.

        Args:
            data: Dictionary with encrypted fields

        Returns:
            Dictionary with fields decrypted
        """
        result = data.copy()

        for key, value in list(data.items()):
            if key.endswith("_encrypted") and value is True:
                field_name = key[:-10]  # Remove "_encrypted" suffix
                if field_name in result:
                    try:
                        result[field_name] = self.decrypt(result[field_name])
                    except Exception as e:
                        logger.error(f"Failed to decrypt field {field_name}: {e}")
                del result[key]

        return result

    def _encrypt_with_kms(self, data: Union[str, bytes, Dict[str, Any]]) -> str:
        """Encrypt using Cloud KMS."""
        import json

        if isinstance(data, dict):
            plaintext = json.dumps(data).encode("utf-8")
        elif isinstance(data, str):
            plaintext = data.encode("utf-8")
        else:
            plaintext = data

        response = self._kms_client.encrypt(
            request={"name": self._key_path, "plaintext": plaintext}
        )
        return base64.b64encode(response.ciphertext).decode("utf-8")

    def _decrypt_with_kms(self, encrypted_data: str) -> Any:
        """Decrypt using Cloud KMS."""
        import json

        ciphertext = base64.b64decode(encrypted_data)
        response = self._kms_client.decrypt(
            request={"name": self._key_path, "ciphertext": ciphertext}
        )
        plaintext = response.plaintext.decode("utf-8")

        try:
            return json.loads(plaintext)
        except json.JSONDecodeError:
            return plaintext

    def _fallback_encrypt(self, data: Union[str, bytes, Dict[str, Any]]) -> str:
        """Fallback encryption when no crypto service available."""
        import json

        if isinstance(data, dict):
            plaintext = json.dumps(data)
        elif isinstance(data, bytes):
            plaintext = data.decode("utf-8")
        else:
            plaintext = data

        # Simple base64 encoding (NOT SECURE - only for development)
        logger.warning("Using fallback base64 encoding - NOT SECURE FOR PRODUCTION")
        return base64.b64encode(plaintext.encode("utf-8")).decode("utf-8")

    def _fallback_decrypt(self, encrypted_data: str) -> Any:
        """Fallback decryption."""
        import json

        plaintext = base64.b64decode(encrypted_data).decode("utf-8")
        try:
            return json.loads(plaintext)
        except json.JSONDecodeError:
            return plaintext

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "operations_count": self._operations_count,
            "kms_enabled": self.use_kms,
            "vertice_crypto_available": VERTICE_CRYPTO_AVAILABLE,
            "kms_available": KMS_AVAILABLE,
        }


# Global instance
_crypto_service: Optional[PrivacyCryptoService] = None


def get_crypto_service() -> PrivacyCryptoService:
    """Get global crypto service instance."""
    global _crypto_service
    if _crypto_service is None:
        _crypto_service = PrivacyCryptoService(
            use_kms=os.getenv("VERTICE_USE_KMS", "false").lower() == "true"
        )
    return _crypto_service


def encrypt_field(value: Any) -> str:
    """Convenience function to encrypt a single value."""
    return get_crypto_service().encrypt(value)


def decrypt_field(encrypted_value: str) -> Any:
    """Convenience function to decrypt a single value."""
    return get_crypto_service().decrypt(encrypted_value)
