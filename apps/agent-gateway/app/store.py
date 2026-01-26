from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Protocol


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class Org:
    org_id: str
    name: str
    created_at: str
    owner_uid: str


@dataclass(frozen=True, slots=True)
class Membership:
    org_id: str
    uid: str
    role: str  # owner|admin|member
    created_at: str


@dataclass(frozen=True, slots=True)
class Run:
    run_id: str
    org_id: str
    uid: str
    session_id: str
    agent: str
    prompt: str
    status: str  # running|completed|error
    created_at: str
    updated_at: str
    final_text: str | None = None


class Store(Protocol):
    async def ensure_default_org(self, *, uid: str) -> Org:
        ...

    async def list_orgs(self, *, uid: str) -> list[Org]:
        ...

    async def create_org(self, *, uid: str, name: str) -> Org:
        ...

    async def set_default_org(self, *, uid: str, org_id: str) -> None:
        ...

    async def get_default_org_id(self, *, uid: str) -> str | None:
        ...

    async def get_membership(self, *, uid: str, org_id: str) -> Membership | None:
        ...

    async def create_run(
        self,
        *,
        uid: str,
        org_id: str,
        session_id: str,
        agent: str,
        prompt: str,
    ) -> Run:
        ...

    async def update_run(
        self,
        *,
        run_id: str,
        org_id: str,
        status: str,
        final_text: str | None = None,
    ) -> None:
        ...

    async def list_runs(self, *, uid: str, org_id: str, limit: int = 50) -> list[Run]:
        ...

    async def get_run(self, *, uid: str, org_id: str, run_id: str) -> Run | None:
        ...


class MemoryStore:
    def __init__(self) -> None:
        self._users: dict[str, dict[str, Any]] = {}
        self._orgs: dict[str, Org] = {}
        self._memberships: dict[tuple[str, str], Membership] = {}
        self._runs: dict[tuple[str, str], Run] = {}  # (org_id, run_id)

    async def ensure_default_org(self, *, uid: str) -> Org:
        default_org_id = self._users.get(uid, {}).get("default_org_id")
        if default_org_id and default_org_id in self._orgs:
            return self._orgs[default_org_id]
        org = await self.create_org(uid=uid, name=f"{uid[:8]} workspace")
        await self.set_default_org(uid=uid, org_id=org.org_id)
        return org

    async def list_orgs(self, *, uid: str) -> list[Org]:
        orgs = []
        for (org_id, member_uid), _m in self._memberships.items():
            if member_uid == uid and org_id in self._orgs:
                orgs.append(self._orgs[org_id])
        return sorted(orgs, key=lambda o: o.created_at, reverse=True)

    async def create_org(self, *, uid: str, name: str) -> Org:
        org_id = str(uuid.uuid4())
        org = Org(
            org_id=org_id, name=name.strip() or "Workspace", created_at=_utc_iso(), owner_uid=uid
        )
        self._orgs[org_id] = org
        self._memberships[(org_id, uid)] = Membership(
            org_id=org_id, uid=uid, role="owner", created_at=_utc_iso()
        )
        return org

    async def set_default_org(self, *, uid: str, org_id: str) -> None:
        self._users.setdefault(uid, {})["default_org_id"] = org_id

    async def get_default_org_id(self, *, uid: str) -> str | None:
        return self._users.get(uid, {}).get("default_org_id")

    async def get_membership(self, *, uid: str, org_id: str) -> Membership | None:
        return self._memberships.get((org_id, uid))

    async def create_run(
        self,
        *,
        uid: str,
        org_id: str,
        session_id: str,
        agent: str,
        prompt: str,
    ) -> Run:
        now = _utc_iso()
        run = Run(
            run_id=str(uuid.uuid4()),
            org_id=org_id,
            uid=uid,
            session_id=session_id,
            agent=agent,
            prompt=prompt,
            status="running",
            created_at=now,
            updated_at=now,
            final_text=None,
        )
        self._runs[(org_id, run.run_id)] = run
        return run

    async def update_run(
        self,
        *,
        run_id: str,
        org_id: str,
        status: str,
        final_text: str | None = None,
    ) -> None:
        key = (org_id, run_id)
        existing = self._runs.get(key)
        if existing is None:
            return
        self._runs[key] = replace(
            existing,
            status=status,
            updated_at=_utc_iso(),
            final_text=existing.final_text if final_text is None else final_text,
        )

    async def list_runs(self, *, uid: str, org_id: str, limit: int = 50) -> list[Run]:
        out = []
        for (o, _rid), run in self._runs.items():
            if o == org_id and run.uid == uid:
                out.append(run)
        out.sort(key=lambda r: r.created_at, reverse=True)
        return out[: max(1, min(limit, 200))]

    async def get_run(self, *, uid: str, org_id: str, run_id: str) -> Run | None:
        run = self._runs.get((org_id, run_id))
        if run is None or run.uid != uid:
            return None
        return run


class FirestoreStore:
    def __init__(self) -> None:
        from google.cloud.firestore_v1.async_client import AsyncClient  # type: ignore

        project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("VERTICE_GCP_PROJECT")
        database = os.getenv("VERTICE_FIRESTORE_DATABASE") or "(default)"
        self._client = AsyncClient(project=project, database=database)

    async def ensure_default_org(self, *, uid: str) -> Org:
        default_org_id = await self.get_default_org_id(uid=uid)
        if default_org_id:
            doc = await self._client.collection("orgs").document(default_org_id).get()
            if doc.exists:
                data = doc.to_dict() or {}
                return Org(
                    org_id=default_org_id,
                    name=str(data.get("name") or "Workspace"),
                    created_at=str(data.get("created_at") or _utc_iso()),
                    owner_uid=str(data.get("owner_uid") or uid),
                )
        org = await self.create_org(uid=uid, name=f"{uid[:8]} workspace")
        await self.set_default_org(uid=uid, org_id=org.org_id)
        return org

    async def list_orgs(self, *, uid: str) -> list[Org]:
        memberships = (
            self._client.collection("memberships")
            .where("uid", "==", uid)
            .order_by("created_at", direction="DESCENDING")
            .limit(100)
        )
        docs = [d async for d in memberships.stream()]
        org_ids = [str((d.to_dict() or {}).get("org_id") or "") for d in docs]
        out: list[Org] = []
        for org_id in org_ids:
            if not org_id:
                continue
            doc = await self._client.collection("orgs").document(org_id).get()
            if not doc.exists:
                continue
            data = doc.to_dict() or {}
            out.append(
                Org(
                    org_id=org_id,
                    name=str(data.get("name") or "Workspace"),
                    created_at=str(data.get("created_at") or _utc_iso()),
                    owner_uid=str(data.get("owner_uid") or ""),
                )
            )
        return out

    async def create_org(self, *, uid: str, name: str) -> Org:
        org_id = str(uuid.uuid4())
        org = Org(
            org_id=org_id, name=name.strip() or "Workspace", created_at=_utc_iso(), owner_uid=uid
        )
        await (
            self._client.collection("orgs")
            .document(org_id)
            .set({"name": org.name, "created_at": org.created_at, "owner_uid": org.owner_uid})
        )
        await (
            self._client.collection("memberships")
            .document(f"{org_id}:{uid}")
            .set({"org_id": org_id, "uid": uid, "role": "owner", "created_at": _utc_iso()})
        )
        return org

    async def set_default_org(self, *, uid: str, org_id: str) -> None:
        await (
            self._client.collection("users")
            .document(uid)
            .set({"default_org_id": org_id}, merge=True)
        )

    async def get_default_org_id(self, *, uid: str) -> str | None:
        doc = await self._client.collection("users").document(uid).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        v = data.get("default_org_id")
        return str(v) if isinstance(v, str) and v else None

    async def get_membership(self, *, uid: str, org_id: str) -> Membership | None:
        doc = await self._client.collection("memberships").document(f"{org_id}:{uid}").get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        return Membership(
            org_id=org_id,
            uid=uid,
            role=str(data.get("role") or "member"),
            created_at=str(data.get("created_at") or _utc_iso()),
        )

    async def create_run(
        self,
        *,
        uid: str,
        org_id: str,
        session_id: str,
        agent: str,
        prompt: str,
    ) -> Run:
        run_id = str(uuid.uuid4())
        now = _utc_iso()
        run = Run(
            run_id=run_id,
            org_id=org_id,
            uid=uid,
            session_id=session_id,
            agent=agent,
            prompt=prompt,
            status="running",
            created_at=now,
            updated_at=now,
        )
        await (
            self._client.collection("runs")
            .document(f"{org_id}:{run_id}")
            .set(
                {
                    "org_id": org_id,
                    "uid": uid,
                    "session_id": session_id,
                    "agent": agent,
                    "prompt": prompt,
                    "status": "running",
                    "created_at": now,
                    "updated_at": now,
                    "final_text": None,
                }
            )
        )
        return run

    async def update_run(
        self,
        *,
        run_id: str,
        org_id: str,
        status: str,
        final_text: str | None = None,
    ) -> None:
        updates: dict[str, Any] = {"status": status, "updated_at": _utc_iso()}
        if final_text is not None:
            updates["final_text"] = final_text
        await (
            self._client.collection("runs").document(f"{org_id}:{run_id}").set(updates, merge=True)
        )

    async def list_runs(self, *, uid: str, org_id: str, limit: int = 50) -> list[Run]:
        q = (
            self._client.collection("runs")
            .where("org_id", "==", org_id)
            .where("uid", "==", uid)
            .order_by("created_at", direction="DESCENDING")
            .limit(max(1, min(limit, 200)))
        )
        docs = [d async for d in q.stream()]
        out: list[Run] = []
        for doc in docs:
            data = doc.to_dict() or {}
            out.append(
                Run(
                    run_id=str(data.get("run_id") or doc.id.split(":")[-1]),
                    org_id=str(data.get("org_id") or org_id),
                    uid=str(data.get("uid") or uid),
                    session_id=str(data.get("session_id") or ""),
                    agent=str(data.get("agent") or "coder"),
                    prompt=str(data.get("prompt") or ""),
                    status=str(data.get("status") or "unknown"),
                    created_at=str(data.get("created_at") or _utc_iso()),
                    updated_at=str(data.get("updated_at") or _utc_iso()),
                    final_text=(
                        str(data.get("final_text")) if data.get("final_text") is not None else None
                    ),
                )
            )
        return out

    async def get_run(self, *, uid: str, org_id: str, run_id: str) -> Run | None:
        doc = await self._client.collection("runs").document(f"{org_id}:{run_id}").get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        if str(data.get("uid") or "") != uid or str(data.get("org_id") or "") != org_id:
            return None
        return Run(
            run_id=run_id,
            org_id=org_id,
            uid=uid,
            session_id=str(data.get("session_id") or ""),
            agent=str(data.get("agent") or "coder"),
            prompt=str(data.get("prompt") or ""),
            status=str(data.get("status") or "unknown"),
            created_at=str(data.get("created_at") or _utc_iso()),
            updated_at=str(data.get("updated_at") or _utc_iso()),
            final_text=(
                str(data.get("final_text")) if data.get("final_text") is not None else None
            ),
        )


def build_store() -> Store:
    """
    Default:
    - Cloud Run/GCP env: Firestore (production).
    - Local/tests: MemoryStore (fast, no credentials needed).
    """

    default = (
        "firestore" if (os.getenv("K_SERVICE") or os.getenv("GOOGLE_CLOUD_PROJECT")) else "memory"
    )
    enabled = os.getenv("VERTICE_STORE", default).strip().lower()
    if enabled in {"memory", "mem", "inmemory"}:
        return MemoryStore()
    # Firestore é a opção padrão "production-ready" (Google-native) quando credenciais/ADC existem.
    return FirestoreStore()
