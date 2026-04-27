from __future__ import annotations

from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


Mode = Literal["connected", "disconnected"]


class Settings(BaseSettings):
    """App configuration loaded from ENV vars.

    Per-service mode/endpoint/key follow the pattern:
        AI_<SERVICE>_MODE, AI_<SERVICE>_ENDPOINT, AI_<SERVICE>_KEY, AI_<SERVICE>_REGION
    where <SERVICE> is one of: SPEECH_STT, SPEECH_TTS, TRANSLATOR, LANGUAGE,
    DOCINTEL_READ, DOCINTEL_LAYOUT, CONTENT_SAFETY_TEXT, CONTENT_SAFETY_IMAGE.
    Falls back to global MODE / endpoints if per-service overrides are empty.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    mode: Mode = "connected"
    use_managed_identity: bool = True

    # Azure infra (connected)
    azure_client_id: Optional[str] = None
    azure_tenant_id: Optional[str] = None
    storage_account_name: Optional[str] = None
    cosmos_account_name: Optional[str] = None
    cosmos_database_name: str = "onelocalapp"
    cosmos_container_name: str = "runs"
    key_vault_name: Optional[str] = None
    applicationinsights_connection_string: Optional[str] = None

    # Disconnected fallbacks (when not using MI)
    storage_connection_string: Optional[str] = None
    cosmos_connection_string: Optional[str] = None

    # Auth (Entra)
    entra_audience: Optional[str] = None
    entra_issuer: Optional[str] = None
    require_auth: bool = False  # behind EasyAuth so backend can trust headers

    # AI service endpoints / keys (per service)
    ai_speech_stt_mode: Optional[Mode] = None
    ai_speech_stt_endpoint: Optional[str] = None
    ai_speech_stt_key: Optional[str] = None

    ai_speech_tts_mode: Optional[Mode] = None
    ai_speech_tts_endpoint: Optional[str] = None
    ai_speech_tts_key: Optional[str] = None

    ai_translator_mode: Optional[Mode] = None
    ai_translator_endpoint: Optional[str] = None
    ai_translator_key: Optional[str] = None
    ai_translator_region: Optional[str] = None

    ai_language_mode: Optional[Mode] = None
    ai_language_endpoint: Optional[str] = None
    ai_language_key: Optional[str] = None

    ai_docintel_read_mode: Optional[Mode] = None
    ai_docintel_read_endpoint: Optional[str] = None
    ai_docintel_read_key: Optional[str] = None

    ai_docintel_layout_mode: Optional[Mode] = None
    ai_docintel_layout_endpoint: Optional[str] = None
    ai_docintel_layout_key: Optional[str] = None

    ai_content_safety_text_mode: Optional[Mode] = None
    ai_content_safety_text_endpoint: Optional[str] = None
    ai_content_safety_text_key: Optional[str] = None

    ai_content_safety_image_mode: Optional[Mode] = None
    ai_content_safety_image_endpoint: Optional[str] = None
    ai_content_safety_image_key: Optional[str] = None

    # ---- helpers ----------------------------------------------------------

    def service_config(self, service: str) -> dict:
        """Return resolved config for a logical service.

        service: one of speech_stt, speech_tts, translator, language,
                 docintel_read, docintel_layout, content_safety_text,
                 content_safety_image.
        """
        prefix = f"ai_{service}"
        mode = getattr(self, f"{prefix}_mode", None) or self.mode
        endpoint = getattr(self, f"{prefix}_endpoint", None)
        key = getattr(self, f"{prefix}_key", None)
        region = getattr(self, f"{prefix}_region", None)
        return {
            "service": service,
            "mode": mode,
            "endpoint": endpoint,
            "key": key,
            "region": region,
        }


settings = Settings()
