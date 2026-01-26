from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException

try:
    from .store import Membership, Org, Store  # type: ignore
except Exception:  # pragma: no cover
    from store import Membership, Org, Store  # type: ignore


@dataclass(frozen=True, slots=True)
class TenantContext:
    org: Org
    membership: Membership


async def resolve_tenant(
    store: Store,
    *,
    uid: str,
    org_id: str | None,
) -> TenantContext:
    """
    Resolve tenant/org for the authenticated user.

    Rules:
    - If `X-Vertice-Org` is provided, it must belong to the user.
    - Otherwise, we use (and create if missing) the user's default org.
    """

    if org_id:
        org_id = org_id.strip()
        if not org_id:
            raise HTTPException(status_code=400, detail="invalid org header")
        membership = await store.get_membership(uid=uid, org_id=org_id)
        if membership is None:
            raise HTTPException(status_code=403, detail="not a member of org")
        # Resolve org metadata by listing (cheap path) to avoid additional API in store protocol.
        orgs = await store.list_orgs(uid=uid)
        org = next((o for o in orgs if o.org_id == org_id), None)
        if org is None:
            # Membership exists but org doc missing => inconsistent data
            raise HTTPException(status_code=404, detail="org not found")
        return TenantContext(org=org, membership=membership)

    org = await store.ensure_default_org(uid=uid)
    membership = await store.get_membership(uid=uid, org_id=org.org_id)
    if membership is None:
        raise HTTPException(status_code=403, detail="not a member of default org")
    return TenantContext(org=org, membership=membership)
