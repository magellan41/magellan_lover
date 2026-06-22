import asyncio
import datetime
import json
import math
import random

from apscheduler.triggers.cron import CronTrigger

from utils import env_util

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

import logging

from utils.agent_util import agents

logger = logging.getLogger(__name__)


scheduler = AsyncIOScheduler()

QUIET_START_HOUR = 23  # 23点
QUIET_END_HOUR = 8     # 次日8点
def is_quiet_time(current_hour):
    """判断当前是否处于免打扰时间段"""
    if QUIET_START_HOUR > QUIET_END_HOUR:
        return current_hour >= QUIET_START_HOUR or current_hour < QUIET_END_HOUR
    else:
        return QUIET_START_HOUR <= current_hour < QUIET_END_HOUR

def activate_function(x):
    """
    激活函数，将分钟数映射到0-0.3之间，作为主动发起对话的概率
    """
    k = 0.03  # 控制曲线陡峭程度
    x0 = 200  # 中心点，y=0.5 的位置
    return (1 / (1 + math.exp(-k * (x - x0)))) * 0.3


# ==================================主动发起对话任务=====================================
async def active_interaction():
    last_interaction_time_str = env_util.read_env_var("last_interaction_time")
    if last_interaction_time_str is None:
        return

    current_time = datetime.datetime.now()
    if is_quiet_time(current_time.hour):
        return

    last_interaction_time = datetime.datetime.fromisoformat(last_interaction_time_str)
    interval = current_time - last_interaction_time
    interval_seconds = int(interval.total_seconds())
    interval_minutes = interval_seconds / 60.0
    activate_prob = activate_function(interval_minutes)
    logger.debug("Activate interval {} with prob {}".format(interval_minutes, activate_prob))
    if activate_prob > random.random():
        logger.info("主动发起对话")
        hours, remainder = divmod(interval_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        logger.debug(f"距离上次对话 {hours} 小时 {minutes} 分钟 {seconds} 秒")
        # 主动发起对话
        from api.api_chat import trigger_agent
        await trigger_agent([f"距离上次与用户对话 {hours} 小时 {minutes} 分钟 {seconds} 秒，你可以尝试发起与用户的对话。"], "system")


# ==================================记忆清理任务=====================================
async def memory_clear():
    from orm.mid_term_memroy_orm import MidTermMemoryOrm
    from orm.long_term_memory_orm import LongTermMemoryOrm

    mid_term_memory_orm_obj = MidTermMemoryOrm()
    mid_term_memory_list = mid_term_memory_orm_obj.select_all()

    if mid_term_memory_list is not None and len(mid_term_memory_list) > 50:
        mid_memory_dicts = [
            {
                "id": memory.id,
                "content": memory.content,
                "create_time": memory.create_time.strftime("%Y-%m-%d %H:%M:%S"),
                "alive": memory.alive_turn
            }
            for memory in mid_term_memory_list
        ]
        mid_term_memory_str = "【历史记忆】[" + ",".join([json.dumps(d, ensure_ascii=False) for d in mid_memory_dicts]) + "]"
        try:
            res = await asyncio.to_thread(agents["memory"].chat, mid_term_memory_str)
            logger.info(f"记忆清理agent原始返回: {res}")
            res = json.loads(res).get("delete_memory_id_list", [])
            mid_term_memory_orm_obj.delete_all(res)
            mid_term_memory_orm_obj.alive()

            memory_to_long = mid_term_memory_orm_obj.alive_to_long_term()
            if memory_to_long is not None:
                long_term_memory_orm_obj = LongTermMemoryOrm()
                for memory in memory_to_long:
                    long_term_memory_orm_obj.insert(memory.content)

        except Exception as e:
            logger.error(f"记忆清理失败: {e}")


def init_scheduler():
    scheduler.add_job(
        func=active_interaction,
        trigger=IntervalTrigger(minutes=1, jitter=540),
        id="active_interaction_task"
    )
    scheduler.add_job(
        func=memory_clear,
        trigger=CronTrigger(hour=3, minute=12),
        id="memory_clear_task"
    )
    scheduler.start()
    logger.info("系统定时任务调度器已启动...")
