from fastapi import APIRouter, Body
import logging

from pydantic import BaseModel, Field

from utils import push_util

logger = logging.getLogger(__name__)

router = APIRouter(tags=["设备接口"])

from orm.device_push_id_orm import DevicePushInfoOrm
device_push_info_orm_obj = DevicePushInfoOrm()

class PushIdRequest(BaseModel):
    pushId: str = Field(..., description="设备ID")

@router.post("/api/device/pushid", summary="推送设备ID", description="推送设备ID到服务器")
async def push_id(pushIdRequest: PushIdRequest):
    logger.info(f"收到设备ID: {pushIdRequest.pushId}")
    device_push_info_orm_obj.insert_device_push_id(pushIdRequest.pushId)
    return {"message": "设备ID已成功接收"}

class PushTestInfo(BaseModel):
    title: str = Field(..., description="消息标题")
    content: str = Field(..., description="消息内容")

@router.post("/api/device/push", summary="推送消息", description="推送消息到设备")
async def push(pushIdRequest: PushTestInfo):
    logger.info(f"收到推送消息: {pushIdRequest}")
    push_util.send_push_meizu(pushIdRequest.title, pushIdRequest.content)
    return {"message": "消息已成功发送"}
