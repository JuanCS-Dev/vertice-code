import pytest
import base64
from app.core.gdpr_crypto import CryptoShreddingService
from cryptography.fernet import InvalidToken


class TestCryptoShredding:
    """Test suite for GDPR Crypto-Shredding Service."""

    @pytest.fixture
    def crypto_service(self):
        # 32-byte base64 encoded key
        master_key = base64.urlsafe_b64encode(b"01234567890123456789012345678901").decode()
        return CryptoShreddingService(master_key=master_key)

    def test_encryption_decryption_success(self, crypto_service):
        """Test basic ALE flow."""
        workspace_id = "test-workspace-123"
        key = crypto_service.derive_workspace_key(workspace_id)
        original_data = "Sensible User Information"

        encrypted = crypto_service.encrypt_data(original_data, key)
        decrypted = crypto_service.decrypt_data(encrypted, key)

        assert encrypted != original_data
        assert decrypted == original_data

    def test_shredding_simulation(self, crypto_service):
        """Test that wrong key (or shredded state) prevents decryption."""
        workspace_id = "test-workspace-123"
        key = crypto_service.derive_workspace_key(workspace_id)
        encrypted = crypto_service.encrypt_data("Secret", key)

        # Simulating a shredded or wrong key
        wrong_key = crypto_service.derive_workspace_key("another-id")

        with pytest.raises(InvalidToken):
            crypto_service.decrypt_data(encrypted, wrong_key)

    def test_key_derivation_is_deterministic(self, crypto_service):
        """Test that same workspace always gets same key."""
        workspace_id = "ws-789"
        key1 = crypto_service.derive_workspace_key(workspace_id)
        key2 = crypto_service.derive_workspace_key(workspace_id)

        assert key1 == key2


def test_crypto_service_requires_key_configuration(monkeypatch):
    from app.core import gdpr_crypto

    monkeypatch.setattr(gdpr_crypto.settings, "GDPR_MASTER_KEY", None, raising=False)
    monkeypatch.setattr(gdpr_crypto.settings, "KMS_KEY_NAME", None, raising=False)
    monkeypatch.setattr(gdpr_crypto.settings, "GDPR_MASTER_KEY_CIPHERTEXT", None, raising=False)

    with pytest.raises(RuntimeError, match="GDPR master key is not configured"):
        gdpr_crypto.CryptoShreddingService(master_key=None)


def test_crypto_service_can_load_master_key_from_kms(monkeypatch):
    from app.core import gdpr_crypto

    class _FakeResp:
        def __init__(self, plaintext: bytes):
            self.plaintext = plaintext

    class _FakeKms:
        def decrypt(self, request):
            assert request["name"] == "projects/p/locations/l/keyRings/r/cryptoKeys/k"
            assert request["ciphertext"] == b"ciphertext"
            return _FakeResp(b"01234567890123456789012345678901")

    class _FakeCloudKmsClient:
        def __init__(self, key_name: str):
            self._inner = _FakeKms()
            self.key_name = key_name

        def decrypt_b64(self, ciphertext_b64: str) -> bytes:
            assert ciphertext_b64 == base64.b64encode(b"ciphertext").decode("utf-8")
            return self._inner.decrypt(
                {"name": self.key_name, "ciphertext": base64.b64decode(ciphertext_b64)}
            ).plaintext

    monkeypatch.setattr(gdpr_crypto.settings, "GDPR_MASTER_KEY", None, raising=False)
    monkeypatch.setattr(
        gdpr_crypto.settings,
        "KMS_KEY_NAME",
        "projects/p/locations/l/keyRings/r/cryptoKeys/k",
        raising=False,
    )
    monkeypatch.setattr(
        gdpr_crypto.settings,
        "GDPR_MASTER_KEY_CIPHERTEXT",
        base64.b64encode(b"ciphertext").decode("utf-8"),
        raising=False,
    )
    monkeypatch.setattr(gdpr_crypto, "CloudKmsClient", _FakeCloudKmsClient)

    svc = gdpr_crypto.CryptoShreddingService(master_key=None)
    assert svc.master_key == b"01234567890123456789012345678901"
