"""
JWS Signer for Agent Cards
==========================

JSON Web Signature (RFC 7515) implementation for A2A Agent Card authentication.

Features:
- JCS canonicalization (RFC 8785) before signing
- RS256/ES256/EdDSA algorithm support
- Key pair generation and management
- Signature verification

Reference:
- RFC 7515 (JWS): https://datatracker.ietf.org/doc/html/rfc7515
- RFC 8785 (JCS): https://datatracker.ietf.org/doc/html/rfc8785
- A2A Spec: https://a2a-protocol.org/latest/specification/

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import base64
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import rfc8785
    HAS_RFC8785 = True
except ImportError:
    HAS_RFC8785 = False

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding
    from cryptography.hazmat.backends import default_backend
    from cryptography.exceptions import InvalidSignature
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

logger = logging.getLogger(__name__)


# =============================================================================
# TYPES
# =============================================================================


class JWSAlgorithm(str, Enum):
    """Supported JWS algorithms per RFC 7518."""

    RS256 = "RS256"  # RSASSA-PKCS1-v1_5 with SHA-256
    RS384 = "RS384"  # RSASSA-PKCS1-v1_5 with SHA-384
    RS512 = "RS512"  # RSASSA-PKCS1-v1_5 with SHA-512
    ES256 = "ES256"  # ECDSA with P-256 and SHA-256
    ES384 = "ES384"  # ECDSA with P-384 and SHA-384
    ES512 = "ES512"  # ECDSA with P-521 and SHA-512


@dataclass
class JWSHeader:
    """JWS Protected Header.

    Per RFC 7515 Section 4.1.

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
    """

    protected: str  # Base64URL-encoded header
    signature: str  # Base64URL-encoded signature
    jku: Optional[str] = None  # JWK Set URL


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
    """Base64URL encode without padding (per RFC 7515)."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def base64url_decode(data: str) -> bytes:
    """Base64URL decode with padding restoration."""
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

    Raises:
        RuntimeError: If rfc8785 not installed
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


# =============================================================================
# KEY MANAGEMENT
# =============================================================================


class KeyManager:
    """Key pair generation and management.

    Generates RSA-2048 or EC P-256 key pairs for JWS signing.
    Keys are stored in PEM format.
    """

    @staticmethod
    def generate_rsa_keypair(
        key_size: int = 2048,
        key_id: Optional[str] = None,
    ) -> KeyPair:
        """Generate RSA key pair.

        Args:
            key_size: RSA key size (2048, 3072, or 4096)
            key_id: Optional key identifier

        Returns:
            KeyPair with RSA keys
        """
        if not HAS_CRYPTOGRAPHY:
            raise RuntimeError(
                "cryptography not installed. Install with: pip install cryptography"
            )

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend(),
        )

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        # Generate key ID if not provided
        if not key_id:
            key_id = f"rsa-{secrets.token_hex(8)}"

        # Determine algorithm based on key size
        algorithm = JWSAlgorithm.RS256

        return KeyPair(
            private_key=private_pem,
            public_key=public_pem,
            key_id=key_id,
            algorithm=algorithm,
        )

    @staticmethod
    def generate_ec_keypair(
        curve: str = "P-256",
        key_id: Optional[str] = None,
    ) -> KeyPair:
        """Generate EC key pair.

        Args:
            curve: EC curve (P-256, P-384, or P-521)
            key_id: Optional key identifier

        Returns:
            KeyPair with EC keys
        """
        if not HAS_CRYPTOGRAPHY:
            raise RuntimeError(
                "cryptography not installed. Install with: pip install cryptography"
            )

        curves = {
            "P-256": (ec.SECP256R1(), JWSAlgorithm.ES256),
            "P-384": (ec.SECP384R1(), JWSAlgorithm.ES384),
            "P-521": (ec.SECP521R1(), JWSAlgorithm.ES512),
        }

        if curve not in curves:
            raise ValueError(f"Unsupported curve: {curve}. Use: {list(curves.keys())}")

        ec_curve, algorithm = curves[curve]
        private_key = ec.generate_private_key(ec_curve, default_backend())

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        if not key_id:
            key_id = f"ec-{secrets.token_hex(8)}"

        return KeyPair(
            private_key=private_pem,
            public_key=public_pem,
            key_id=key_id,
            algorithm=algorithm,
        )


# =============================================================================
# JWS SIGNER
# =============================================================================


class JWSSigner:
    """JWS Signer for Agent Cards.

    Signs Agent Cards using JWS (RFC 7515) with JCS canonicalization (RFC 8785).

    Example:
        signer = JWSSigner(keypair)
        signature = signer.sign_agent_card(agent_card_dict)
        is_valid = signer.verify_signature(agent_card_dict, signature)
    """

    def __init__(
        self,
        keypair: KeyPair,
        jku: Optional[str] = None,
    ) -> None:
        """Initialize JWS signer.

        Args:
            keypair: Key pair for signing
            jku: JWK Set URL for key retrieval
        """
        if not HAS_CRYPTOGRAPHY:
            raise RuntimeError(
                "cryptography not installed. Install with: pip install cryptography"
            )

        self._keypair = keypair
        self._jku = jku

        # Load keys
        self._private_key = serialization.load_pem_private_key(
            keypair.private_key,
            password=None,
            backend=default_backend(),
        )
        self._public_key = serialization.load_pem_public_key(
            keypair.public_key,
            backend=default_backend(),
        )

    def sign_agent_card(
        self,
        agent_card: Dict[str, Any],
    ) -> JWSSignature:
        """Sign an Agent Card.

        Per A2A spec:
        1. Remove 'signatures' field from card
        2. Remove properties with default values
        3. Canonicalize with RFC 8785
        4. Sign with JWS

        Args:
            agent_card: Agent Card dictionary

        Returns:
            JWSSignature object
        """
        # Step 1: Prepare payload (remove signatures)
        payload = {k: v for k, v in agent_card.items() if k != "signatures"}

        # Step 2: Remove empty/default values
        payload = self._remove_defaults(payload)

        # Step 3: Canonicalize
        canonical = canonicalize_json(payload)

        # Step 4: Create protected header
        header = JWSHeader(
            alg=self._keypair.algorithm,
            typ="JWS",
            kid=self._keypair.key_id,
            jku=self._jku,
        )
        protected = base64url_encode(
            json.dumps(header.to_dict()).encode("utf-8")
        )

        # Step 5: Create signing input
        signing_input = f"{protected}.{base64url_encode(canonical)}".encode("ascii")

        # Step 6: Sign
        signature = self._sign(signing_input)

        return JWSSignature(
            protected=protected,
            signature=base64url_encode(signature),
            jku=self._jku,
        )

    def verify_signature(
        self,
        agent_card: Dict[str, Any],
        signature: JWSSignature,
        public_key: Optional[bytes] = None,
    ) -> bool:
        """Verify an Agent Card signature.

        Args:
            agent_card: Agent Card dictionary (with or without signatures)
            signature: JWSSignature to verify
            public_key: Optional public key (uses own key if not provided)

        Returns:
            True if signature is valid
        """
        try:
            # Prepare payload
            payload = {k: v for k, v in agent_card.items() if k != "signatures"}
            payload = self._remove_defaults(payload)
            canonical = canonicalize_json(payload)

            # Reconstruct signing input
            signing_input = (
                f"{signature.protected}.{base64url_encode(canonical)}".encode("ascii")
            )

            # Decode signature
            sig_bytes = base64url_decode(signature.signature)

            # Verify
            if public_key:
                verifier_key = serialization.load_pem_public_key(
                    public_key,
                    backend=default_backend(),
                )
            else:
                verifier_key = self._public_key

            return self._verify(signing_input, sig_bytes, verifier_key)

        except Exception as e:
            logger.warning(f"Signature verification failed: {e}")
            return False

    def _sign(self, data: bytes) -> bytes:
        """Sign data with private key."""
        algorithm = self._keypair.algorithm

        if algorithm in (JWSAlgorithm.RS256, JWSAlgorithm.RS384, JWSAlgorithm.RS512):
            hash_alg = {
                JWSAlgorithm.RS256: hashes.SHA256(),
                JWSAlgorithm.RS384: hashes.SHA384(),
                JWSAlgorithm.RS512: hashes.SHA512(),
            }[algorithm]

            return self._private_key.sign(
                data,
                padding.PKCS1v15(),
                hash_alg,
            )

        elif algorithm in (JWSAlgorithm.ES256, JWSAlgorithm.ES384, JWSAlgorithm.ES512):
            hash_alg = {
                JWSAlgorithm.ES256: hashes.SHA256(),
                JWSAlgorithm.ES384: hashes.SHA384(),
                JWSAlgorithm.ES512: hashes.SHA512(),
            }[algorithm]

            from cryptography.hazmat.primitives.asymmetric import ec as ec_module
            return self._private_key.sign(
                data,
                ec_module.ECDSA(hash_alg),
            )

        raise ValueError(f"Unsupported algorithm: {algorithm}")

    def _verify(
        self,
        data: bytes,
        signature: bytes,
        public_key: Any,
    ) -> bool:
        """Verify signature with public key."""
        algorithm = self._keypair.algorithm

        try:
            if algorithm in (JWSAlgorithm.RS256, JWSAlgorithm.RS384, JWSAlgorithm.RS512):
                hash_alg = {
                    JWSAlgorithm.RS256: hashes.SHA256(),
                    JWSAlgorithm.RS384: hashes.SHA384(),
                    JWSAlgorithm.RS512: hashes.SHA512(),
                }[algorithm]

                public_key.verify(
                    signature,
                    data,
                    padding.PKCS1v15(),
                    hash_alg,
                )
                return True

            elif algorithm in (JWSAlgorithm.ES256, JWSAlgorithm.ES384, JWSAlgorithm.ES512):
                hash_alg = {
                    JWSAlgorithm.ES256: hashes.SHA256(),
                    JWSAlgorithm.ES384: hashes.SHA384(),
                    JWSAlgorithm.ES512: hashes.SHA512(),
                }[algorithm]

                from cryptography.hazmat.primitives.asymmetric import ec as ec_module
                public_key.verify(
                    signature,
                    data,
                    ec_module.ECDSA(hash_alg),
                )
                return True

        except InvalidSignature:
            return False
        except Exception as e:
            logger.warning(f"Verification error: {e}")
            return False

        return False

    @staticmethod
    def _remove_defaults(data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove properties with default/empty values."""
        result = {}
        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, (list, dict)) and not value:
                continue
            if isinstance(value, str) and not value:
                continue
            if isinstance(value, dict):
                cleaned = JWSSigner._remove_defaults(value)
                if cleaned:
                    result[key] = cleaned
            elif isinstance(value, list):
                cleaned_list = [
                    JWSSigner._remove_defaults(v) if isinstance(v, dict) else v
                    for v in value
                    if v is not None
                ]
                if cleaned_list:
                    result[key] = cleaned_list
            else:
                result[key] = value
        return result


# =============================================================================
# SIGNED AGENT CARD
# =============================================================================


@dataclass
class SignedAgentCard:
    """Agent Card with JWS signatures.

    Wraps an Agent Card with one or more JWS signatures.
    """

    card: Dict[str, Any]
    signatures: List[JWSSignature] = field(default_factory=list)

    def add_signature(self, signer: JWSSigner) -> None:
        """Add a signature to the card."""
        signature = signer.sign_agent_card(self.card)
        self.signatures.append(signature)

    def verify_all(
        self,
        signers: List[JWSSigner],
    ) -> bool:
        """Verify all signatures."""
        if len(self.signatures) != len(signers):
            return False

        for sig, signer in zip(self.signatures, signers):
            if not signer.verify_signature(self.card, sig):
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (A2A-compliant format)."""
        result = dict(self.card)
        result["signatures"] = [
            {
                "protected": sig.protected,
                "signature": sig.signature,
                "jku": sig.jku,
            }
            for sig in self.signatures
        ]
        return result


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "JWSAlgorithm",
    "JWSHeader",
    "JWSSignature",
    "KeyPair",
    "KeyManager",
    "JWSSigner",
    "SignedAgentCard",
    "base64url_encode",
    "base64url_decode",
    "canonicalize_json",
]
