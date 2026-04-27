from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from azure.storage.blob import BlobServiceClient

from ..config import settings
from ..credentials import get_credential

logger = logging.getLogger(__name__)

_RESULTS_CONTAINER = "results"
_INPUTS_CONTAINER = "inputs"


def _blob_service() -> BlobServiceClient:
    if settings.use_managed_identity and settings.storage_account_name:
        url = f"https://{settings.storage_account_name}.blob.core.windows.net"
        return BlobServiceClient(account_url=url, credential=get_credential())
    if settings.storage_connection_string:
        return BlobServiceClient.from_connection_string(settings.storage_connection_string)
    raise RuntimeError("No storage configuration available (set STORAGE_ACCOUNT_NAME or STORAGE_CONNECTION_STRING)")


def _path(service: str, run_id: str, suffix: str) -> str:
    now = datetime.now(timezone.utc)
    return f"{service}/{now:%Y/%m/%d}/{run_id}.{suffix}"


def make_run_id() -> str:
    return uuid4().hex


def upload_result(service: str, run_id: str, payload: dict) -> str:
    client = _blob_service().get_blob_client(_RESULTS_CONTAINER, _path(service, run_id, "json"))
    client.upload_blob(json.dumps(payload, ensure_ascii=False, default=str), overwrite=True)
    return client.url


def upload_input(service: str, run_id: str, data: bytes, ext: str = "bin") -> str:
    client = _blob_service().get_blob_client(_INPUTS_CONTAINER, _path(service, run_id, ext))
    client.upload_blob(data, overwrite=True)
    return client.url


def download_result(service: str, run_id: str, blob_path: Optional[str] = None) -> dict:
    path = blob_path or _path(service, run_id, "json")
    client = _blob_service().get_blob_client(_RESULTS_CONTAINER, path)
    data = client.download_blob().readall()
    return json.loads(data)
