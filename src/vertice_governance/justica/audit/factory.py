"""
Audit Factory - Factory functions for creating audit loggers.

Provides convenience functions for creating AuditLogger instances
with different configurations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from .backends import ConsoleBackend, FileBackend, InMemoryBackend
from .logger import AuditLogger


def create_default_logger(
    log_dir: Optional[str | Path] = None,
    console: bool = True,
    file: bool = True,
) -> AuditLogger:
    """Cria um logger com configuracao padrao."""
    backends = []

    if console:
        backends.append(ConsoleBackend())

    if file and log_dir:
        log_path = Path(log_dir) / "justica_audit.jsonl"
        backends.append(FileBackend(log_path))

    return AuditLogger(backends=backends)


def create_test_logger() -> Tuple[AuditLogger, InMemoryBackend]:
    """Cria um logger para testes com backend em memoria."""
    memory_backend = InMemoryBackend()
    logger = AuditLogger(backends=[memory_backend], async_mode=False)
    return logger, memory_backend


def create_file_only_logger(
    filepath: str | Path,
    max_size_mb: int = 100,
    backup_count: int = 5,
) -> AuditLogger:
    """Cria um logger apenas com arquivo (sem console)."""
    file_backend = FileBackend(
        filepath=filepath,
        max_size_mb=max_size_mb,
        backup_count=backup_count,
    )
    return AuditLogger(backends=[file_backend])


__all__ = [
    "create_default_logger",
    "create_test_logger",
    "create_file_only_logger",
]
