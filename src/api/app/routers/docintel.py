from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from ..auth import get_user
from ..clients.docintel import DocIntelClient
from ._helpers import http_error, persist, timed

router = APIRouter(prefix="/docintel", tags=["docintel"])


@router.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    model: str = Form("prebuilt-read"),
    user: dict = Depends(get_user),
):
    data = await file.read()
    variant = "layout" if "layout" in model else "read"
    client = DocIntelClient(variant=variant)  # type: ignore[arg-type]
    with timed() as t:
        try:
            result = await client.analyze(
                data, content_type=file.content_type or "application/octet-stream", model=model,  # type: ignore[arg-type]
            )
        except Exception as exc:
            raise http_error(exc) from exc

    pages = (result.get("analyzeResult") or {}).get("pages") or []
    summary = {
        "model": model,
        "pages": len(pages),
        "fileName": file.filename,
        "contentType": file.content_type,
    }
    meta = persist(
        client=client, operation=f"analyze:{model}", user=user, duration_ms=t["ms"],
        summary=summary, full_result=result, input_bytes=data, input_ext=(file.filename or "bin").split(".")[-1],
    )
    return {"meta": meta, "result": result}
