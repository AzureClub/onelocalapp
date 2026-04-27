from __future__ import annotations

from fastapi import APIRouter

from ..clients.content_safety import ContentSafetyImageClient, ContentSafetyTextClient
from ..clients.docintel import DocIntelClient
from ..clients.language import LanguageClient
from ..clients.speech import SpeechSTTClient, SpeechTTSClient
from ..clients.translator import TranslatorClient
from ..config import settings

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz():
    return {"ok": True, "mode": settings.mode}


@router.get("/readyz")
async def readyz():
    return {"ok": True}


@router.get("/services/health")
async def services_health():
    clients = [
        SpeechSTTClient(), SpeechTTSClient(), TranslatorClient(),
        LanguageClient(), DocIntelClient("read"), DocIntelClient("layout"),
        ContentSafetyTextClient(), ContentSafetyImageClient(),
    ]
    items = []
    for c in clients:
        items.append(await c.health())
    return {"globalMode": settings.mode, "services": items}
