from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import get_user
from ..clients.language import LanguageClient
from ._helpers import http_error, persist, timed

router = APIRouter(prefix="/language", tags=["language"])


async def _run(operation: str, user: dict, fn, summary_fn, payload: dict):
    client = LanguageClient()
    with timed() as t:
        try:
            result = await fn(client)
        except Exception as exc:
            raise http_error(exc) from exc
    meta = persist(
        client=client, operation=operation, user=user, duration_ms=t["ms"],
        summary=summary_fn(result, payload), full_result=result,
    )
    return {"meta": meta, "result": result}


@router.post("/detect")
async def detect(body: dict, user: dict = Depends(get_user)):
    texts = body.get("texts") or [body.get("text", "")]
    return await _run("detect", user, lambda c: c.detect_language(texts),
                      lambda r, p: {"items": len(texts)}, body)


@router.post("/pii")
async def pii(body: dict, user: dict = Depends(get_user)):
    texts = body.get("texts") or [body.get("text", "")]
    language = body.get("language", "en")
    return await _run("pii", user, lambda c: c.pii(texts, language),
                      lambda r, p: {"items": len(texts), "language": language}, body)


@router.post("/ner")
async def ner(body: dict, user: dict = Depends(get_user)):
    texts = body.get("texts") or [body.get("text", "")]
    language = body.get("language", "en")
    return await _run("ner", user, lambda c: c.ner(texts, language),
                      lambda r, p: {"items": len(texts), "language": language}, body)


@router.post("/health")
async def health_text(body: dict, user: dict = Depends(get_user)):
    texts = body.get("texts") or [body.get("text", "")]
    language = body.get("language", "en")
    return await _run("health", user, lambda c: c.health(texts, language),
                      lambda r, p: {"items": len(texts), "language": language}, body)
