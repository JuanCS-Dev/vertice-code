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
