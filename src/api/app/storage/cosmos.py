from __future__ import annotations

import logging
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Optional

from azure.cosmos import CosmosClient, PartitionKey, exceptions

from ..config import settings
from ..credentials import get_credential

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _client() -> CosmosClient:
    if settings.use_managed_identity and settings.cosmos_account_name:
        url = f"https://{settings.cosmos_account_name}.documents.azure.com:443/"
        return CosmosClient(url, credential=get_credential())
    if settings.cosmos_connection_string:
        return CosmosClient.from_connection_string(settings.cosmos_connection_string)
    raise RuntimeError("No Cosmos configuration available")


def _container():
    return _client().get_database_client(settings.cosmos_database_name).get_container_client(settings.cosmos_container_name)


def save_run(
    *,
    run_id: str,
    service: str,
    operation: str,
    mode: str,
    user_id: Optional[str],
    duration_ms: int,
    status: str,
    summary: dict[str, Any],
    blob_input_uri: Optional[str] = None,
    blob_result_uri: Optional[str] = None,
    error: Optional[str] = None,
) -> dict:
    item = {
        "id": run_id,
        "service": service,
        "operation": operation,
        "mode": mode,
        "userId": user_id or "anonymous",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "durationMs": duration_ms,
        "status": status,
        "summary": summary,
        "blobInputUri": blob_input_uri,
        "blobResultUri": blob_result_uri,
        "error": error,
    }
    _container().upsert_item(item)
    return item


def list_runs(
    *,
    service: Optional[str] = None,
    mode: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    q = "SELECT * FROM c WHERE 1=1"
    params: list[dict] = []
    if service:
        q += " AND c.service = @service"
        params.append({"name": "@service", "value": service})
    if mode:
        q += " AND c.mode = @mode"
        params.append({"name": "@mode", "value": mode})
    if status:
        q += " AND c.status = @status"
        params.append({"name": "@status", "value": status})
    q += " ORDER BY c.createdAt DESC OFFSET 0 LIMIT @limit"
    params.append({"name": "@limit", "value": limit})
    items = list(_container().query_items(query=q, parameters=params, enable_cross_partition_query=True))
    return items


def get_run(run_id: str, service: str) -> Optional[dict]:
    try:
        return _container().read_item(item=run_id, partition_key=service)
    except exceptions.CosmosResourceNotFoundError:
        return None
