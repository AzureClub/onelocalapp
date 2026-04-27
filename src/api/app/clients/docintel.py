from __future__ import annotations

import asyncio
from typing import Literal

import httpx

from .base import AIServiceClient


_ModelKind = Literal["read", "layout", "prebuilt-invoice", "prebuilt-receipt", "prebuilt-idDocument"]


class DocIntelClient(AIServiceClient):
    """Wraps Document Intelligence (Form Recognizer) container/PaaS endpoint.

    Two underlying clients exist: docintel_read and docintel_layout. We pick
    based on requested model.
    """

    def __init__(self, variant: Literal["read", "layout"] = "read"):
        super().__init__(f"docintel_{variant}")
        self.variant = variant

    async def analyze(self, data: bytes, content_type: str, model: _ModelKind | None = None) -> dict:
        model = model or ("prebuilt-read" if self.variant == "read" else "prebuilt-layout")
        path = f"documentintelligence/documentModels/{model}:analyze"
        params = {"api-version": "2024-11-30"}
        # POST returns 202 with operation-location
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(
                self._url(path), content=data, params=params,
                headers=self._headers(content_type=content_type),
            )
            resp.raise_for_status()
            op_url = resp.headers.get("operation-location")
            if not op_url:
                return resp.json() if resp.content else {}
            # Poll
            for _ in range(60):
                await asyncio.sleep(2)
                poll = await client.get(op_url, headers=self._headers(content_type=None))
                poll.raise_for_status()
                body = poll.json()
                if body.get("status") in ("succeeded", "failed"):
                    return body
            raise TimeoutError("Document Intelligence analyze timed out")
