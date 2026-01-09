"""
Audit Package - Audit logging system for JUSTICA governance.

"Documentacao: 100% acoes"
"Uma decisao que nao pode ser explicada nao deveria ser tomada"

This package provides transparent, traceable audit logging with
multiple backend support.

Submodules:
    - types: AuditLevel, AuditCategory enums
    - entry: AuditEntry dataclass
    - backends: AuditBackend ABC and implementations
    - logger: AuditLogger main class
    - factory: Factory functions

Usage:
    from vertice_governance.justica.audit import (
        AuditLogger,
        AuditLevel,
        AuditCategory,
        create_test_logger,
    )

    logger, memory = create_test_logger()
    logger.log_system_event("Started", {"version": "3.0.0"})
"""

# Types
from .types import (
    AuditCategory,
    AuditLevel,
)

# Entry
from .entry import AuditEntry

# Backends
from .backends import (
    AuditBackend,
    ConsoleBackend,
    FileBackend,
    InMemoryBackend,
)

# Logger
from .logger import AuditLogger

# Factory
from .factory import (
    create_default_logger,
    create_file_only_logger,
    create_test_logger,
)


__all__ = [
    # Types
    "AuditLevel",
    "AuditCategory",
    # Entry
    "AuditEntry",
    # Backends
    "AuditBackend",
    "ConsoleBackend",
    "FileBackend",
    "InMemoryBackend",
    # Logger
    "AuditLogger",
    # Factory
    "create_default_logger",
    "create_test_logger",
    "create_file_only_logger",
]
