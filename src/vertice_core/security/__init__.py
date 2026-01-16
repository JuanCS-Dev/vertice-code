"""
Security Module - OAuth 2.1, PKCE, JWS, and MCP Authorization.
==============================================================

Implements MCP 2025-11-25 and A2A v0.3 security requirements:
- PKCE (Proof Key for Code Exchange) with S256
- OAuth 2.1 authorization code flow
- URL mode elicitation (SEP-1036)
- Protected Resource Metadata (RFC 9728)
- JWS signatures for Agent Cards (RFC 7515)
- JCS canonicalization (RFC 8785)

References:
- MCP Authorization: https://modelcontextprotocol.io/specification/draft/basic/authorization
- OAuth 2.1: https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-12
- PKCE: https://datatracker.ietf.org/doc/html/rfc7636
- JWS: https://datatracker.ietf.org/doc/html/rfc7515
- JCS: https://datatracker.ietf.org/doc/html/rfc8785

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

from .pkce import PKCEChallenge, generate_pkce
from .oauth21 import (
    OAuth21Client,
    OAuth21Config,
    TokenResponse,
    AuthorizationServerMetadata,
    ProtectedResourceMetadata,
)
from .consent import (
    ConsentLevel,
    OperationCategory,
    ConsentRequest,
    ConsentRecord,
    ConsentManager,
    requires_consent,
)
from .jws import (
    JWSAlgorithm,
    JWSHeader,
    JWSSignature,
    KeyPair,
    KeyManager,
    JWSSigner,
    SignedAgentCard,
    base64url_encode,
    base64url_decode,
    canonicalize_json,
)

__all__ = [
    # PKCE
    "PKCEChallenge",
    "generate_pkce",
    # OAuth 2.1
    "OAuth21Client",
    "OAuth21Config",
    "TokenResponse",
    "AuthorizationServerMetadata",
    "ProtectedResourceMetadata",
    # Consent
    "ConsentLevel",
    "OperationCategory",
    "ConsentRequest",
    "ConsentRecord",
    "ConsentManager",
    "requires_consent",
    # JWS (A2A Security Cards)
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
