from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import content_safety, docintel, health, history, language, speech, translator
from .telemetry import setup_telemetry

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="OneLocalApp API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_telemetry(app)

API_PREFIX = "/api"
app.include_router(health.router)
app.include_router(speech.router, prefix=API_PREFIX)
app.include_router(translator.router, prefix=API_PREFIX)
app.include_router(language.router, prefix=API_PREFIX)
app.include_router(docintel.router, prefix=API_PREFIX)
app.include_router(content_safety.router, prefix=API_PREFIX)
app.include_router(history.router, prefix=API_PREFIX)


@app.get("/")
async def root():
    return {"name": "OneLocalApp API", "mode": settings.mode}
