from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from scheduler.system_scheduler import active_interaction, memory_clear, daily_schedule_task, detail_schedule_task, \
    diary_task

import logging

from utils import agent_util

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler()

def remove_scheduler_job(task_id):
    if _scheduler.get_job(task_id):
        _scheduler.remove_job(task_id)

def add_scheduler_job(func, trigger, task_id):
    _scheduler.add_job(
        func=func,
        trigger=trigger,
        id=task_id,
        replace_existing=False
    )

def init_scheduler():
    # 每1-10分钟执行一次，主动与用户互动
    _scheduler.add_job(
        func=active_interaction,
        trigger=IntervalTrigger(minutes=1, jitter=540),
        id="active_interaction_task"
    )
    # 每天凌晨2点半执行一次，写日记
    _scheduler.add_job(
        func=diary_task,
        trigger=CronTrigger(hour=2, minute=30),
        id="diary_task"
    )
    # 每天凌晨3点12分执行一次，清除记忆
    _scheduler.add_job(
        func=memory_clear,
        trigger=CronTrigger(hour=3, minute=12),
        id="memory_clear_task"
    )
    # 四点半生成当天的日程
    _scheduler.add_job(
        func=daily_schedule_task,
        trigger=CronTrigger(hour=4, minute=30),
        id="daily_schedule_task"
    )
    # 从6点开始，每5分钟执行一次，直到24点结束，细化日程表
    _scheduler.add_job(
        func=detail_schedule_task,
        trigger=CronTrigger(hour='6-23', minute='*/5'),
        # trigger=CronTrigger(minute='*/5'),
        id="detail_schedule_task"
    )
    from orm.remind_orm import RemindORM
    remind_orm_obj = RemindORM()
    remind_task = remind_orm_obj.select_all()
    for task in remind_task:
        async def task_wrapper():
            try:
                logger.info(f"正在执行任务: {task.task_name} (ID: {task.task_id})")
                await agent_util.trigger_agent(
                    [("text", "你向系统预定的提醒任务触发,请你查阅提醒内容,执行对应任务,提醒内容提示：" + task.prompt)],
                    task.task_name)
                # 删除数据库中的任务
                remind_orm_obj.delete(task.task_id)
                # 阅后即焚
                remove_scheduler_job(task.task_id)
                logger.info(f"任务 {task.task_name} (ID: {task.task_id}) 已阅后即焚")
            except Exception as e:
                logger.error(f"任务 {task.task_name} 执行失败: {e}")
        add_scheduler_job(task_wrapper, trigger=DateTrigger(run_date=task.remind_time), task_id=task.task_id)
    _scheduler.start()
    logger.info("系统定时任务调度器已启动...")

def stop_scheduler():
    _scheduler.shutdown()
    logger.info("系统定时任务调度器已停止...")
