import datetime

from fastapi import APIRouter, Body

from entity.Diary import DiaryDto
from orm.remind_orm import RemindORM
from orm.diary_orm import DiaryORM

from utils import scheduler_util

remind_orm_obj = RemindORM()
diary_orm_obj = DiaryORM()

import logging

from entity.Remind import RemindListResponse, RemindItem

logger = logging.getLogger(__name__)

router = APIRouter(tags=["智能体工作接口"])

@router.get("/api/agent/remind/list", summary="获取智能体提醒列表", description="获取所有智能体的提醒列表")
async def list_remind() -> RemindListResponse:
    remind_list = remind_orm_obj.select_all()
    return RemindListResponse(data=[RemindItem(**remind.__dict__) for remind in remind_list])

@router.delete("/api/agent/remind/delete", summary="删除智能体提醒", description="删除提醒")
async def delete_remind(remind_ids: list = Body(..., description="提醒ID")) -> dict:
    remind_list = remind_orm_obj.select_by_ids(remind_ids)
    for remind in remind_list:
        scheduler_util.remove_scheduler_job(remind.task_id)
    remind_orm_obj.delete_by_ids(remind_ids)
    return {"message": "删除成功"}

@router.get("/api/agent/diary/list/{mini_id}", summary="获取智能体日记列表", description="获取所有智能体的日记列表")
async def list_diary(mini_id: int)  -> dict:
    diary_list = diary_orm_obj.list_diary_titles(mini_id)
    return {"data": diary_list}

@router.get("/api/agent/diary/get/{diary_id}", summary="获取智能体日记", description="获取智能体的日记")
async def get_diary(diary_id: int) -> DiaryDto:
    diary = diary_orm_obj.select_diary_by_id(diary_id)
    return DiaryDto(title=diary.title, content=diary.content)


