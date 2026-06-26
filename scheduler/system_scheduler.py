import asyncio
import datetime
import json
import math
import os
import random


from utils import env_util, setting, holiday_util, common_util, agent_util


import logging


logger = logging.getLogger(__name__)

from orm.schedule_orm import DetailScheduleORM
from orm.diary_orm import DiaryORM
detail_schedule_orm_obj = DetailScheduleORM()
diary_orm_obj = DiaryORM()


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
    last_schedule = detail_schedule_orm_obj.select_last()

    # 如果当前在睡觉，不主动发起对话
    if last_schedule is not None and last_schedule.activity == "睡觉":
        return
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
        await agent_util.trigger_agent([("text", f"距离上次与用户对话 {hours} 小时 {minutes} 分钟 {seconds} 秒，你可以尝试发起与用户的对话。")], "system")


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
            res = await asyncio.to_thread(agent_util.agents["memory"].chat, mid_term_memory_str)
            logger.info(f"记忆清理agent原始返回: {res}")
            res = common_util.safe_json_loads(res).get("delete_memory_id_list", [])
            mid_term_memory_orm_obj.delete_all(res)
            mid_term_memory_orm_obj.alive()

            memory_to_long = mid_term_memory_orm_obj.alive_to_long_term()
            if memory_to_long is not None:
                long_term_memory_orm_obj = LongTermMemoryOrm()
                for memory in memory_to_long:
                    long_term_memory_orm_obj.insert(memory.content)

        except Exception as e:
            logger.error(f"记忆清理失败: {e}")

# ==================================日程制定任务=====================================
from orm.schedule_orm import DailyScheduleORM

daily_schedule_orm_obj = DailyScheduleORM()


async def daily_schedule_task():
    logger.info("开始制定今日日程")
    # 文件不存在
    if not os.path.exists(os.path.join(setting.CONFIG_PATH, "rough_schedule.json")):
        logger.warning("日程制定规则文件不存在")
        return

    with open(os.path.join(setting.CONFIG_PATH, "rough_schedule.json"), "r", encoding="utf-8") as f:
        rough_schedule = f.read()
    # 无日程安排规则
    if rough_schedule.strip() == "":
        logger.warning("日程制定规则为空")
        return

    workday_flag, day_type, day_name, day_str = holiday_util.today_status()
    daily_schedule_obj = daily_schedule_orm_obj.select_by_date(day_str)
    if daily_schedule_obj is not None:
        logger.warning("今日已存在程制定,无需重复制定")
        return

    daily_schedule_prompt = f"""【日程制定规则】
{rough_schedule}

【当前日期描述】
{day_str}
{day_type}
{day_name}
请你根据以上信息，制定今日日程。

【返回格式】
[{{
    "start_time": "开始时间HH:MM",
    "end_time": "结束时间HH:MM",
    "activity": "活动名称",
}}]
时间为前闭后开区间
【返回示例】
[{{
    "start_time": "07:00",
    "end_time": "08:00",
    "activity": "起床",
}},
{{
    "start_time": "08:00",
    "end_time": "09:00",
    "activity": "洗漱早餐赶公交",
}}, 
{{
    "start_time": "23:00",
    "end_time": "24:00",
    "activity": "睡觉",
}}]
事件名称在10个字符以内，不能包含特殊字符。
请确保返回的日程安排没有重叠，无冲突，第一件事为起床，最后一件事必须为睡觉且最后一件事的结束时间为24:00。
请你直接返回json对象列表，,不要包含任何解释、问候或前缀（如“好的”、“以下是回复”等）。
"""
    logger.info("开始制定今日日程")
    res = await asyncio.to_thread(agent_util.agents["story"].chat, daily_schedule_prompt)
    # res = json.dumps(common_util.safe_json_loads(res), ensure_ascii=False)
    # logger.info(f"制定今日日程: {res}")
    daily_schedule_orm_obj.insert(day_str, res)


async def detail_schedule_task():
    workday_flag, day_type, day_name, day_str = holiday_util.today_status()
    daily_schedule = daily_schedule_orm_obj.select_by_date(day_str)
    # 无日程安排
    if daily_schedule is None:
        return
    last_schedule = detail_schedule_orm_obj.select_last()
    # 上一个活动未结束
    if last_schedule is not None and last_schedule.end_time > datetime.datetime.now():
        return

    today_schedule = detail_schedule_orm_obj.select_today()
    today_schedule_summary = "\n".join([f"{item.start_time.strftime('%H:%M')} - {item.end_time.strftime('%H:%M')} {item.activity} {item.detail}" for item in today_schedule])

    detail_schedule_prompt = f"""【今日日程安排】
{daily_schedule.daily_schedule}

【当前时间信息】
{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{day_type}
{day_name}
【今日已完成日程(格式为(开始时间 - 结束时间 活动名称 活动详情))】
{today_schedule_summary}

【返回格式】
{{
    "start_time": "开始时间(%Y-%m-%d %H:%M:%S)",
    "end_time": "结束时间(%Y-%m-%d %H:%M:%S)",
    "activity": "活动名称",
    "detail": "关于活动的详细描述，请以二人称形式描述，详细描述发生了'你'做了什么。",
}}
如果时间为24:00，请以次日00:00表示。
仅需返回一个json对象，表示当前时间点需要进行的活动及其信息。请你严格遵守以上格式返回，不要包含任何解释、问候或前缀（如“好的”、“以下是回复”等）。
"""
    res = await asyncio.to_thread(agent_util.agents["story"].chat, detail_schedule_prompt)
    detail_schedule_json = common_util.safe_json_loads(res)
    start_time = detail_schedule_json["start_time"]
    start_datetime = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end_time = detail_schedule_json["end_time"]
    end_datetime = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

    logger.info(f"插入日程细节: {start_time} - {end_time} {detail_schedule_json['activity']} {detail_schedule_json['detail']}")
    detail_schedule_orm_obj.insert(start_datetime, end_datetime, detail_schedule_json["activity"], detail_schedule_json["detail"])




async def diary_task():
    yesterday_schedule = detail_schedule_orm_obj.select_last_day()
    if yesterday_schedule:
        yesterday_schedule_str = "\n".join([f"{item.start_time.strftime('%H:%M')} - {item.end_time.strftime('%H:%M')} {item.activity} {item.detail}" for item in yesterday_schedule])
        prompt = f"【你昨天一天的完整经历】\n{yesterday_schedule_str}，请你根据你的经历以及对话记录，写一篇日记，或者可以所心所欲写一篇文章，本次返回不需要添加任何语气词以及前缀头，你可以随心所欲，写任何你所想的内容"
        res = await asyncio.to_thread(agent_util.agents["story"].diary, prompt)
        logger.info(f"写日记: {res}")
        diary_orm_obj.insert(res)
