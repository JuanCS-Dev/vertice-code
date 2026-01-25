from __future__ import annotations

import base64
from typing import Any, Optional


class CloudKmsClient:
    """Small wrapper around Google Cloud KMS encrypt/decrypt for backend use."""

    def __init__(self, key_name: str, *, client: Optional[Any] = None) -> None:
        self.key_name = key_name
        self._client = client or self._default_client()

    @staticmethod
    def _default_client() -> Any:
        try:
            from google.cloud import kms  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "google-cloud-kms is required for KMS integration. "
                "Install it in the backend environment."
            ) from exc
        return kms.KeyManagementServiceClient()

    def encrypt(self, plaintext: bytes) -> bytes:
        resp = self._client.encrypt(request={"name": self.key_name, "plaintext": plaintext})
        return resp.ciphertext

    def decrypt(self, ciphertext: bytes) -> bytes:
        resp = self._client.decrypt(request={"name": self.key_name, "ciphertext": ciphertext})
        return resp.plaintext

    def encrypt_b64(self, plaintext: bytes) -> str:
        return base64.b64encode(self.encrypt(plaintext)).decode("utf-8")

    def decrypt_b64(self, ciphertext_b64: str) -> bytes:
        return self.decrypt(base64.b64decode(ciphertext_b64))
