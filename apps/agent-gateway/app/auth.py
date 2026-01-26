from __future__ import annotations

import os
from dataclasses import dataclass

from fastapi import Header, HTTPException, Request


@dataclass(frozen=True, slots=True)
class AuthContext:
    uid: str


def _truthy_env(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _auth_required() -> bool:
    default = "1" if os.getenv("K_SERVICE") else "0"
    return _truthy_env("VERTICE_AUTH_REQUIRED", default)


def _dev_uid() -> str:
    return os.getenv("VERTICE_DEV_UID", "dev-user")


async def get_auth_context(
    request: Request,
    *,
    x_vertice_user: str | None = Header(default=None, alias="X-Vertice-User"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> AuthContext:
    """
    Auth model:
    - Preferred (prod behind a trusted proxy): `X-Vertice-User: <uid>`
    - Fallback (direct calls/dev): `Authorization: Bearer <Firebase ID token>`
    - Test/dev bypass: `VERTICE_AUTH_REQUIRED=0`
    """

    if x_vertice_user:
        uid = x_vertice_user.strip()
        if not uid:
            raise HTTPException(status_code=401, detail="invalid user header")
        return AuthContext(uid=uid)

    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        if not token:
            raise HTTPException(status_code=401, detail="missing bearer token")

        try:
            import firebase_admin  # type: ignore
            from firebase_admin import auth as fb_auth  # type: ignore
        except Exception as exc:
            raise HTTPException(status_code=500, detail="firebase-admin not available") from exc

        if not firebase_admin._apps:  # noqa: SLF001
            # ADC on Cloud Run will be used automatically (no JSON key in repo).
            firebase_admin.initialize_app()

        try:
            decoded = fb_auth.verify_id_token(token, check_revoked=True)
        except Exception as exc:
            raise HTTPException(status_code=401, detail="invalid token") from exc

        uid = str(decoded.get("uid") or "")
        if not uid:
            raise HTTPException(status_code=401, detail="invalid token payload")
        return AuthContext(uid=uid)

    if not _auth_required():
        return AuthContext(uid=_dev_uid())

    path = getattr(request.url, "path", "")
    raise HTTPException(status_code=401, detail=f"authentication required for {path}")
