from __future__ import annotations

from .base import AIServiceClient


class SpeechSTTClient(AIServiceClient):
    def __init__(self):
        super().__init__("speech_stt")

    async def transcribe(self, audio: bytes, content_type: str = "audio/wav", language: str = "en-US") -> dict:
        # Speech container conversation REST endpoint
        params = {"language": language, "format": "detailed"}
        resp = await self.post_bytes(
            "speech/recognition/conversation/cognitiveservices/v1",
            audio,
            content_type=content_type,
            params=params,
        )
        return resp.json()


class SpeechTTSClient(AIServiceClient):
    def __init__(self):
        super().__init__("speech_tts")

    async def synthesize(self, ssml: str, voice_format: str = "audio-24khz-48kbitrate-mono-mp3") -> bytes:
        resp = await self.post_bytes(
            "cognitiveservices/v1",
            ssml.encode("utf-8"),
            content_type="application/ssml+xml",
            extra_headers={"X-Microsoft-OutputFormat": voice_format},
        )
        return resp.content
