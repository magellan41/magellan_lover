import datetime
from typing import List

from pydantic import BaseModel, Field


class ChatMessageItem(BaseModel):
    id: int = Field(..., description="消息ID")
    role: str = Field(..., description="角色：user/assistant")
    type: str = Field(..., description="消息类型：text/image/voice")
    content: str = Field(..., description="消息内容")
    time_stamp: datetime.datetime = Field(..., description="消息发送时间")

class ChatListResponse(BaseModel):
    data: List[ChatMessageItem] = Field(..., description="聊天历史列表")

class ChatResponse(BaseModel):
    content: str  = Field(..., description="AI 返回的响应内容")
    voice: bool = Field(..., description="是否需要转语音")
