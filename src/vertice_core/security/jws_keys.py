"""
JWS Key Management
==================

Key pair generation for JWS signing (RSA and EC).

Reference:
- RFC 7517 (JWK): https://datatracker.ietf.org/doc/html/rfc7517
- RFC 7518 (JWA): https://datatracker.ietf.org/doc/html/rfc7518

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import secrets
from typing import Optional

from .jws_types import JWSAlgorithm, KeyPair

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, ec
    from cryptography.hazmat.backends import default_backend

    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


class KeyManager:
    """Key pair generation and management.

    Generates RSA-2048 or EC P-256/P-384/P-521 key pairs for JWS signing.
    Keys are stored in PEM format.

    Example:
        >>> keypair = KeyManager.generate_rsa_keypair()
        >>> print(keypair.key_id)
        'rsa-a1b2c3d4e5f6g7h8'

        >>> ec_keypair = KeyManager.generate_ec_keypair("P-256")
        >>> print(ec_keypair.algorithm)
        JWSAlgorithm.ES256
    """

    @staticmethod
    def generate_rsa_keypair(
        key_size: int = 2048,
        key_id: Optional[str] = None,
    ) -> KeyPair:
        """Generate RSA key pair.

        Args:
            key_size: RSA key size (2048, 3072, or 4096)
            key_id: Optional key identifier (auto-generated if not provided)

        Returns:
            KeyPair with RSA keys in PEM format

        Raises:
            RuntimeError: If cryptography package not installed
            ValueError: If key_size is invalid
        """
        if not HAS_CRYPTOGRAPHY:
            raise RuntimeError("cryptography not installed. Install with: pip install cryptography")

        if key_size not in (2048, 3072, 4096):
            raise ValueError(f"Invalid key_size: {key_size}. Use 2048, 3072, or 4096")

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

        if not key_id:
            key_id = f"rsa-{secrets.token_hex(8)}"

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
            key_id: Optional key identifier (auto-generated if not provided)

        Returns:
            KeyPair with EC keys in PEM format

        Raises:
            RuntimeError: If cryptography package not installed
            ValueError: If curve is not supported
        """
        if not HAS_CRYPTOGRAPHY:
            raise RuntimeError("cryptography not installed. Install with: pip install cryptography")

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


__all__ = [
    "KeyManager",
    "HAS_CRYPTOGRAPHY",
]
