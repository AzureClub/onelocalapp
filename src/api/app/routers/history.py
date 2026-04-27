from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..auth import get_user
from ..storage import cosmos

router = APIRouter(prefix="/history", tags=["history"])


@router.get("")
async def list_history(
    service: str | None = Query(default=None),
    mode: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, le=500),
    user: dict = Depends(get_user),
):
    items = cosmos.list_runs(service=service, mode=mode, status=status, limit=limit)
    return {"items": items, "count": len(items)}


@router.get("/{service}/{run_id}")
async def get_history_item(service: str, run_id: str, user: dict = Depends(get_user)):
    return cosmos.get_run(run_id, service) or {}
