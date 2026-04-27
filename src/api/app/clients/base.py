from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


class AIServiceClient:
    """Generic HTTP client for an Azure AI container or PaaS endpoint.

    Same code path for connected and disconnected — only ENV (endpoint/key) differs.
    For PaaS endpoints in connected mode you can still use API-Key, or swap to
    AAD token via DefaultAzureCredential where supported.
    """

    def __init__(self, service: str, default_route_prefix: str = ""):
        cfg = settings.service_config(service)
        self.service = service
        self.mode: str = cfg["mode"]
        self.endpoint: Optional[str] = (cfg["endpoint"] or "").rstrip("/")
        self.key: Optional[str] = cfg["key"]
        self.region: Optional[str] = cfg["region"]
        self.route_prefix = default_route_prefix.strip("/")

    @property
    def configured(self) -> bool:
        return bool(self.endpoint)

    def _url(self, path: str) -> str:
        path = path.lstrip("/")
        if self.route_prefix:
            return f"{self.endpoint}/{self.route_prefix}/{path}"
        return f"{self.endpoint}/{path}"

    def _headers(self, extra: Optional[dict] = None, content_type: Optional[str] = "application/json") -> dict:
        h: dict[str, str] = {}
        if content_type:
            h["Content-Type"] = content_type
        if self.key:
            h["Ocp-Apim-Subscription-Key"] = self.key
        if self.region:
            h["Ocp-Apim-Subscription-Region"] = self.region
        if extra:
            h.update(extra)
        return h

    async def post_json(self, path: str, json_body: Any, params: Optional[dict] = None, extra_headers: Optional[dict] = None) -> dict:
        if not self.configured:
            raise RuntimeError(f"Service {self.service} is not configured (missing endpoint)")
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(self._url(path), json=json_body, params=params, headers=self._headers(extra_headers))
            resp.raise_for_status()
            return resp.json() if resp.content else {}

    async def post_bytes(self, path: str, data: bytes, content_type: str, params: Optional[dict] = None, extra_headers: Optional[dict] = None) -> httpx.Response:
        if not self.configured:
            raise RuntimeError(f"Service {self.service} is not configured (missing endpoint)")
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(
                self._url(path),
                content=data,
                params=params,
                headers=self._headers(extra_headers, content_type=content_type),
            )
            resp.raise_for_status()
            return resp

    async def get(self, path: str, params: Optional[dict] = None) -> httpx.Response:
        if not self.configured:
            raise RuntimeError(f"Service {self.service} is not configured (missing endpoint)")
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(self._url(path), params=params, headers=self._headers(content_type=None))
            resp.raise_for_status()
            return resp

    async def health(self) -> dict:
        if not self.configured:
            return {"service": self.service, "mode": self.mode, "configured": False, "ok": False}
        # Both connected (Azure container) and PaaS expose /status or root liveness
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(self.endpoint, headers=self._headers(content_type=None))
            ok = r.status_code < 500
        except Exception as exc:  # pragma: no cover
            return {"service": self.service, "mode": self.mode, "configured": True, "ok": False, "error": str(exc)}
        return {"service": self.service, "mode": self.mode, "configured": True, "ok": ok, "endpoint": self.endpoint}
