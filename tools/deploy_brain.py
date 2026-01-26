from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, Optional, Sequence


class DeployBrainError(RuntimeError):
    pass


@dataclass(frozen=True)
class DeployedEngine:
    agent: str
    engine_id: str
    display_name: str
    project: str
    location: str


AGENT_IMPORTS: Dict[str, Dict[str, str]] = {
    "coder": {
        "module": "vertice_core.agents.coder.reasoning_engine_app",
        "symbol": "CoderReasoningEngineApp",
    },
    "reviewer": {
        "module": "vertice_core.agents.reviewer.reasoning_engine_app",
        "symbol": "ReviewerReasoningEngineApp",
    },
    "architect": {
        "module": "vertice_core.agents.architect.reasoning_engine_app",
        "symbol": "ArchitectReasoningEngineApp",
    },
    "orchestrator": {
        "module": "vertice_core.agents.orchestrator.agent",
        "symbol": "OrchestratorAgent",
    },
    "researcher": {"module": "vertice_core.agents.researcher.agent", "symbol": "ResearcherAgent"},
    "devops": {"module": "vertice_core.agents.devops.agent", "symbol": "DevOpsAgent"},
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_src_on_path() -> None:
    # Avoid accidental import of the repo-root `agents` symlink target being absent.
    # Prefer the monorepo python sources explicitly.
    repo_root = Path(__file__).resolve().parents[1]
    core_src = repo_root / "packages" / "vertice-core" / "src"
    sys.path.insert(0, str(core_src))


def _load_agent_class(agent: str) -> type[Any]:
    if agent not in AGENT_IMPORTS:
        raise DeployBrainError(
            f"Unknown agent '{agent}'. Supported: {', '.join(sorted(AGENT_IMPORTS))}"
        )
    spec = AGENT_IMPORTS[agent]
    try:
        mod = import_module(spec["module"])
    except Exception as e:  # pragma: no cover
        raise DeployBrainError(f"Failed to import {spec['module']}: {e}") from e
    try:
        return getattr(mod, spec["symbol"])
    except AttributeError as e:  # pragma: no cover
        raise DeployBrainError(f"Missing symbol {spec['symbol']} in {spec['module']}") from e


def _create_reasoning_engine(
    *,
    agent_class: type[Any],
    display_name: str,
    project: str,
    location: str,
    staging_bucket: Optional[str],
    requirements: Optional[Sequence[str]],
    extra_packages: Optional[Sequence[str]],
    sys_version: Optional[str],
) -> str:
    """
    Create a Vertex AI Reasoning Engine and return the engine resource id/name.

    This function intentionally does not handle auth; it will fail closed if the
    environment isn't configured for Vertex AI.
    """
    try:
        from vertexai.preview import reasoning_engines  # type: ignore
        import vertexai
    except Exception as e:  # pragma: no cover
        raise DeployBrainError(
            "Vertex AI SDK not available. Install/enable `google-cloud-aiplatform` "
            "and ensure `vertexai.preview.reasoning_engines` is importable."
        ) from e

    # NOTE: Google manages scaling and tool execution. The agent_class must be
    # compatible with the Reasoning Engine runtime (Phase 2 requirement).
    try:
        repo_root = Path(__file__).resolve().parents[1]
        core_src = repo_root / "packages" / "vertice-core" / "src"
        cwd_before = os.getcwd()

        # Contract (Google 2026): package resolution should be stable and not depend on repo-root symlinks.
        # Always deploy from `packages/vertice-core/src` so extra_packages can refer to real directories.
        os.chdir(str(core_src))

        # Pass a stable, explicit list by default. If the caller provides `extra_packages`,
        # use it as-is (but still from core_src cwd).
        extra_packages_to_use = (
            list(extra_packages) if extra_packages else ["agents", "vertice_core", "vertice_agents"]
        )

        missing: list[str] = []
        for rel in ["agents", "vertice_core", "vertice_agents"]:
            if not (core_src / rel).exists():
                missing.append(str(core_src / rel))
        if missing:
            raise DeployBrainError(
                "extra_packages preflight failed; missing paths: " + ", ".join(missing)
            )

        vertexai.init(project=project, location=location, staging_bucket=staging_bucket)

        default_requirements = [
            # Best practice (Google): pin key deps for reproducible builds.
            "google-cloud-aiplatform==1.130.0",
            "cloudpickle==3.1.1",
            "google-genai==1.60.0",
            "google-cloud-alloydb-connector",
            "pydantic>=2.5.0",
            "async-lru",
            "sqlalchemy",
            "asyncpg",
            "pgvector",
            "structlog",
        ]

        engine = reasoning_engines.ReasoningEngine.create(
            agent_class(),
            display_name=display_name,
            requirements=list(requirements) if requirements else default_requirements,
            extra_packages=extra_packages_to_use,
            sys_version=sys_version,
        )
    except Exception as e:  # pragma: no cover
        try:
            os.chdir(cwd_before)
        except Exception:
            pass
        raise DeployBrainError(
            f"Failed to create ReasoningEngine: {e}. Verify ADC credentials, project/location, "
            "and required Vertex APIs are enabled."
        ) from e
    finally:
        try:
            os.chdir(cwd_before)
        except Exception:
            pass

    # Prefer fully-qualified resource name for downstream consumers (gateway SDK clients).
    engine_id = getattr(engine, "resource_name", None) or getattr(engine, "name", None)
    if not engine_id:
        raise DeployBrainError("ReasoningEngine.create returned an object without an id/name")
    return str(engine_id)


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"engines": {}, "updated_at": _utc_now_iso()}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:  # pragma: no cover
        raise DeployBrainError(f"Invalid JSON in {path}: {e}") from e


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def deploy_brain(
    *,
    agent: str,
    project: str,
    location: str,
    display_name: Optional[str],
    engines_config_path: Path,
    dry_run: bool,
    staging_bucket: Optional[str] = None,
    requirements: Optional[Sequence[str]] = None,
    extra_packages: Optional[Sequence[str]] = None,
    sys_version: Optional[str] = None,
) -> DeployedEngine:
    _ensure_src_on_path()

    if location.strip().lower() == "global":
        raise DeployBrainError(
            "Invalid location='global' for Reasoning Engine runtime. "
            "Reasoning Engines are regional resources (e.g. us-central1). "
            "Keep model inference on the global endpoint separately."
        )

    agent_class = _load_agent_class(agent)
    final_display_name = display_name or f"vertice-{agent}"

    if dry_run:
        engine_id = f"dry-run://{agent}/{_utc_now_iso()}"
    else:
        engine_id = _create_reasoning_engine(
            agent_class=agent_class,
            display_name=final_display_name,
            project=project,
            location=location,
            staging_bucket=staging_bucket,
            requirements=requirements,
            extra_packages=extra_packages,
            sys_version=sys_version,
        )

    payload = _read_json(engines_config_path)
    engines = payload.setdefault("engines", {})
    engines[agent] = {
        "engine_id": engine_id,
        "display_name": final_display_name,
        "project": project,
        "location": location,
        "deployed_at": _utc_now_iso(),
    }
    payload["updated_at"] = _utc_now_iso()
    _write_json(engines_config_path, payload)

    return DeployedEngine(
        agent=agent,
        engine_id=engine_id,
        display_name=final_display_name,
        project=project,
        location=location,
    )


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Deploy Vertice core agents to Vertex AI Reasoning Engines."
    )
    p.add_argument("--agent", required=True, choices=sorted(AGENT_IMPORTS.keys()))
    p.add_argument("--project", required=True)
    # Reasoning Engine resources are regional (not 'global').
    p.add_argument("--location", default="us-central1")
    p.add_argument("--display-name", default=None)
    p.add_argument(
        "--staging-bucket",
        default=None,
        help="Optional GCS bucket for packaging/staging (e.g. gs://... in the same region).",
    )
    p.add_argument(
        "--requirement",
        action="append",
        default=[],
        help="Extra pip requirement(s) to install in the managed runtime (repeatable).",
    )
    p.add_argument(
        "--extra-package",
        action="append",
        default=[],
        help="Extra local package(s) to ship to the runtime (dir or wheel). Default: packages/vertice-core/src",
    )
    p.add_argument(
        "--sys-version",
        default=None,
        help="Optional Python runtime version string for Reasoning Engine.",
    )
    p.add_argument(
        "--engines-config",
        default="apps/agent-gateway/config/engines.json",
        help="Path to the agent-gateway engine registry JSON.",
    )
    p.add_argument(
        "--dry-run", action="store_true", help="No Vertex calls; still writes engines.json."
    )
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    deployed = deploy_brain(
        agent=args.agent,
        project=args.project,
        location=args.location,
        display_name=args.display_name,
        engines_config_path=Path(args.engines_config),
        dry_run=bool(args.dry_run),
        staging_bucket=args.staging_bucket,
        requirements=args.requirement or None,
        extra_packages=args.extra_package or None,
        sys_version=args.sys_version,
    )
    print(deployed.engine_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
