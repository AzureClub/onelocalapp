from __future__ import annotations

import logging
import os

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from .config import settings

logger = logging.getLogger(__name__)


def setup_telemetry(app) -> None:
    cs = settings.applicationinsights_connection_string
    if not cs:
        logger.info("App Insights connection string not set, skipping telemetry")
        return
    os.environ.setdefault("APPLICATIONINSIGHTS_CONNECTION_STRING", cs)
    configure_azure_monitor(connection_string=cs)
    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    logger.info("App Insights telemetry configured")
