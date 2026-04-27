from __future__ import annotations

import base64

from .base import AIServiceClient


class ContentSafetyTextClient(AIServiceClient):
    def __init__(self):
        super().__init__("content_safety_text")

    async def analyze_text(self, text: str, categories: list[str] | None = None) -> dict:
        body: dict = {"text": text}
        if categories:
            body["categories"] = categories
        return await self.post_json("contentsafety/text:analyze", body, params={"api-version": "2024-09-01"})

    async def detect_jailbreak(self, user_prompt: str, documents: list[str] | None = None) -> dict:
        body = {"userPrompt": user_prompt, "documents": documents or []}
        return await self.post_json(
            "contentsafety/text:shieldPrompt", body, params={"api-version": "2024-09-01"}
        )


class ContentSafetyImageClient(AIServiceClient):
    def __init__(self):
        super().__init__("content_safety_image")

    async def analyze_image(self, image_bytes: bytes) -> dict:
        body = {"image": {"content": base64.b64encode(image_bytes).decode("ascii")}}
        return await self.post_json("contentsafety/image:analyze", body, params={"api-version": "2024-09-01"})
