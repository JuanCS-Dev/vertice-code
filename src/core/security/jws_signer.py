"""
JWS Signer for Agent Cards
==========================

Signs and verifies Agent Cards using JWS (RFC 7515) with JCS canonicalization.

Reference:
- RFC 7515 (JWS): https://datatracker.ietf.org/doc/html/rfc7515
- A2A Spec: https://a2a-protocol.org/latest/specification/

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .jws_types import (
    JWSAlgorithm,
    JWSHeader,
    JWSSignature,
    KeyPair,
    base64url_encode,
    base64url_decode,
    canonicalize_json,
)

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend
    from cryptography.exceptions import InvalidSignature
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

logger = logging.getLogger(__name__)


class JWSSigner:
    """JWS Signer for Agent Cards.

    Signs Agent Cards using JWS (RFC 7515) with JCS canonicalization (RFC 8785).

    Example:
        >>> signer = JWSSigner(keypair)
        >>> signature = signer.sign_agent_card(agent_card_dict)
        >>> is_valid = signer.verify_signature(agent_card_dict, signature)

    Attributes:
        keypair: The key pair used for signing
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

        Raises:
            RuntimeError: If cryptography not installed
        """
        if not HAS_CRYPTOGRAPHY:
            raise RuntimeError(
                "cryptography not installed. Install with: pip install cryptography"
            )

        self._keypair = keypair
        self._jku = jku

        self._private_key = serialization.load_pem_private_key(
            keypair.private_key,
            password=None,
            backend=default_backend(),
        )
        self._public_key = serialization.load_pem_public_key(
            keypair.public_key,
            backend=default_backend(),
        )

    @property
    def keypair(self) -> KeyPair:
        """Get the key pair."""
        return self._keypair

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
        payload = {k: v for k, v in agent_card.items() if k != "signatures"}
        payload = self._remove_defaults(payload)
        canonical = canonicalize_json(payload)

        header = JWSHeader(
            alg=self._keypair.algorithm,
            typ="JWS",
            kid=self._keypair.key_id,
            jku=self._jku,
        )
        protected = base64url_encode(
            json.dumps(header.to_dict()).encode("utf-8")
        )

        signing_input = f"{protected}.{base64url_encode(canonical)}".encode("ascii")
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
            True if signature is valid, False otherwise
        """
        try:
            payload = {k: v for k, v in agent_card.items() if k != "signatures"}
            payload = self._remove_defaults(payload)
            canonical = canonicalize_json(payload)

            signing_input = (
                f"{signature.protected}.{base64url_encode(canonical)}".encode("ascii")
            )

            sig_bytes = base64url_decode(signature.signature)

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
        result: Dict[str, Any] = {}
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


@dataclass
class SignedAgentCard:
    """Agent Card with JWS signatures.

    Wraps an Agent Card with one or more JWS signatures.

    Attributes:
        card: The Agent Card dictionary
        signatures: List of JWS signatures

    Example:
        >>> signed = SignedAgentCard(card=agent_card_dict)
        >>> signed.add_signature(signer)
        >>> print(signed.to_dict())
    """

    card: Dict[str, Any]
    signatures: List[JWSSignature] = field(default_factory=list)

    def add_signature(self, signer: JWSSigner) -> None:
        """Add a signature to the card.

        Args:
            signer: JWSSigner to sign with
        """
        signature = signer.sign_agent_card(self.card)
        self.signatures.append(signature)

    def verify_all(
        self,
        signers: List[JWSSigner],
    ) -> bool:
        """Verify all signatures.

        Args:
            signers: List of signers (one per signature)

        Returns:
            True if all signatures valid, False otherwise
        """
        if len(self.signatures) != len(signers):
            return False

        for sig, signer in zip(self.signatures, signers):
            if not signer.verify_signature(self.card, sig):
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (A2A-compliant format).

        Returns:
            Dictionary with card data and signatures
        """
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


__all__ = [
    "JWSSigner",
    "SignedAgentCard",
]
