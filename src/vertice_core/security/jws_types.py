"""
JWS Types and Utilities
=======================

Type definitions and utility functions for JWS (RFC 7515) implementation.

Reference:
- RFC 7515 (JWS): https://datatracker.ietf.org/doc/html/rfc7515
- RFC 8785 (JCS): https://datatracker.ietf.org/doc/html/rfc8785

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

try:
    import rfc8785

    HAS_RFC8785 = True
except ImportError:
    HAS_RFC8785 = False

logger = logging.getLogger(__name__)


# =============================================================================
# TYPES
# =============================================================================


class JWSAlgorithm(str, Enum):
    """Supported JWS algorithms per RFC 7518.

    Attributes:
        RS256: RSASSA-PKCS1-v1_5 with SHA-256
        RS384: RSASSA-PKCS1-v1_5 with SHA-384
        RS512: RSASSA-PKCS1-v1_5 with SHA-512
        ES256: ECDSA with P-256 and SHA-256
        ES384: ECDSA with P-384 and SHA-384
        ES512: ECDSA with P-521 and SHA-512
    """

    RS256 = "RS256"
    RS384 = "RS384"
    RS512 = "RS512"
    ES256 = "ES256"
    ES384 = "ES384"
    ES512 = "ES512"


@dataclass
class JWSHeader:
    """JWS Protected Header per RFC 7515 Section 4.1.

    Attributes:
        alg: Algorithm (required)
        typ: Type (typically "JWS")
        kid: Key ID
        jku: JWK Set URL for key retrieval
    """

    alg: JWSAlgorithm
    typ: str = "JWS"
    kid: Optional[str] = None
    jku: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result: Dict[str, Any] = {
            "alg": self.alg.value,
            "typ": self.typ,
        }
        if self.kid:
            result["kid"] = self.kid
        if self.jku:
            result["jku"] = self.jku
        return result


@dataclass
class JWSSignature:
    """JWS Signature object.

    Contains protected header and signature for Agent Card.

    Attributes:
        protected: Base64URL-encoded header
        signature: Base64URL-encoded signature
        jku: JWK Set URL (optional)
    """

    protected: str
    signature: str
    jku: Optional[str] = None


@dataclass
class KeyPair:
    """RSA/EC key pair for signing.

    Attributes:
        private_key: Private key bytes (PEM format)
        public_key: Public key bytes (PEM format)
        key_id: Unique key identifier
        algorithm: JWS algorithm
        created_at: Creation timestamp
    """

    private_key: bytes
    public_key: bytes
    key_id: str
    algorithm: JWSAlgorithm
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# UTILITIES
# =============================================================================


def base64url_encode(data: bytes) -> str:
    """Base64URL encode without padding (per RFC 7515).

    Args:
        data: Bytes to encode

    Returns:
        Base64URL-encoded string without padding
    """
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def base64url_decode(data: str) -> bytes:
    """Base64URL decode with padding restoration.

    Args:
        data: Base64URL-encoded string

    Returns:
        Decoded bytes
    """
    padding_needed = 4 - len(data) % 4
    if padding_needed != 4:
        data += "=" * padding_needed
    return base64.urlsafe_b64decode(data)


def canonicalize_json(data: Dict[str, Any]) -> bytes:
    """Canonicalize JSON per RFC 8785 (JCS).

    Args:
        data: Dictionary to canonicalize

    Returns:
        Canonical UTF-8 bytes

    Note:
        Falls back to simple deterministic JSON if rfc8785 not installed.
    """
    if HAS_RFC8785:
        return rfc8785.dumps(data)

    # Fallback: simple canonical JSON (deterministic key ordering)
    logger.warning(
        "rfc8785 not installed - using fallback canonicalization. "
        "Install with: pip install rfc8785"
    )
    return json.dumps(
        data,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=False,
    ).encode("utf-8")


__all__ = [
    "JWSAlgorithm",
    "JWSHeader",
    "JWSSignature",
    "KeyPair",
    "HAS_RFC8785",
    "base64url_encode",
    "base64url_decode",
    "canonicalize_json",
]
