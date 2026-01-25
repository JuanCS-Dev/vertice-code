from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure() -> None:
    """
    Ensure `import app.*` works when running tests from the monorepo root.

    These tests belong to `vertice-chat-webapp/backend`, which is not installed as a package in this repo.
    """

    backend_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backend_root))
