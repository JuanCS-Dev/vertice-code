from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, Optional


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
    "coder": {"module": "agents.coder.agent", "symbol": "CoderAgent"},
    "reviewer": {"module": "agents.reviewer.agent", "symbol": "ReviewerAgent"},
    "architect": {"module": "agents.architect.agent", "symbol": "ArchitectAgent"},
    "orchestrator": {"module": "agents.orchestrator.agent", "symbol": "OrchestratorAgent"},
    "researcher": {"module": "agents.researcher.agent", "symbol": "ResearcherAgent"},
    "devops": {"module": "agents.devops.agent", "symbol": "DevOpsAgent"},
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
) -> str:
    """
    Create a Vertex AI Reasoning Engine and return the engine resource id/name.

    This function intentionally does not handle auth; it will fail closed if the
    environment isn't configured for Vertex AI.
    """
    try:
        from vertexai.preview import reasoning_engines  # type: ignore
    except Exception as e:  # pragma: no cover
        raise DeployBrainError(
            "Vertex AI SDK not available. Install/enable `google-cloud-aiplatform` "
            "and ensure `vertexai.preview.reasoning_engines` is importable."
        ) from e

    # NOTE: Google manages scaling and tool execution. The agent_class must be
    # compatible with the Reasoning Engine runtime (Phase 2 requirement).
    try:
        engine = reasoning_engines.ReasoningEngine.create(
            agent_class(),
            display_name=display_name,
            project=project,
            location=location,
        )
    except Exception as e:  # pragma: no cover
        raise DeployBrainError(
            "Failed to create ReasoningEngine. Verify ADC credentials, project/location, "
            "and required Vertex APIs are enabled."
        ) from e

    engine_id = getattr(engine, "name", None) or getattr(engine, "resource_name", None)
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
) -> DeployedEngine:
    _ensure_src_on_path()

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
    p.add_argument("--location", default="global")
    p.add_argument("--display-name", default=None)
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
    )
    print(deployed.engine_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
