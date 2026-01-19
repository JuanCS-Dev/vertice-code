import sqlite3
import queue
from contextlib import contextmanager
from typing import Dict
from pathlib import Path


class ConnectionPool:
    """A thread-safe SQLite connection pool."""

    def __init__(self, max_connections: int = 10):
        self._pools: Dict[str, queue.Queue] = {}
        self.max_connections = max_connections

    def get_connection(self, db_path: Path) -> sqlite3.Connection:
        """Get a connection from the pool."""
        db_key = str(db_path)
        if db_key not in self._pools:
            self._pools[db_key] = queue.Queue(maxsize=self.max_connections)

        pool = self._pools[db_key]
        try:
            return pool.get_nowait()
        except queue.Empty:
            return sqlite3.connect(db_path, check_same_thread=False)

    def release_connection(self, db_path: Path, conn: sqlite3.Connection):
        """Release a connection back to the pool."""
        db_key = str(db_path)
        if db_key in self._pools:
            pool = self._pools[db_key]
            try:
                pool.put_nowait(conn)
            except queue.Full:
                conn.close()

    @contextmanager
    def get_conn(self, db_path: Path):
        """A context manager to get and release a connection."""
        conn = self.get_connection(db_path)
        try:
            yield conn
        finally:
            self.release_connection(db_path, conn)


_connection_pool = ConnectionPool()


def get_connection_pool() -> ConnectionPool:
    """Get the global connection pool instance."""
    return _connection_pool
