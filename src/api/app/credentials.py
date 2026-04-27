from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

from .config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_credential():
    if settings.use_managed_identity and settings.azure_client_id:
        logger.info("Using ManagedIdentityCredential client_id=%s", settings.azure_client_id)
        return ManagedIdentityCredential(client_id=settings.azure_client_id)
    logger.info("Using DefaultAzureCredential")
    return DefaultAzureCredential(exclude_interactive_browser_credential=False)
