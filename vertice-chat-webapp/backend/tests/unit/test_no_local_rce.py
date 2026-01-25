from __future__ import annotations

import re
from pathlib import Path


def test_backend_app_has_no_exec_or_eval_calls() -> None:
    """
    PR-0: hard block of local RCE surfaces.

    We intentionally fail if `exec(` or `eval(` appears anywhere in backend app code.
    """

    app_root = Path(__file__).resolve().parents[2] / "app"
    assert app_root.exists()

    exec_re = re.compile(r"(?<![A-Za-z0-9_])exec\(")
    eval_re = re.compile(r"(?<![A-Za-z0-9_])eval\(")

    offenders: list[str] = []
    for path in sorted(app_root.rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if exec_re.search(text) or eval_re.search(text):
            offenders.append(str(path.relative_to(app_root)))

    assert offenders == [], f"Found forbidden patterns in: {offenders}"
