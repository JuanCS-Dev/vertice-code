"""
PKCE (Proof Key for Code Exchange) Implementation.
===================================================

Implements RFC 7636 PKCE with S256 (SHA-256) method.
Required by MCP 2025-11-25 and OAuth 2.1.

Security Requirements (MCP Spec):
- MUST use S256 code challenge method
- MUST verify code_challenge_methods_supported includes S256
- code_verifier: 43-128 characters from unreserved set
- code_challenge: BASE64URL(SHA256(code_verifier))

References:
- RFC 7636: https://datatracker.ietf.org/doc/html/rfc7636
- MCP Auth: https://modelcontextprotocol.io/specification/draft/basic/authorization

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from typing import Literal


# RFC 7636: Unreserved characters for code_verifier
# [A-Z] / [a-z] / [0-9] / "-" / "." / "_" / "~"
UNRESERVED_CHARS = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)

# RFC 7636: code_verifier length constraints
MIN_VERIFIER_LENGTH = 43
MAX_VERIFIER_LENGTH = 128
DEFAULT_VERIFIER_LENGTH = 64


@dataclass(frozen=True)
class PKCEChallenge:
    """PKCE challenge pair for OAuth 2.1 authorization.

    Attributes:
        code_verifier: Secret random string (43-128 chars)
        code_challenge: BASE64URL(SHA256(code_verifier))
        code_challenge_method: Always "S256" per MCP spec
    """

    code_verifier: str
    code_challenge: str
    code_challenge_method: Literal["S256"] = "S256"

    def to_auth_params(self) -> dict[str, str]:
        """Get parameters for authorization request.

        Returns:
            Dict with code_challenge and code_challenge_method
        """
        return {
            "code_challenge": self.code_challenge,
            "code_challenge_method": self.code_challenge_method,
        }

    def to_token_params(self) -> dict[str, str]:
        """Get parameters for token request.

        Returns:
            Dict with code_verifier
        """
        return {"code_verifier": self.code_verifier}


def _generate_code_verifier(length: int = DEFAULT_VERIFIER_LENGTH) -> str:
    """Generate cryptographically secure code_verifier.

    Args:
        length: Length of verifier (43-128, default 64)

    Returns:
        Random string from unreserved character set

    Raises:
        ValueError: If length is outside valid range
    """
    if not MIN_VERIFIER_LENGTH <= length <= MAX_VERIFIER_LENGTH:
        raise ValueError(
            f"code_verifier length must be {MIN_VERIFIER_LENGTH}-{MAX_VERIFIER_LENGTH}, "
            f"got {length}"
        )

    return "".join(secrets.choice(UNRESERVED_CHARS) for _ in range(length))


def _generate_code_challenge(code_verifier: str) -> str:
    """Generate S256 code_challenge from code_verifier.

    Implements: BASE64URL(SHA256(ASCII(code_verifier)))

    Args:
        code_verifier: The secret verifier string

    Returns:
        Base64URL-encoded SHA-256 hash (no padding)
    """
    # SHA-256 hash of ASCII-encoded verifier
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()

    # Base64URL encode without padding (RFC 7636 Appendix B)
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    return challenge


def generate_pkce(length: int = DEFAULT_VERIFIER_LENGTH) -> PKCEChallenge:
    """Generate complete PKCE challenge pair.

    Creates a cryptographically secure code_verifier and
    corresponding S256 code_challenge for OAuth 2.1 flows.

    Args:
        length: Length of code_verifier (43-128, default 64)

    Returns:
        PKCEChallenge with verifier and challenge

    Example:
        >>> pkce = generate_pkce()
        >>> # Add to authorization request
        >>> auth_url = f"{auth_endpoint}?{urlencode(pkce.to_auth_params())}"
        >>> # Add to token request
        >>> token_data = {"code": auth_code, **pkce.to_token_params()}
    """
    code_verifier = _generate_code_verifier(length)
    code_challenge = _generate_code_challenge(code_verifier)

    return PKCEChallenge(
        code_verifier=code_verifier,
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )


def verify_pkce(code_verifier: str, code_challenge: str) -> bool:
    """Verify PKCE challenge against verifier (server-side).

    Used by authorization servers to validate token requests.

    Args:
        code_verifier: The original verifier from token request
        code_challenge: The challenge from authorization request

    Returns:
        True if verification passes
    """
    expected_challenge = _generate_code_challenge(code_verifier)
    return secrets.compare_digest(expected_challenge, code_challenge)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "PKCEChallenge",
    "generate_pkce",
    "verify_pkce",
    "MIN_VERIFIER_LENGTH",
    "MAX_VERIFIER_LENGTH",
]
