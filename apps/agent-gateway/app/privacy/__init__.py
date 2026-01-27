"""
Privacy Module for GDPR/LGPD Compliance.

Provides:
- Data encryption at rest (AES-256-GCM)
- Right to be Forgotten (data erasure)
- Data Portability (export)
- Consent management

Part of M9: Data Protection & Privacy.
"""

from privacy.crypto import (
    PrivacyCryptoService,
    get_crypto_service,
    encrypt_field,
    decrypt_field,
)
from privacy.erasure import (
    DataErasureService,
    ErasureRequest,
    ErasureStatus,
)
from privacy.export import (
    DataExportService,
    ExportRequest,
    ExportFormat,
)

__all__ = [
    # Crypto
    "PrivacyCryptoService",
    "get_crypto_service",
    "encrypt_field",
    "decrypt_field",
    # Erasure
    "DataErasureService",
    "ErasureRequest",
    "ErasureStatus",
    # Export
    "DataExportService",
    "ExportRequest",
    "ExportFormat",
]
