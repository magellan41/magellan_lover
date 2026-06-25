import datetime
import uuid

import dateutil
from apscheduler.triggers.date import DateTrigger

import logging

from utils import scheduler_util, agent_util

logger = logging.getLogger(__name__)


from orm.remind_orm import RemindORM
remind_orm_obj = RemindORM()


def _calculate_remind_time(remind_time:dict, remind_time_type:str="increment"):
    seconds = remind_time.get("seconds", 0)
    minutes = remind_time.get("minutes", 0)
    hours = remind_time.get("hours", 0)
    days = remind_time.get("days", 0)
    weeks = remind_time.get("weeks", 0)
    months = remind_time.get("months", 0)
    years = remind_time.get("years", 0)

    current_time = datetime.datetime.now()
    if remind_time_type == "increment":

        delta = dateutil.relativedelta.relativedelta(
            years=years, months=months, weeks=weeks, days=days,
            hours=hours, minutes=minutes, seconds=seconds
        )
        true_remind_time = current_time + delta
    else:
        new_year = years if "years" in remind_time else current_time.year
        new_month = months if "months" in remind_time else current_time.month
        new_day = days if "days" in remind_time else current_time.day
        try:
            true_remind_time = current_time.replace(
                year=new_year,
                month=new_month,
                day=new_day,
                hour=hours,
                minute=minutes,
                second=seconds,
                microsecond=0
            )
        except ValueError as e:
            raise ValueError(f"绝对时间不合法：{e}")

    return true_remind_time

def _add_remind(task_id: str, trigger, task_name: str, prompt: str):
    async def task_wrapper():
        try:
            logger.info(f"正在执行任务: {task_name} (ID: {task_id})")
            await agent_util.trigger_agent([("text", "你向系统预定的提醒任务触发,请你查阅提醒内容,执行对应任务,提醒内容提示：" + prompt)], task_name)
            # 删除数据库中的任务
            remind_orm_obj.delete(task_id)
            # 阅后即焚
            scheduler_util.remove_scheduler_job(task_id)
            logger.info(f"任务 {task_name} (ID: {task_id}) 已阅后即焚")
        except Exception as e:
            logger.error(f"任务 {task_name} 执行失败: {e}")

    scheduler_util.add_scheduler_job(task_wrapper, trigger, task_id)
    return {
        "message": "Task created successfully",
        "task_id": task_id
    }

def add_remind(remind_name: str, remind_prompt: str, remind_time: dict, remind_time_type:str="increment"):
    if remind_time_type not in ["increment", "absolute"]:
        raise ValueError("参数 remind_time_type 必须为 'increment' 或 'absolute'")
    try:
        true_remind_time = _calculate_remind_time(remind_time, remind_time_type)
    except ValueError as e:
        raise ValueError(f"提醒 [{remind_name}] 设定的时间不合法：{e}") from e

    current_time = datetime.datetime.now()
    if true_remind_time <= current_time:
        raise ValueError(
            f"提醒 [{remind_name}] 设定的绝对时间 {true_remind_time} 已经过去！当前时间 {current_time} 无法生成提醒")
    task_id = uuid.uuid4().hex
    _add_remind(task_id, DateTrigger(run_date=true_remind_time), remind_name, remind_prompt)
    # 插入数据库
    remind_orm_obj.insert(task_id=task_id, task_name=remind_name, prompt=remind_prompt, trigger_time=true_remind_time)
    return {
        "message": "提醒任务已添加",
        "task_id": task_id,
        "task_name": remind_name,
        "trigger_time": true_remind_time
    }


