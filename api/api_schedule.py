import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from utils import scheduler_util

router = APIRouter(tags=["任务接口"])

class ArtificialTask(BaseModel):
    task_name: str
    prompt: str
    trigger_time: datetime.datetime

@router.post("/api/schedule/add", summary="添加人工任务", description="添加人工任务")
def schedule_add(task: ArtificialTask):
    res = scheduler_util.add_artificial_task(task.trigger_time, task.task_name, task.prompt)
    return res
