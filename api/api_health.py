from starlette.responses import JSONResponse

from entity.health import HealthModel
from orm.health_orm import StepORM, HeartRateORM, SleepSessionORM
from utils import health_util

step_orm_obj = StepORM()
heart_rate_orm_obj = HeartRateORM()
sleep_session_orm_obj = SleepSessionORM()

import logging
logger = logging.getLogger(__name__)

from fastapi import APIRouter
router = APIRouter(tags=["健康数据接口"])




@router.post("/api/health/load", summary="上传健康数据", description="上传健康数据")
async def health(data: HealthModel):
    # 打印到控制台查看
    logger.debug(f"health load: {data}")
    # 插入健康数据
    if data.heart_rate.sample_count != 0:
        heart_rate_orm_obj.insert(data)
    sleep_session_orm_obj.insert(data)
    step_orm_obj.insert(data)


    # 返回给推送方，方便确认是否推送成功
    return JSONResponse(content={"message": "数据接收成功"})

    # return JSONResponse({"status": "ok"})

@router.get("/api/health/last_day", summary="获取最近一天的健康数据", description="获取最近一天的健康数据")
async def last_day_health():
    return JSONResponse(content={"message": health_util.select_last_day_health_data()})
    # return JSONResponse({"status": "ok"})
