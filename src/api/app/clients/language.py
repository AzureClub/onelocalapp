from __future__ import annotations

from .base import AIServiceClient


class LanguageClient(AIServiceClient):
    """Azure AI Language container/PaaS — only non-deprecated features."""

    def __init__(self):
        super().__init__("language")

    async def _analyze(self, kind: str, documents: list[dict], parameters: dict | None = None) -> dict:
        body = {"kind": kind, "analysisInput": {"documents": documents}}
        if parameters:
            body["parameters"] = parameters
        return await self.post_json("language/:analyze-text", body, params={"api-version": "2023-04-01"})

    async def detect_language(self, texts: list[str]) -> dict:
        docs = [{"id": str(i), "text": t} for i, t in enumerate(texts)]
        return await self._analyze("LanguageDetection", docs)

    async def pii(self, texts: list[str], language: str = "en") -> dict:
        docs = [{"id": str(i), "language": language, "text": t} for i, t in enumerate(texts)]
        return await self._analyze("PiiEntityRecognition", docs)

    async def ner(self, texts: list[str], language: str = "en") -> dict:
        docs = [{"id": str(i), "language": language, "text": t} for i, t in enumerate(texts)]
        return await self._analyze("EntityRecognition", docs)

    async def health(self, texts: list[str], language: str = "en") -> dict:
        # Health uses async jobs endpoint; container also supports synchronous in newer versions.
        docs = [{"id": str(i), "language": language, "text": t} for i, t in enumerate(texts)]
        return await self._analyze("Healthcare", docs)
