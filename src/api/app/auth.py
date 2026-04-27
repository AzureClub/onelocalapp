from __future__ import annotations

import base64
import json
import logging
from typing import Optional

from fastapi import Header, HTTPException, status

logger = logging.getLogger(__name__)


def _parse_easyauth_principal(header_value: str) -> dict:
    try:
        decoded = base64.b64decode(header_value).decode("utf-8")
        return json.loads(decoded)
    except Exception:
        return {}


def get_user(
    x_ms_client_principal: Optional[str] = Header(default=None),
    x_ms_client_principal_id: Optional[str] = Header(default=None),
    x_ms_client_principal_name: Optional[str] = Header(default=None),
) -> dict:
    """Extract user identity from Container Apps EasyAuth headers.

    In dev (no auth), returns an anonymous principal to keep things working.
    Hard auth enforcement happens at ingress / EasyAuth layer.
    """
    if x_ms_client_principal:
        principal = _parse_easyauth_principal(x_ms_client_principal)
        claims = {c.get("typ"): c.get("val") for c in principal.get("claims", [])}
        oid = claims.get("http://schemas.microsoft.com/identity/claims/objectidentifier") or x_ms_client_principal_id
        return {
            "oid": oid,
            "name": x_ms_client_principal_name or claims.get("name"),
            "email": claims.get("preferred_username") or claims.get("email"),
            "claims": claims,
        }
    if x_ms_client_principal_id:
        return {"oid": x_ms_client_principal_id, "name": x_ms_client_principal_name}
    return {"oid": "anonymous", "name": "anonymous"}
