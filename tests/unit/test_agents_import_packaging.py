from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_agents_package_importable_without_repo_root(tmp_path: Path) -> None:
    """
    Regression for Vertex Reasoning Engine runtime:
    the managed environment won't have the repo-root `agents/` symlink/tree.

    We simulate that by running python from an empty CWD and setting PYTHONPATH
    to the monorepo source dir that is shipped via deploy_brain `extra_packages`.
    """

    repo_root = Path(__file__).resolve().parents[2]
    core_src = repo_root / "packages" / "vertice-core" / "src"

    env = {**os.environ, "PYTHONPATH": str(core_src)}

    cmd = [
        sys.executable,
        "-c",
        "import agents; import agents.coder.reasoning_engine_app as app; print(agents.__file__); print(app.__file__)",
    ]
    proc = subprocess.run(
        cmd,
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "packages/vertice-core/src/agents" in proc.stdout.replace("\\", "/")
