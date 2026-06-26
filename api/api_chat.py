import asyncio
import os

from fastapi import APIRouter, Body, UploadFile, File
from starlette.responses import StreamingResponse

from api import api_file
from entity.Chat import ChatMessageItem, ChatListResponse
from orm.dialog_history_orm import DialogueHistoryOrm
from orm.short_term_memory_orm import ShortTermMemoryORM
from utils import agent_util, setting, sse_util

import logging

from utils.voice_generation import voice_generation

logger = logging.getLogger(__name__)

# router = APIRouter()
router = APIRouter(tags=["聊天接口"])

short_term_memory_orm_obj = ShortTermMemoryORM()
dialogue_history_orm_obj = DialogueHistoryOrm()


@router.get("/api/chat/list/{min_id}", summary="获取聊天记录", description="每次返回100条，min_id 为上一次查询的最小 id，第一次调用时 min_id 为 -1")
async def chat_list(min_id: int) -> ChatListResponse:
    conversation = dialogue_history_orm_obj.list(min_id)
    conversation = [ChatMessageItem(id=item.id, role=item.role, type=item.type, content=item.content, time_stamp=item.create_time, duration_seconds=item.duration_seconds) for item in conversation]
    return ChatListResponse(data=conversation)


# return ChatListResponse(data=conversation)
# =============================
# 消息缓冲区
message_buffer: list[tuple[str, str]] = []
delay_task: asyncio.Task | None = None
# 用于向 SSE 长连接推送数据的管道
sse_push_queue: asyncio.Queue = asyncio.Queue()



async def delayed_call():
    """
    防抖、延迟组合消息
    """
    try:
        await asyncio.sleep(10)
        messages = message_buffer.copy()
        # logger.debug(f"delayed_call messages: {messages}")
        message_buffer.clear()
        if messages:
            await agent_util.trigger_agent(messages)
    finally:
        global delay_task
        delay_task = None


@router.post("/api/chat/send", summary="发送消息", description="向 AI 发送消息并获取响应")
async def chat_send(message: str = Body(..., embed=True, description="用户消息", examples=["你好，今天天气怎么样？"])):
    global delay_task

    message_buffer.append(("text", message))
    if delay_task is not None:
        delay_task.cancel()

    delay_task = asyncio.create_task(delayed_call())
    dialogue_history_orm_obj.insert(message, "user", "text")

    return {"status": "received"}

@router.post("/api/chat/image", summary="上传对话图片", description="上传对话图片, 格式只能是 png, jpg, jpeg")
async def upload_file(files: list[UploadFile] = File(..., max_length=9, description="最多上传9张图片")):
    if not agent_util.agents["chat"].could_input_image():
        raise ValueError("agent 不支持上传图片")
    file_parent_path = os.path.join(setting.UPLOAD_PATH, "chat_image")
    os.makedirs(file_parent_path, exist_ok=True)
    urls = []

    for file in files:
        new_filename = await api_file.save_file_to_disk(file, file_parent_path, allowed_extensions=api_file.ALLOWED_EXTENSIONS)
        url = f'/static/uploads/chat_image/{new_filename}'
        file_path = os.path.join(file_parent_path, new_filename)

        message_buffer.append(("image", file_path))
        dialogue_history_orm_obj.insert(url, "user", "image")
        urls.append(url)

    global delay_task

    if delay_task is not None:
        delay_task.cancel()

    delay_task = asyncio.create_task(delayed_call())


    return {"status": "received", "urls": urls}


# ================= 2. SSE 推送接口（长连接） =================
@router.get("/api/chat/stream", summary="SSE消息流", description="建立长连接，接收 AI 的异步响应")
async def chat_stream():
    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue(maxsize=64)
        try:
            sse_util.active_connections.add(queue)
            while True:
                # 阻塞等待，直到 Agent 把结果塞入队列
                response = await queue.get()
                logger.debug(response)
                # data = json.loads(response)
                # 封装成 SSE 标准格式推送
                yield f"data: {response}\n\n"
        except asyncio.CancelledError:
            pass
        except ConnectionResetError:
            pass
        finally:
            sse_util.active_connections.discard(queue)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

