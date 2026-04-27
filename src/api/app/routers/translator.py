from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import get_user
from ..clients.translator import TranslatorClient
from ._helpers import http_error, persist, timed

router = APIRouter(prefix="/translator", tags=["translator"])


@router.post("/translate")
async def translate(body: dict, user: dict = Depends(get_user)):
    texts = body.get("texts") or [body.get("text", "")]
    to = body.get("to") or ["en"]
    src = body.get("from")
    client = TranslatorClient()
    with timed() as t:
        try:
            result = await client.translate(texts, to_languages=to, from_language=src)
        except Exception as exc:
            raise http_error(exc) from exc
    summary = {
        "from": src or (result[0].get("detectedLanguage", {}).get("language") if result else None),
        "to": to,
        "items": len(texts),
    }
    meta = persist(client=client, operation="translate", user=user, duration_ms=t["ms"],
                   summary=summary, full_result=result)
    return {"meta": meta, "result": result}
