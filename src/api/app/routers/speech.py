from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response

from ..auth import get_user
from ..clients.speech import SpeechSTTClient, SpeechTTSClient
from ._helpers import http_error, persist, timed

router = APIRouter(prefix="/speech", tags=["speech"])


@router.post("/stt")
async def speech_to_text(
    audio: UploadFile = File(...),
    language: str = Form("en-US"),
    user: dict = Depends(get_user),
):
    data = await audio.read()
    client = SpeechSTTClient()
    with timed() as t:
        try:
            result = await client.transcribe(data, content_type=audio.content_type or "audio/wav", language=language)
        except Exception as exc:
            raise http_error(exc) from exc

    summary = {
        "language": language,
        "displayText": result.get("DisplayText") or (result.get("NBest") or [{}])[0].get("Display"),
    }
    meta = persist(
        client=client, operation="stt", user=user, duration_ms=t["ms"],
        summary=summary, full_result=result, input_bytes=data, input_ext="wav",
    )
    return {"meta": meta, "result": result}


@router.post("/tts")
async def text_to_speech(
    body: dict,
    user: dict = Depends(get_user),
):
    text = body.get("text", "")
    voice = body.get("voice", "en-US-JennyNeural")
    ssml = (
        f"<speak version='1.0' xml:lang='en-US'>"
        f"<voice name='{voice}'>{text}</voice></speak>"
    )
    client = SpeechTTSClient()
    with timed() as t:
        try:
            audio = await client.synthesize(ssml)
        except Exception as exc:
            raise http_error(exc) from exc
    meta = persist(
        client=client, operation="tts", user=user, duration_ms=t["ms"],
        summary={"text": text[:200], "voice": voice, "bytes": len(audio)},
        full_result=audio, input_bytes=ssml.encode("utf-8"), input_ext="ssml",
    )
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={"X-Run-Id": meta["runId"], "X-Result-Uri": meta.get("blobResultUri") or ""},
    )
