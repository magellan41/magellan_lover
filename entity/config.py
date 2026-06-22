from pydantic import BaseModel


class VoiceConfig(BaseModel):
    voice_enable: str
    voice_key_type: str
    voice_api_key: str
    voice_generation_type: str
