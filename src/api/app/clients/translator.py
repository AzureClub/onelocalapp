from __future__ import annotations

from typing import Iterable

from .base import AIServiceClient


class TranslatorClient(AIServiceClient):
    def __init__(self):
        super().__init__("translator")

    async def translate(self, texts: Iterable[str], to_languages: list[str], from_language: str | None = None) -> dict:
        params = {"api-version": "3.0", "to": to_languages}
        if from_language:
            params["from"] = from_language
        body = [{"Text": t} for t in texts]
        return await self.post_json("translate", body, params=params)
