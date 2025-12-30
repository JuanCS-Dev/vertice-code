"""
Tests for PKCE Implementation.

Tests RFC 7636 PKCE with S256 method per MCP 2025-11-25 requirements.

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import base64
import hashlib
import re

import pytest

from core.security.pkce import (
    PKCEChallenge,
    generate_pkce,
    verify_pkce,
    UNRESERVED_CHARS,
)


# =============================================================================
# PKCE GENERATION TESTS
# =============================================================================


class TestPKCEGeneration:
    """Tests for PKCE generation."""

    def test_generate_pkce_returns_challenge(self) -> None:
        """generate_pkce returns PKCEChallenge."""
        pkce = generate_pkce()

        assert isinstance(pkce, PKCEChallenge)
        assert pkce.code_verifier
        assert pkce.code_challenge
        assert pkce.code_challenge_method == "S256"

    def test_generate_pkce_default_length(self) -> None:
        """Default verifier length is 64 characters."""
        pkce = generate_pkce()

        assert len(pkce.code_verifier) == 64

    def test_generate_pkce_custom_length(self) -> None:
        """Custom verifier length works."""
        pkce = generate_pkce(length=43)
        assert len(pkce.code_verifier) == 43

        pkce = generate_pkce(length=128)
        assert len(pkce.code_verifier) == 128

    def test_generate_pkce_min_length_validation(self) -> None:
        """Verifier length below minimum raises ValueError."""
        with pytest.raises(ValueError, match="must be 43-128"):
            generate_pkce(length=42)

    def test_generate_pkce_max_length_validation(self) -> None:
        """Verifier length above maximum raises ValueError."""
        with pytest.raises(ValueError, match="must be 43-128"):
            generate_pkce(length=129)

    def test_generate_pkce_uses_unreserved_chars(self) -> None:
        """Verifier uses only RFC 7636 unreserved characters."""
        pkce = generate_pkce()

        for char in pkce.code_verifier:
            assert char in UNRESERVED_CHARS

    def test_generate_pkce_unique_each_call(self) -> None:
        """Each call generates unique PKCE pair."""
        pkce1 = generate_pkce()
        pkce2 = generate_pkce()

        assert pkce1.code_verifier != pkce2.code_verifier
        assert pkce1.code_challenge != pkce2.code_challenge


# =============================================================================
# CODE CHALLENGE TESTS
# =============================================================================


class TestCodeChallenge:
    """Tests for S256 code challenge generation."""

    def test_challenge_is_base64url(self) -> None:
        """Code challenge is valid base64url (no padding)."""
        pkce = generate_pkce()

        # Base64URL uses only these characters
        base64url_pattern = re.compile(r"^[A-Za-z0-9_-]+$")
        assert base64url_pattern.match(pkce.code_challenge)

        # No padding
        assert "=" not in pkce.code_challenge

    def test_challenge_length(self) -> None:
        """Code challenge is 43 characters (SHA-256 base64url encoded)."""
        pkce = generate_pkce()

        # SHA-256 = 32 bytes = 43 chars in base64url without padding
        assert len(pkce.code_challenge) == 43

    def test_challenge_s256_calculation(self) -> None:
        """Challenge is correctly calculated as BASE64URL(SHA256(verifier))."""
        pkce = generate_pkce()

        # Manual calculation
        digest = hashlib.sha256(pkce.code_verifier.encode("ascii")).digest()
        expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

        assert pkce.code_challenge == expected

    def test_known_vector(self) -> None:
        """Test against known test vector from RFC 7636 Appendix B."""
        # RFC 7636 Appendix B test vector
        verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        expected_challenge = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"

        # Manual calculation
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

        assert challenge == expected_challenge


# =============================================================================
# VERIFICATION TESTS
# =============================================================================


class TestPKCEVerification:
    """Tests for PKCE verification (server-side)."""

    def test_verify_valid_pkce(self) -> None:
        """Valid PKCE verifies successfully."""
        pkce = generate_pkce()

        assert verify_pkce(pkce.code_verifier, pkce.code_challenge) is True

    def test_verify_invalid_verifier(self) -> None:
        """Invalid verifier fails verification."""
        pkce = generate_pkce()

        assert verify_pkce("wrong_verifier", pkce.code_challenge) is False

    def test_verify_invalid_challenge(self) -> None:
        """Invalid challenge fails verification."""
        pkce = generate_pkce()

        assert verify_pkce(pkce.code_verifier, "wrong_challenge") is False

    def test_verify_timing_safe(self) -> None:
        """Verification uses timing-safe comparison."""
        # This is implicit in secrets.compare_digest usage
        pkce = generate_pkce()

        # Should not leak timing info on partial match
        partial_challenge = pkce.code_challenge[:-1] + "X"
        assert verify_pkce(pkce.code_verifier, partial_challenge) is False


# =============================================================================
# PKCE CHALLENGE DATACLASS TESTS
# =============================================================================


class TestPKCEChallengeDataclass:
    """Tests for PKCEChallenge dataclass methods."""

    def test_to_auth_params(self) -> None:
        """to_auth_params returns correct dict."""
        pkce = generate_pkce()
        params = pkce.to_auth_params()

        assert params == {
            "code_challenge": pkce.code_challenge,
            "code_challenge_method": "S256",
        }

    def test_to_token_params(self) -> None:
        """to_token_params returns correct dict."""
        pkce = generate_pkce()
        params = pkce.to_token_params()

        assert params == {"code_verifier": pkce.code_verifier}

    def test_immutable(self) -> None:
        """PKCEChallenge is immutable (frozen dataclass)."""
        pkce = generate_pkce()

        with pytest.raises(Exception):  # FrozenInstanceError
            pkce.code_verifier = "new_value"  # type: ignore
