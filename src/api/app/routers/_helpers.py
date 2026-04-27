from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Optional

from fastapi import HTTPException

from ..clients.base import AIServiceClient
from ..config import settings
from ..storage import blob, cosmos


@contextmanager
def timed():
    start = time.perf_counter()
    holder = {"ms": 0}
    try:
        yield holder
    finally:
        holder["ms"] = int((time.perf_counter() - start) * 1000)


def persist(
    *,
    client: AIServiceClient,
    operation: str,
    user: dict,
    duration_ms: int,
    summary: dict[str, Any],
    full_result: dict | bytes,
    input_bytes: Optional[bytes] = None,
    input_ext: str = "bin",
    error: Optional[str] = None,
) -> dict:
    run_id = blob.make_run_id()
    service_key = client.service
    blob_input_uri = None
    blob_result_uri = None
    try:
        if input_bytes is not None:
            blob_input_uri = blob.upload_input(service_key, run_id, input_bytes, ext=input_ext)
        if isinstance(full_result, (dict, list)):
            blob_result_uri = blob.upload_result(service_key, run_id, {"result": full_result})
        elif isinstance(full_result, (bytes, bytearray)):
            # binary result (e.g. tts audio) — store under inputs container as well
            blob_result_uri = blob.upload_input(f"{service_key}-out", run_id, bytes(full_result), ext="bin")
    except Exception as exc:  # storage failure shouldn't break user response
        error = (error or "") + f" | storage: {exc}"

    cosmos.save_run(
        run_id=run_id,
        service=service_key,
        operation=operation,
        mode=client.mode,
        user_id=user.get("oid"),
        duration_ms=duration_ms,
        status="error" if error else "ok",
        summary=summary,
        blob_input_uri=blob_input_uri,
        blob_result_uri=blob_result_uri,
        error=error,
    )
    return {
        "runId": run_id,
        "service": service_key,
        "operation": operation,
        "mode": client.mode,
        "durationMs": duration_ms,
        "blobResultUri": blob_result_uri,
        "blobInputUri": blob_input_uri,
        "summary": summary,
    }


def http_error(exc: Exception) -> HTTPException:
    return HTTPException(status_code=502, detail=f"Upstream AI error: {exc}")
