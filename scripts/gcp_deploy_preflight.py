#!/usr/bin/env python3
"""GCP deploy preflight guardrails (commit/push).

Goal: block commits/pushes that are known to break Google Cloud deploy/runtime.

Design:
- Commit stage: cheap checks on staged files (policy + obvious drift).
- Push stage: full repository invariants (Cloud Build, Dockerfiles, Vertex runtime contracts).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Finding:
    message: str
    file: Path | None = None


DISALLOWED_MODEL_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Policy: forbid Gemini 1/2 references (code + docs). Use Gemini 3 only.
    re.compile(r"\bgemini-(?:1|2)(?:\.\d+)?\b", re.IGNORECASE),
    re.compile(r"\bgemini-1\.5\b", re.IGNORECASE),
)


def _iter_lines(path: Path) -> Iterable[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return []


def _normalize_paths(files: list[str]) -> list[Path]:
    out: list[Path] = []
    for name in files:
        p = Path(name)
        if not p.is_absolute():
            p = (REPO_ROOT / p).resolve()
        if REPO_ROOT in p.parents or p == REPO_ROOT:
            out.append(p)
    return out


def _scan_disallowed_models(files: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        if not path.is_file():
            continue
        for i, line in enumerate(_iter_lines(path), start=1):
            for pat in DISALLOWED_MODEL_PATTERNS:
                if pat.search(line):
                    findings.append(
                        Finding(f"Disallowed model reference at L{i}: {line.strip()}", path)
                    )
                    break
    return findings


def _require_files_exist(paths: Iterable[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for p in paths:
        if not p.exists():
            findings.append(Finding("Required file missing (deploy would break).", p))
    return findings


def _assert_contains(path: Path, *, needles: Iterable[str]) -> list[Finding]:
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    findings: list[Finding] = []
    for needle in needles:
        if needle not in text:
            findings.append(Finding(f"Expected content missing: {needle!r}", path))
    return findings


def _full_repo_invariants() -> list[Finding]:
    findings: list[Finding] = []

    # Cloud Build contract (monorepo context must be repo root ".")
    findings += _require_files_exist(
        [
            REPO_ROOT / "cloudbuild.backend.yaml",
            REPO_ROOT / "cloudbuild.mcp.yaml",
            REPO_ROOT / "Dockerfile.backend",
            REPO_ROOT / "Dockerfile.mcp",
            REPO_ROOT / "tools" / "deploy_brain.py",
            REPO_ROOT / "apps" / "agent-gateway" / "config" / "engines.json",
        ]
    )

    findings += _assert_contains(
        REPO_ROOT / "cloudbuild.backend.yaml",
        needles=[
            "Dockerfile.backend",
            "gcr.io/cloud-builders/docker",
            "-t",
            "vertice-cloud/backend",
            ".",
        ],
    )
    findings += _assert_contains(
        REPO_ROOT / "cloudbuild.mcp.yaml",
        needles=[
            "Dockerfile.mcp",
            "gcr.io/cloud-builders/docker",
            "-t",
            "vertice-cloud/mcp-server",
            ".",
        ],
    )

    # Cloud Run container contract: bind 0.0.0.0, port from env
    findings += _assert_contains(
        REPO_ROOT / "Dockerfile.backend",
        needles=["python:3.11-slim", "--host", "0.0.0.0", "${PORT"],
    )
    findings += _assert_contains(
        REPO_ROOT / "Dockerfile.mcp",
        needles=[
            "python:3.11-slim",
            "vertice_core.prometheus.mcp_server.run_server",
            "ENV PORT=8080",
        ],
    )

    # Vertex Reasoning Engine runtime must be regional (NOT global)
    engines_json = REPO_ROOT / "apps" / "agent-gateway" / "config" / "engines.json"
    if engines_json.exists():
        txt = engines_json.read_text(encoding="utf-8", errors="replace")
        if '"location": "global"' in txt or '"location":"global"' in txt:
            findings.append(
                Finding(
                    'Invalid engine runtime location: "global". Reasoning Engine runtime is regional.',
                    engines_json,
                )
            )

    return findings


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices={"commit", "push"}, required=True)
    parser.add_argument("--full", action="store_true")
    parser.add_argument("files", nargs="*")
    args = parser.parse_args(argv)

    stage = args.stage
    env_stage = os.getenv("PRE_COMMIT_STAGE")
    if env_stage and env_stage != stage:
        # Keep behavior deterministic even if user calls script manually.
        stage = env_stage

    findings: list[Finding] = []
    staged_files = _normalize_paths(args.files)

    # Always enforce policy on changed files.
    if staged_files:
        findings += _scan_disallowed_models(staged_files)

    # Full invariants at push stage (or when requested).
    if stage == "push" or args.full:
        findings += _full_repo_invariants()

    if not findings:
        return 0

    print("GCP deploy preflight FAILED:")
    for f in findings[:50]:
        loc = f" ({f.file})" if f.file else ""
        print(f"- {f.message}{loc}")
    if len(findings) > 50:
        print(f"... and {len(findings) - 50} more")

    print(
        "\nFix the issues above before committing/pushing. "
        "If you intentionally need an exception, update the guardrails explicitly."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
