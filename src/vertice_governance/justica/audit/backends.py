"""
Audit Backends - Storage backends for audit logs.

Abstract backend and concrete implementations:
- ConsoleBackend: Terminal output with colors
- FileBackend: JSON Lines file with rotation
- InMemoryBackend: In-memory storage for testing
"""

from __future__ import annotations

import sys
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, TextIO

from .entry import AuditEntry
from .types import AuditCategory, AuditLevel


class AuditBackend(ABC):
    """
    Backend abstrato para persistencia de audit logs.

    Implementacoes podem incluir:
    - Console/Stdout
    - Arquivo (JSON Lines, rotativo)
    - Banco de dados
    - Sistema de logs centralizado (ELK, CloudWatch, etc.)
    - Blockchain (para auditoria imutavel)
    """

    @abstractmethod
    def write(self, entry: AuditEntry) -> bool:
        """Escreve uma entrada. Retorna True se bem-sucedido."""
        pass

    @abstractmethod
    def flush(self) -> None:
        """Forca flush de buffers."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Fecha o backend."""
        pass


class ConsoleBackend(AuditBackend):
    """Backend que escreve para console com formatacao colorida."""

    LEVEL_COLORS = {
        AuditLevel.DEBUG: "\033[90m",      # Cinza
        AuditLevel.INFO: "\033[97m",       # Branco
        AuditLevel.WARNING: "\033[93m",    # Amarelo
        AuditLevel.ERROR: "\033[91m",      # Vermelho
        AuditLevel.CRITICAL: "\033[95m",   # Magenta
        AuditLevel.SECURITY: "\033[96m",   # Ciano
    }
    RESET = "\033[0m"

    def __init__(
        self,
        stream: TextIO = sys.stdout,
        use_colors: bool = True,
        min_level: AuditLevel = AuditLevel.INFO,
    ):
        self.stream = stream
        self.use_colors = use_colors and stream.isatty()
        self.min_level = min_level

    def write(self, entry: AuditEntry) -> bool:
        if entry.level.value < self.min_level.value:
            return True  # Ignorado mas nao e erro

        try:
            color = self.LEVEL_COLORS.get(entry.level, "") if self.use_colors else ""
            reset = self.RESET if self.use_colors else ""

            timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            agent = f"[{entry.agent_id}]" if entry.agent_id else ""

            line = (
                f"{color}[{timestamp}] [{entry.level.name:8}] "
                f"[{entry.category.value}] {agent} {entry.action}{reset}\n"
            )

            if entry.reasoning:
                line += f"  -> Reasoning: {entry.reasoning}\n"

            self.stream.write(line)
            return True
        except (IOError, OSError, ValueError):
            return False

    def flush(self) -> None:
        # SECURITY FIX: Check if stream is closed
        # Prevents "ValueError: I/O operation on closed file" in atexit
        try:
            if hasattr(self.stream, 'closed') and not self.stream.closed:
                self.stream.flush()
        except (ValueError, AttributeError):
            pass

    def close(self) -> None:
        # SECURITY FIX: Safe close with error handling
        try:
            self.flush()
        except (IOError, OSError, ValueError):
            pass


class FileBackend(AuditBackend):
    """Backend que escreve para arquivo JSON Lines com rotacao."""

    def __init__(
        self,
        filepath: str | Path,
        max_size_mb: int = 100,
        backup_count: int = 5,
    ):
        self.filepath = Path(filepath)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.backup_count = backup_count

        # Criar diretorio se nao existir
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        # Abrir arquivo
        self._file: Optional[TextIO] = None
        self._open_file()

    def _open_file(self) -> None:
        self._file = open(self.filepath, "a", encoding="utf-8")

    def _rotate_if_needed(self) -> None:
        if not self._file:
            return

        try:
            if self.filepath.stat().st_size >= self.max_size_bytes:
                self._file.close()
                self._rotate_files()
                self._open_file()
        except OSError:
            pass

    def _rotate_files(self) -> None:
        """Rotaciona arquivos de backup."""
        # Deletar o mais antigo
        oldest = self.filepath.with_suffix(f".{self.backup_count}.jsonl")
        if oldest.exists():
            oldest.unlink()

        # Renomear em cascata
        for i in range(self.backup_count - 1, 0, -1):
            current = self.filepath.with_suffix(f".{i}.jsonl")
            next_file = self.filepath.with_suffix(f".{i + 1}.jsonl")
            if current.exists():
                current.rename(next_file)

        # Renomear atual para .1
        if self.filepath.exists():
            self.filepath.rename(self.filepath.with_suffix(".1.jsonl"))

    def write(self, entry: AuditEntry) -> bool:
        if not self._file:
            return False

        try:
            self._rotate_if_needed()
            self._file.write(entry.to_json() + "\n")
            return True
        except (IOError, OSError, ValueError):
            return False

    def flush(self) -> None:
        if self._file:
            self._file.flush()

    def close(self) -> None:
        if self._file:
            self._file.close()
            self._file = None


class InMemoryBackend(AuditBackend):
    """Backend que mantem logs em memoria (util para testes)."""

    def __init__(self, max_entries: int = 10000):
        self.max_entries = max_entries
        self.entries: List[AuditEntry] = []
        self._lock = threading.Lock()

    def write(self, entry: AuditEntry) -> bool:
        with self._lock:
            self.entries.append(entry)
            if len(self.entries) > self.max_entries:
                self.entries = self.entries[-self.max_entries:]
        return True

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass

    def get_entries(
        self,
        level: Optional[AuditLevel] = None,
        category: Optional[AuditCategory] = None,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Retorna entradas com filtros opcionais."""
        with self._lock:
            entries = self.entries.copy()

        if level:
            entries = [e for e in entries if e.level == level]
        if category:
            entries = [e for e in entries if e.category == category]
        if agent_id:
            entries = [e for e in entries if e.agent_id == agent_id]

        return entries[-limit:]

    def clear(self) -> None:
        """Limpa todas as entradas."""
        with self._lock:
            self.entries.clear()


__all__ = [
    "AuditBackend",
    "ConsoleBackend",
    "FileBackend",
    "InMemoryBackend",
]
