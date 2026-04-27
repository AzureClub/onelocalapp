from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from ..auth import get_user
from ..clients.content_safety import ContentSafetyImageClient, ContentSafetyTextClient
from ._helpers import http_error, persist, timed

router = APIRouter(prefix="/content-safety", tags=["content-safety"])


@router.post("/text")
async def analyze_text(body: dict, user: dict = Depends(get_user)):
    text = body.get("text", "")
    categories = body.get("categories")
    client = ContentSafetyTextClient()
    with timed() as t:
        try:
            result = await client.analyze_text(text, categories=categories)
        except Exception as exc:
            raise http_error(exc) from exc
    cats = result.get("categoriesAnalysis") or []
    max_severity = max((c.get("severity", 0) for c in cats), default=0)
    meta = persist(
        client=client, operation="text", user=user, duration_ms=t["ms"],
        summary={"length": len(text), "maxSeverity": max_severity},
        full_result=result,
    )
    return {"meta": meta, "result": result}


@router.post("/prompt-shield")
async def prompt_shield(body: dict, user: dict = Depends(get_user)):
    user_prompt = body.get("userPrompt", "")
    documents = body.get("documents") or []
    client = ContentSafetyTextClient()
    with timed() as t:
        try:
            result = await client.detect_jailbreak(user_prompt, documents=documents)
        except Exception as exc:
            raise http_error(exc) from exc
    meta = persist(
        client=client, operation="prompt-shield", user=user, duration_ms=t["ms"],
        summary={
            "promptAttackDetected": (result.get("userPromptAnalysis") or {}).get("attackDetected"),
            "documentCount": len(documents),
        },
        full_result=result,
    )
    return {"meta": meta, "result": result}


@router.post("/image")
async def analyze_image(image: UploadFile = File(...), user: dict = Depends(get_user)):
    data = await image.read()
    client = ContentSafetyImageClient()
    with timed() as t:
        try:
            result = await client.analyze_image(data)
        except Exception as exc:
            raise http_error(exc) from exc
    cats = result.get("categoriesAnalysis") or []
    max_severity = max((c.get("severity", 0) for c in cats), default=0)
    ext = (image.filename or "img.bin").split(".")[-1]
    meta = persist(
        client=client, operation="image", user=user, duration_ms=t["ms"],
        summary={"bytes": len(data), "maxSeverity": max_severity, "fileName": image.filename},
        full_result=result, input_bytes=data, input_ext=ext,
    )
    return {"meta": meta, "result": result}
