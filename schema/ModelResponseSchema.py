from pydantic import BaseModel, Field, ConfigDict


class ChatModelResponseSchema(BaseModel):
    model_config = ConfigDict(strict=False)
    flag: bool = Field(default=True,description="布尔标识")
    voice: bool = Field(default=False,description="语音标识")
    content: str = Field(default="",description="输出的内容")