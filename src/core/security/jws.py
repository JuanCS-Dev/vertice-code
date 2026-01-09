"""
JWS Signer for Agent Cards
==========================

JSON Web Signature (RFC 7515) implementation for A2A Agent Card authentication.

This module provides:
- JWS signing and verification
- RSA and EC key pair generation
- JCS canonicalization (RFC 8785)

Reference:
- RFC 7515 (JWS): https://datatracker.ietf.org/doc/html/rfc7515
- RFC 8785 (JCS): https://datatracker.ietf.org/doc/html/rfc8785
- A2A Spec: https://a2a-protocol.org/latest/specification/

Example:
    >>> from core.security.jws import KeyManager, JWSSigner
    >>> keypair = KeyManager.generate_rsa_keypair()
    >>> signer = JWSSigner(keypair)
    >>> signature = signer.sign_agent_card(agent_card)
    >>> assert signer.verify_signature(agent_card, signature)

Author: JuanCS Dev
Date: 2025-12-30
"""

from .jws_types import (
    JWSAlgorithm,
    JWSHeader,
    JWSSignature,
    KeyPair,
    base64url_encode,
    base64url_decode,
    canonicalize_json,
)
from .jws_keys import KeyManager
from .jws_signer import JWSSigner, SignedAgentCard


__all__ = [
    # Types
    "JWSAlgorithm",
    "JWSHeader",
    "JWSSignature",
    "KeyPair",
    # Key Management
    "KeyManager",
    # Signing
    "JWSSigner",
    "SignedAgentCard",
    # Utilities
    "base64url_encode",
    "base64url_decode",
    "canonicalize_json",
]
